"""E2: pick a home pose whose arm is OUT of the belt region of the camera image (the empty-belt background is built with the arm at home;
an arm that sits on the belt there leaves a "ghost" foreground blob when it moves away).

For each candidate joint vector: teleport (no physics), render, count arm pixels (not belt-coloured) inside the projected belt rectangle and inside the object band
(scene.toml belt.object_band_x_mm), then hold 1.0 s of physics under gravity to see the sag.  Simulation only.
    ~/env_isaac/bin/python arena/scripts/e2_home_probe.py --out arena/runs/e2/home_probe
"""
import argparse, json, math, os, sys
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
os.makedirs(args.out, exist_ok=True)

from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
import cv2, omni.usd, omni.timeline
import omni.replicator.core as rep
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface, get_physx_simulation_interface
from arena import scene as S
from cl0.kinematics import SO101Kinematics

ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg)
b, cc = cfg["belt"], cfg["camera"]
rp = rep.create.render_product(paths.camera, (cc["width"], cc["height"]))
rgb = rep.AnnotatorRegistry.get_annotator("rgb"); rgb.attach([rp])
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(30): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root)
phx = get_physx_interface(); sim_i = get_physx_simulation_interface(); DT = 1.0 / cfg["physics"]["hz"]
idx0 = np.array([0], np.int32); zero = np.zeros((1, 6), np.float32)
kin = SO101Kinematics()
link_names = list(art.shared_metatype.link_names)

K = S.camera_intrinsics(cfg)
u, v = S.belt_axes(b["dir_deg"])
cam = np.array([x * 1e-3 for x in cc["xyz_mm"]])
Xc, Yc, Zc = np.array([u[0], u[1], 0.0]), np.array([v[0], v[1], 0.0]), np.array([0.0, 0.0, 1.0])


def w2p(p):
    r = np.asarray(p, float) - cam
    x, y, zc = r @ Xc, r @ Yc, -(r @ Zc)
    return K["cx"] + K["fx"] * x / zc, K["cy"] - K["fy"] * y / zc


def rect_mask(x_lo_mm, x_hi_mm, a_lo_mm, a_hi_mm, z_mm):
    """polygon of the W-region {x in [x_lo, x_hi], a (along belt) in [a_lo, a_hi]} at height z (belt dir 90 deg => a = y)."""
    pts = []
    for a_, x_ in ((a_lo_mm, x_lo_mm), (a_hi_mm, x_lo_mm), (a_hi_mm, x_hi_mm), (a_lo_mm, x_hi_mm)):
        p = np.array([x_ * 1e-3, a_ * 1e-3, z_mm * 1e-3]) if abs(b["dir_deg"] - 90) < 1e-6 else None
        pts.append(w2p(p))
    m = np.zeros((cc["height"], cc["width"]), np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts)).astype(np.int32)], 1)
    return m.astype(bool)


assert abs(b["dir_deg"] - 90.0) < 1e-6, "probe written for phi = 90 deg"
belt_x_lo, belt_x_hi = -b["center_b_mm"] - b["width_mm"] / 2, -b["center_b_mm"] + b["width_mm"] / 2
belt_m = rect_mask(belt_x_lo, belt_x_hi, -220, 220, b["z_mm"])                     # perception window half length 220 mm (harness default)
bx = b["object_band_x_mm"]
band_m = rect_mask(bx[0], bx[1], -220, 220, b["z_mm"])


def render():
    phx.update_transformations(False, True, False)
    rep.orchestrator.step(rt_subframes=1, delta_time=0.0, pause_timeline=False)
    return np.asarray(rgb.get_data())[..., :3][..., ::-1].copy()      # BGR


def teleport(q5, g_deg=0.0):
    q = np.radians(np.r_[q5, g_deg]).astype(np.float32)[None, :]
    art.set_dof_positions(q, idx0); art.set_dof_velocities(zero, idx0); art.set_dof_position_targets(q, idx0)
    sim.update_articulations_kinematic()


cands = {
    "A_cl0_default": [0, -49, 48, 91, 0],
    "B_rest_fold": [0, -96, 92, 70, 0],
    "C_fold_wrist_down": [0, -96, 92, 90, 0],
    "D_fold_wrist_mid": [0, -90, 85, 60, 0],
    "E_pan_m90_default": [-90, -49, 48, 91, 0],
    "F_pan_m90_fold": [-90, -96, 92, 70, 0],
    "G_pan_p90_fold": [90, -96, 92, 70, 0],
    "H_pan_m60_fold": [-60, -96, 92, 70, 0],
    "I_pan_p90_default": [90, -49, 48, 91, 0],
    "J_pan_p75_default": [75, -49, 48, 91, 0],
    "K_pan_p90_mid": [90, -70, 70, 80, 0],
}
teleport(cands["B_rest_fold"]);
for _ in range(10): app.update()
rows = []
sheet = []
for name, q5 in cands.items():
    teleport(q5)
    sim_i.simulate(DT, 0.0); sim_i.fetch_results()                           # the renderer (Fabric) only follows PhysX after a stepped fetch_results, not after a bare teleport (29/10)
    for _ in range(2): img = render()
    ref = np.median(img[belt_m].reshape(-1, 3), axis=0)                     # belt colour (median is the belt unless the arm covers more than half of it)
    diff = np.abs(img.astype(int) - ref.astype(int)).max(axis=2) > 30
    n_belt, n_band = int((diff & belt_m).sum()), int((diff & band_m).sum())
    p_ref, _ = kin.fk(np.array(q5, float))
    # 1.0 s of physics under gravity at the held pose: sag + finite check
    t = 0.0; bad = False
    for _ in range(int(1.0 / DT)):
        sim_i.simulate(DT, t); sim_i.fetch_results(); t += DT
        if not np.all(np.isfinite(art.get_dof_velocities())): bad = True; break
    qm = np.degrees(art.get_dof_positions()[0, :5]) if not bad else None
    tf = art.get_link_transforms()[0, link_names.index("gripper_frame_link")] if not bad else None
    row = {"name": name, "q_deg": q5, "tcp_fk_mm": [round(float(x), 1) for x in p_ref], "arm_px_in_belt_window": n_belt, "arm_px_in_object_band": n_band,
           "belt_window_px": int(belt_m.sum()), "band_px": int(band_m.sum()), "nan_after_1s": bad,
           "sag_deg_max": None if bad else round(float(np.max(np.abs(qm - np.array(q5)))), 2),
           "tcp_z_after_1s_mm": None if bad else round(float(tf[2] * 1000), 1)}
    rows.append(row); print(json.dumps(row), flush=True)
    vis = img.copy(); cv2.putText(vis, f"{name} belt_px={n_belt} band_px={n_band}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cnt, _ = cv2.findContours(belt_m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(vis, cnt, -1, (0, 255, 0), 1)
    cnt, _ = cv2.findContours(band_m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(vis, cnt, -1, (255, 128, 0), 1)
    cv2.imwrite(os.path.join(args.out, f"home_{name}.png"), vis)
    sheet.append(cv2.resize(vis, (640, 360)))
while len(sheet) % 2: sheet.append(np.zeros_like(sheet[0]))
grid = np.vstack([np.hstack(sheet[i:i + 2]) for i in range(0, len(sheet), 2)])
cv2.imwrite(os.path.join(args.out, "home_candidates_sheet.png"), grid)
json.dump({"engine": "isaac", "rows": rows}, open(os.path.join(args.out, "home_probe.json"), "w"), indent=1)
app.close()
