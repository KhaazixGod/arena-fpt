"""E1 (b)(c)(d): belt speed seen by a free object (ground truth AND the rendered camera image), belt fully in view, real seconds per simulated second.

A flat 40x40x6 mm box rests on the belt; for each commanded speed the belt surface velocity is set, the box settles 1.5 s, then 4 s are measured.
Physics advances with PhysX simulate()/fetch_results() (the E0 path); the camera image is rendered after each 1/30 s.  If the image does NOT follow the
physics (stale render), the image velocity will disagree with the ground truth: that is exactly what this script is meant to reveal.
Threshold [de xuat]: |measured - commanded| / commanded <= 3 %.
"""
import argparse, json, math, os, sys, time
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--speeds", default="20,40,60,80", help="mm/s")
ap.add_argument("--settle-s", type=float, default=1.5); ap.add_argument("--measure-s", type=float, default=4.0); ap.add_argument("--fps", type=float, default=30.0)
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.makedirs(args.out, exist_ok=True)

from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
import cv2, omni.usd, omni.timeline
import omni.replicator.core as rep
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface, get_physx_simulation_interface
from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
from arena import scene as S
from arena import belt as B

ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg)
b = cfg["belt"]; cam_cfg = cfg["camera"]
u, v = S.belt_axes(b["dir_deg"])
OBJ_H = 0.006
obj = S._box(stage, "/World/TestObj", (0.040, 0.040, OBJ_H), (0, 0, 0), yaw_deg=b["dir_deg"], color=(0.85, 0.12, 0.10))
S.make_dynamic(obj, 0.02, 1.0, 1.0)
S.bind_physics_material(obj, S._physics_material(stage, "/World/Looks/ObjPhys", 1.0, 1.0))
rp = rep.create.render_product(paths.camera, (cam_cfg["width"], cam_cfg["height"]))
rgb = rep.AnnotatorRegistry.get_annotator("rgb"); rgb.attach([rp])
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(30): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
rb = sim.create_rigid_body_view("/World/TestObj")
sim_i = get_physx_simulation_interface(); phx = get_physx_interface(); DT = 1.0 / cfg["physics"]["hz"]
idx0 = np.array([0], np.int32)

# camera model (pinhole, no distortion), world pose from the scene config
K = S.camera_intrinsics(cfg)
cam_pos = np.array([x * 1e-3 for x in cam_cfg["xyz_mm"]])
Xc, Yc, Zc = np.array([u[0], u[1], 0.0]), np.array([v[0], v[1], 0.0]), np.array([0.0, 0.0, 1.0])   # Rz(phi): image right = u, image up = v, optical axis = -Zc


def pix_to_world(px, py, z):
    d = Xc * ((px - K["cx"]) / K["fx"]) + Yc * (-(py - K["cy"]) / K["fy"]) - Zc
    t = (z - cam_pos[2]) / d[2]
    return cam_pos + t * d


def world_to_pix(p):
    r = p - cam_pos
    x, y, zc = r @ Xc, r @ Yc, -(r @ Zc)
    return K["cx"] + K["fx"] * x / zc, K["cy"] - K["fy"] * y / zc


def a_of(p):                      # coordinate along the belt, mm
    return (p[0] * u[0] + p[1] * u[1]) * 1000.0


def render():
    phx.update_transformations(False, True, False)     # write PhysX poses back to USD so the renderer sees them
    rep.orchestrator.step(rt_subframes=1, delta_time=0.0, pause_timeline=False)
    return np.asarray(rgb.get_data())[..., :3]


def step_phys(t, seconds):
    n = int(round(seconds / DT))
    for _ in range(n):
        sim_i.simulate(DT, t); sim_i.fetch_results(); t += DT
    return t


def centroid_px(img):
    m = (img[..., 0].astype(int) - img[..., 1].astype(int) > 60) & (img[..., 0] > 110)
    ys, xs = np.nonzero(m)
    return (float(xs.mean()), float(ys.mean()), int(m.sum())) if len(xs) > 20 else None


# --- (c) belt fully in view: project the four belt-surface corners
half_l, half_w = b["length_mm"] / 2000.0, b["width_mm"] / 2000.0
c0 = np.array([(b["center_a_mm"] * u[0] + b["center_b_mm"] * v[0]) * 1e-3, (b["center_a_mm"] * u[1] + b["center_b_mm"] * v[1]) * 1e-3, b["z_mm"] * 1e-3])
corners = [c0 + sa * half_l * np.array([u[0], u[1], 0]) + sb * half_w * np.array([v[0], v[1], 0]) for sa in (-1, 1) for sb in (-1, 1)]
cpx = [world_to_pix(c) for c in corners]
inside = all(0 <= x < K["width"] and 0 <= y < K["height"] for x, y in cpx)
mm_per_px = (cam_cfg["xyz_mm"][2] - b["z_mm"]) * 2 * math.tan(math.radians(cam_cfg["hfov_deg"]) / 2) / K["width"]
view = {"belt_corners_px": [[round(x, 1), round(y, 1)] for x, y in cpx], "belt_fully_in_view": bool(inside), "mm_per_px_at_belt": round(mm_per_px, 4)}

