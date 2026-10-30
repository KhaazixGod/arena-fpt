"""E1 (a): forward kinematics of the arena USD vs cl0.kinematics.SO101Kinematics, 20 random joint configurations.

Two checks per configuration (simulation only):
  * kinematic: joint positions teleported, link pose read back with NO physics step -> tests the USD asset (axes, zeros, order, offsets);
  * dynamic:   from the home pose, drive targets = home +- 12 deg, 1.5 s of physics under gravity (240 Hz) -> PD tracking error (informative).
Threshold [de xuat]: <= 2 mm and <= 1 deg on the kinematic check.  ~/env_isaac/bin/python arena/scripts/e1_fk_check.py --out arena/runs/e1
"""
import argparse, json, os, sys
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=20); ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--settle-s", type=float, default=1.5)
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
os.makedirs(args.out, exist_ok=True)

from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 640, "height": 480})
import omni.usd, omni.timeline
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_simulation_interface
from arena import scene as S
from cl0.kinematics import SO101Kinematics

ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg)
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(10): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root)
mt = art.shared_metatype
dof_names, link_names = list(mt.dof_names), list(mt.link_names)
assert dof_names == list(S.ALL_JOINTS), dof_names
tcp_i = link_names.index("gripper_frame_link")
lim = art.get_dof_limits().reshape(-1, 2)                              # (6,2) radians, order = dof_names

kin = SO101Kinematics()                                                # official chain, tcp offset 0 = gripper_frame_link
rng = np.random.default_rng(args.seed)
lo_deg = np.degrees(lim[:5, 0]) + 8.0; hi_deg = np.degrees(lim[:5, 1]) - 8.0   # stay 8 deg inside the URDF limits


def quat_to_R(q):                       # (x, y, z, w)
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def rot_err_deg(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def tcp_pose():
    tf = art.get_link_transforms()[0, tcp_i]
    return tf[:3] * 1000.0, quat_to_R(tf[3:7])


zero = np.zeros((1, 6), np.float32)
idx0 = np.array([0], np.int32)
sim_i = get_physx_simulation_interface(); DT = 1.0 / cfg["physics"]["hz"]


def teleport(q5, gripper_deg=0.0):
    q = np.radians(np.r_[q5, gripper_deg]).astype(np.float32)[None, :]
    art.set_dof_positions(q, idx0); art.set_dof_velocities(zero, idx0); art.set_dof_position_targets(q, idx0)
    sim.update_articulations_kinematic()


# ---- phase 1: kinematic, NO physics step at all (a failure here is the asset: axes, zeros, order, offsets)
rows = []
for k in range(args.n):
    q5 = rng.uniform(lo_deg, hi_deg)
    teleport(q5)
    p_k, R_k = tcp_pose()
    p_ref, R_ref = kin.fk(q5)
    rows.append({"i": k, "q_deg": [round(float(x), 3) for x in q5], "tcp_ref_mm": [round(float(x), 2) for x in p_ref],
                 "kin_pos_err_mm": round(float(np.linalg.norm(p_k - p_ref)), 4), "kin_rot_err_deg": round(rot_err_deg(R_k, R_ref), 4)})
    print(f"[kin {k:2d}] {rows[-1]['kin_pos_err_mm']:8.4f} mm {rows[-1]['kin_rot_err_deg']:7.4f} deg", flush=True)

# ---- phase 2: dynamic, starting from the config home pose (cl0.toml robot.home_q_deg), targets = home +- 12 deg, 1.5 s under gravity
import tomllib
home = np.array(tomllib.load(open(os.path.join(os.path.dirname(HERE), "cl0", "cl0.toml"), "rb"))["robot"]["home_q_deg"], float)
dyn_rows = []
for k in range(8):
    tgt = np.clip(home + rng.uniform(-12.0, 12.0, 5) * (k > 0), lo_deg, hi_deg)       # k = 0: hold the home pose (pure gravity sag)
    teleport(home)
    q = np.radians(np.r_[tgt, 0.0]).astype(np.float32)[None, :]
    art.set_dof_position_targets(q, idx0)
    t, vmax, nan = 0.0, 0.0, False
    for _ in range(int(args.settle_s / DT)):
        sim_i.simulate(DT, t); sim_i.fetch_results(); t += DT
        v = art.get_dof_velocities()[0]
        if not np.all(np.isfinite(v)):
            nan = True; break
        vmax = max(vmax, float(np.max(np.abs(np.degrees(v[:5])))))
    if nan:
        dyn_rows.append({"i": k, "target_deg": [round(float(x), 2) for x in tgt], "nan": True}); print(f"[dyn {k}] NaN", flush=True)
        break
    p_d, R_d = tcp_pose(); p_ref, R_ref = kin.fk(tgt)
    qm = np.degrees(art.get_dof_positions()[0, :5])
    dyn_rows.append({"i": k, "target_deg": [round(float(x), 2) for x in tgt], "nan": False,
                     "pos_err_mm": round(float(np.linalg.norm(p_d - p_ref)), 2), "rot_err_deg": round(rot_err_deg(R_d, R_ref), 2),
                     "joint_err_deg_max": round(float(np.max(np.abs(qm - tgt))), 2), "joint_err_deg": [round(float(x), 2) for x in (qm - tgt)],
                     "qdot_peak_deg_s": round(vmax, 1), "tcp_z_mm": round(float(p_d[2]), 1)})
    print(f"[dyn {k}] tcp err {dyn_rows[-1]['pos_err_mm']:6.2f} mm  joint max {dyn_rows[-1]['joint_err_deg_max']:5.2f} deg  peak qdot {vmax:6.1f} deg/s", flush=True)

kp = np.array([r["kin_pos_err_mm"] for r in rows]); kr = np.array([r["kin_rot_err_deg"] for r in rows])
ok_dyn = [r for r in dyn_rows if not r.get("nan")]
dp = np.array([r["pos_err_mm"] for r in ok_dyn] or [np.nan]); dj = np.array([r["joint_err_deg_max"] for r in ok_dyn] or [np.nan])
summary = {"engine": "isaac", "n": len(rows), "seed": args.seed, "joint_margin_from_limit_deg": 8.0,
           "kinematic": {"pos_mm_max": float(kp.max()), "pos_mm_mean": float(kp.mean()), "rot_deg_max": float(kr.max())},
           "dynamic": {"n": len(dyn_rows), "n_nan": sum(1 for r in dyn_rows if r.get("nan")), "pos_mm_max": float(np.nanmax(dp)), "pos_mm_mean": float(np.nanmean(dp)), "joint_deg_max": float(np.nanmax(dj))},
           "threshold_proposed": {"pos_mm": 2.0, "rot_deg": 1.0}, "pass_kinematic": bool(kp.max() <= 2.0 and kr.max() <= 1.0),
           "dof_names": dof_names, "link_names": link_names}
json.dump({"summary": summary, "rows": rows, "dynamic_rows": dyn_rows}, open(os.path.join(args.out, "e1_fk.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
app.close()
