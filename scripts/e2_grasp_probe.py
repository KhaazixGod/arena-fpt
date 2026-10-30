"""E2: physical grasp probe, NO rendering and NO CL-0 perception.  For each interim object and each TCP height above the belt: park, home, place the object under a known pose,
IK (cl0 SO101Kinematics, arena.toml tcp_offset) to above it, descend, close, lift, hold.  Reports whether the object follows the gripper up (bottom >= 25 mm for >= 1 s) and the
fastest object speed (ejection check).  Overrides: --set robot.gripper_max_force_nm=2.5 --set objects.max_depenetration_m_s=0 (scene.toml keys).  Simulation only.
    ~/env_isaac/bin/python arena/scripts/e2_grasp_probe.py --out arena/runs/e2/grasp_probe --heights 8,12,16,20,24
"""
import argparse, json, os, sys
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--heights", default="8,12,16,20,24"); ap.add_argument("--objects", default="")
ap.add_argument("--set", action="append", default=[]); ap.add_argument("--repeat", type=int, default=1)
ap.add_argument("--swing", action="store_true", help="after the lift, move to CL-0's hold_q_deg in 1.0 s (min-jerk) and hold 1.5 s: the motion where objects slipped in E2/E4")
ap.add_argument("--x", type=float, default=190.0); ap.add_argument("--a", type=float, default=0.0)
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
OUT = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out); os.makedirs(OUT, exist_ok=True)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 640, "height": 360})
from arena import scene as S
from arena.objects import INTERIM_SPECS
from arena.world import IsaacWorld
from cl0.config import load_config
from cl0.kinematics import SO101Kinematics

sc = S.load_scene_cfg()
for kv in args.set:
    k, v = kv.split("=", 1); sec, key = k.split(".")
    sc.setdefault(sec, {})
    sc[sec][key] = v if isinstance(sc[sec].get(key), str) else (int(float(v)) if key.endswith("iters") else float(v))
cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
kin = SO101Kinematics(tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
specs = [s for s in INTERIM_SPECS if not args.objects or s.name in args.objects.split(",")]
w = IsaacWorld(app, INTERIM_SPECS, sc)
home = np.array(cfg.robot.home_q_deg, float); g_open, belt_top = cfg.robot.gripper_open, w.belt_top_mm
X, A = args.x, args.a                               # object centre (default x = 190 mm, i.e. b = -190, a = 0)


def move(q_from, q_to, T, g=None, hold_g=None):
    n = int(T * 50)
    for i in range(1, n + 1):
        s = i / n; s = 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5
        w.set_targets(q_from + (q_to - q_from) * s, g if g is not None else None)
        for _ in range(6): w.step()


rows = []
for sp in specs:
    for h in [float(x) for x in args.heights.split(",")]:
        for rep in range(args.repeat):
            w.set_belt_speed(0.0); w.park_all(); w.teleport_arm(home, g_open); w.step_seconds(0.3)
            w.place([{"name": sp.name, "a_mm": A, "b_mm": -X, "yaw_deg": 0.0}]); w.step_seconds(0.5)
            top = belt_top + h
            ik_pre = kin.ik([X, A, belt_top + 70.0], 0.0, q0_deg=home, tilt_deg=90.0); ik_g = kin.ik([X, A, top], 0.0, q0_deg=ik_pre.q_deg, tilt_deg=90.0)
            ik_up = kin.ik([X, A, belt_top + 60.0], 0.0, q0_deg=ik_g.q_deg, tilt_deg=90.0)
            if not (ik_pre.ok and ik_g.ok and ik_up.ok):
                rows.append({"object": sp.name, "h_mm": h, "rep": rep, "ik_ok": False}); print(sp.name, h, "IK FAIL", flush=True); continue
            q0 = w.joint_deg()[:5]
            move(q0, ik_pre.q_deg, 1.2, g_open); move(ik_pre.q_deg, ik_g.q_deg, 0.8, g_open); w.step_seconds(0.3)
            g_at_open = w.grip_deg_to_pos(w.joint_deg()[5])
            w.set_targets(None, 0.0); w.step_seconds(0.8)
            g_closed = w.grip_deg_to_pos(w.joint_deg()[5])
            o_before = w.gt_objects()[sp.name]
            lifts, speeds, prev = [], [], None
            n = 50
            for i in range(1, n + 1):
                s = i / n; s = 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5
                w.set_targets(ik_g.q_deg + (ik_up.q_deg - ik_g.q_deg) * s, None)
                for _ in range(6):
                    w.step()
                o = w.gt_objects()[sp.name]["pos_mm"]; lifts.append(o[2] - sp.height_mm / 2 - belt_top)
                if prev is not None: speeds.append(np.linalg.norm(o - prev) / (6 * w.dt) / 1000.0)
                prev = o
            if args.swing:                                                    # CL-0's MOVE_HOLD: joint-space min-jerk to hold_q in 1.0 s
                hold = np.array(cfg.robot.hold_q_deg, float)
                q_up = w.joint_deg()[:5]
                for i in range(1, 51):
                    s_ = i / 50; s_ = 10 * s_ ** 3 - 15 * s_ ** 4 + 6 * s_ ** 5
                    w.set_targets(q_up + (hold - q_up) * s_, None)
                    for _ in range(6): w.step()
                    o = w.gt_objects()[sp.name]["pos_mm"]; lifts.append(o[2] - sp.height_mm / 2 - belt_top)
            for i in range(75):                                               # hold 1.5 s
                for _ in range(6): w.step()
                o = w.gt_objects()[sp.name]["pos_mm"]; lifts.append(o[2] - sp.height_mm / 2 - belt_top)
            if not w.finite(): raise SystemExit("NaN")
            lifts = np.array(lifts); held = bool(np.all(lifts[-50:] >= 25.0))
            rows.append({"object": sp.name, "h_mm": h, "rep": rep, "ik_ok": True, "held_lifted": held, "final_lift_mm": round(float(lifts[-1]), 1), "max_lift_mm": round(float(lifts.max()), 1),
                         "grip_open": round(g_at_open, 1), "grip_after_close": round(g_closed, 1), "grip_end": round(w.grip_deg_to_pos(w.joint_deg()[5]), 1),
                         "obj_shift_on_close_mm": round(float(np.hypot(o_before["a_mm"] - A, o_before["b_mm"] + X)), 1), "max_obj_speed_m_s": round(float(max(speeds)), 2)})
            print(json.dumps(rows[-1]), flush=True)
json.dump({"engine": "isaac", "overrides": args.set, "rows": rows}, open(os.path.join(OUT, "grasp_probe.json"), "w"), indent=1)
print("\nheld (lift >= 25 mm for the last 1 s):")
hs = sorted({r["h_mm"] for r in rows})
print("object      " + "  ".join(f"h={h:4.0f}" for h in hs))
for sp in specs:
    cells = []
    for h in hs:
        rr = [r for r in rows if r["object"] == sp.name and r["h_mm"] == h]
        cells.append(f"{sum(1 for r in rr if r.get('held_lifted'))}/{len(rr)}".center(6))
    print(f"{sp.name:11s} " + "  ".join(cells))
app.close()