# --- (b) speeds
a0 = -b["length_mm"] / 2 + 60.0                     # start 60 mm from the upstream end
bc = b["center_b_mm"]
results = []
wall0 = time.perf_counter(); sim_total = 0.0
for vmm in [float(x) for x in args.speeds.split(",")]:
    # reset object on the belt centre line, belt stopped
    B.set_speed(stage, paths.belt, b["dir_deg"], 0.0); sim_i.flush_changes()
    pos = np.array([(a0 * u[0] + bc * v[0]) * 1e-3, (a0 * u[1] + bc * v[1]) * 1e-3, (b["z_mm"] + 3.0 + 0.5) * 1e-3])
    ang = math.radians(b["dir_deg"]); q = [0.0, 0.0, math.sin(ang / 2), math.cos(ang / 2)]
    rb.set_transforms(np.array([[*pos, *q]], np.float32), idx0); rb.set_velocities(np.zeros((1, 6), np.float32), idx0)
    t = step_phys(0.0, 0.5)
    B.set_speed(stage, paths.belt, b["dir_deg"], vmm); sim_i.flush_changes()
    t = step_phys(t, args.settle_s)
    ts, a_gt, a_img, miss = [], [], [], 0
    dt_f = 1.0 / args.fps; n_f = int(round(args.measure_s * args.fps)); t_start = t
    for k in range(n_f + 1):
        p = rb.get_transforms()[0, :3].astype(float)
        c = centroid_px(render())
        ts.append(t - t_start); a_gt.append(a_of(p))
        if c is None:
            miss += 1; a_img.append(float("nan"))
        else:
            a_img.append(a_of(pix_to_world(c[0], c[1], b["z_mm"] * 1e-3 + OBJ_H)))
        if k < n_f:
            t = step_phys(t, dt_f)
    sim_total += 0.5 + args.settle_s + args.measure_s
    ts, a_gt, a_img = np.array(ts), np.array(a_gt), np.array(a_img)
    ok = np.isfinite(a_img)
    v_gt = float(np.polyfit(ts, a_gt, 1)[0]); v_img = float(np.polyfit(ts[ok], a_img[ok], 1)[0]) if ok.sum() > 10 else float("nan")
    lat_dev = float(np.abs(np.polyval(np.polyfit(ts, a_gt, 1), ts) - a_gt).max())
    results.append({"cmd_mm_s": vmm, "gt_mm_s": round(v_gt, 3), "gt_err_pct": round(100 * (v_gt - vmm) / vmm, 2),
                    "img_mm_s": round(v_img, 3), "img_err_pct": round(100 * (v_img - vmm) / vmm, 2), "img_vs_gt_pct": round(100 * (v_img - v_gt) / vmm, 2),
                    "gt_linearity_max_dev_mm": round(lat_dev, 3), "frames": n_f + 1, "frames_no_detection": miss,
                    "a_start_mm": round(float(a_gt[0]), 1), "a_end_mm": round(float(a_gt[-1]), 1)})
    print(f"v_cmd {vmm:5.1f}: GT {v_gt:7.3f} ({results[-1]['gt_err_pct']:+.2f} %)  image {v_img:7.3f} ({results[-1]['img_err_pct']:+.2f} %)  "
          f"nodet {miss}  a {a_gt[0]:.0f}->{a_gt[-1]:.0f} mm", flush=True)
wall = time.perf_counter() - wall0
img = render(); cv2.imwrite(os.path.join(args.out, "e1_camera_belt_object.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
summary = {"engine": "isaac", "speeds": results, "view": view, "wall_s": round(wall, 1), "sim_s": round(sim_total, 1),
           "wall_s_per_sim_s": round(wall / sim_total, 2), "render_frames": sum(r["frames"] for r in results),
           "threshold_proposed_pct": 3.0, "pass": bool(all(abs(r["gt_err_pct"]) <= 3.0 for r in results) and all(abs(r["img_err_pct"]) <= 3.0 for r in results))}
json.dump(summary, open(os.path.join(args.out, "e1_belt.json"), "w"), indent=1)
print(json.dumps({k: summary[k] for k in ("view", "wall_s_per_sim_s", "pass")}, indent=1))
app.close()
