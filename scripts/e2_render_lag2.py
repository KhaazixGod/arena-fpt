"""E2: image staleness measured against ground truth.  A thin plate rides the belt at v; after each 1/30 s of physics the camera renders once and the plate
centroid in the image (pinhole inverse, belt plane + plate top) is compared with the GT position read from PhysX at the SAME instant.
lag_s = (a_img - a_gt) / (-v)  (positive = the image shows an OLDER state).  v = 0 gives the bias (parallax, centroid) which is subtracted.
Recipes: A = phx.update_transformations + orchestrator.step(rt_subframes=1, delta_time=0)  (the E1 path)
         B = same with rt_subframes=3;   C = A preceded by app.update() (checks whether app.update() also steps physics: counted by GT travel).
Simulation only.  ~/env_isaac/bin/python arena/scripts/e2_render_lag2.py --out arena/runs/e2/render_lag
"""
import argparse, json, math, os, sys
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--v", type=float, default=150.0)
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
os.makedirs(args.out, exist_ok=True)

from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
import omni.usd, omni.timeline
import omni.replicator.core as rep
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface, get_physx_simulation_interface
from arena import scene as S, belt as B

ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg); cc, b = cfg["camera"], cfg["belt"]
OBJ_H = 0.006
obj = S._box(stage, "/World/Plate", (0.040, 0.040, OBJ_H), (0, 0, 0), yaw_deg=b["dir_deg"], color=(0.85, 0.12, 0.10))
S.make_dynamic(obj, 0.02, 1.0, 1.0); S.bind_physics_material(obj, S._physics_material(stage, "/World/Looks/PlatePhys", 1.0, 1.0))
rp = rep.create.render_product(paths.camera, (cc["width"], cc["height"]))
rgb = rep.AnnotatorRegistry.get_annotator("rgb"); rgb.attach([rp])
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(30): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
rb = sim.create_rigid_body_view("/World/Plate")
phx = get_physx_interface(); sim_i = get_physx_simulation_interface()
HZ = float(cfg["physics"]["hz"]); DT = 1.0 / HZ; idx0 = np.array([0], np.int32)
K = S.camera_intrinsics(cfg); u, v = S.belt_axes(b["dir_deg"])
cam = np.array([x * 1e-3 for x in cc["xyz_mm"]])
Xc, Yc, Zc = np.array([u[0], u[1], 0.0]), np.array([v[0], v[1], 0.0]), np.array([0.0, 0.0, 1.0])


def pix_to_a(px, py, z):
    d = Xc * ((px - K["cx"]) / K["fx"]) + Yc * (-(py - K["cy"]) / K["fy"]) - Zc
    p = cam + ((z - cam[2]) / d[2]) * d
    return (p[0] * u[0] + p[1] * u[1]) * 1000.0


def centroid(img):
    m = (img[..., 0].astype(int) - img[..., 1].astype(int) > 60) & (img[..., 0] > 110)
    ys, xs = np.nonzero(m)
    return (float(xs.mean()), float(ys.mean())) if len(xs) > 20 else None


def render(recipe):
    if recipe == "C": app.update()
    phx.update_transformations(False, True, False)
    rep.orchestrator.step(rt_subframes=3 if recipe == "B" else 1, delta_time=0.0, pause_timeline=False)
    return np.asarray(rgb.get_data())[..., :3]


def run(recipe, vmm):
    """returns (mean offset a_img - a_gt [mm], travel check: GT a(end)-a(start) vs v * simulated seconds [mm])"""
    B.set_speed(stage, paths.belt, b["dir_deg"], 0.0); sim_i.flush_changes()
    pos = np.array([(-150.0 * u[0] + b["center_b_mm"] * v[0]) * 1e-3, (-150.0 * u[1] + b["center_b_mm"] * v[1]) * 1e-3, (b["z_mm"] + 3.0 + 0.5) * 1e-3])
    ang = math.radians(b["dir_deg"]); q = [0.0, 0.0, math.sin(ang / 2), math.cos(ang / 2)]
    rb.set_transforms(np.array([[*pos, *q]], np.float32), idx0); rb.set_velocities(np.zeros((1, 6), np.float32), idx0)
    t = 0.0
    for _ in range(int(0.5 * HZ)): sim_i.simulate(DT, t); sim_i.fetch_results(); t += DT
    B.set_speed(stage, paths.belt, b["dir_deg"], vmm); sim_i.flush_changes()
    for _ in range(int(1.0 * HZ)): sim_i.simulate(DT, t); sim_i.fetch_results(); t += DT          # settle to belt speed
    offs, a0, steps = [], None, 0
    for k in range(40):
        for _ in range(int(round(HZ / 30.0))): sim_i.simulate(DT, t); sim_i.fetch_results(); t += DT; steps += 1
        p = rb.get_transforms()[0, :3].astype(float)
        a_gt = (p[0] * u[0] + p[1] * u[1]) * 1000.0
        a0 = a_gt if a0 is None else a0
        c = centroid(render(recipe))
        if c is not None:
            offs.append(pix_to_a(c[0], c[1], b["z_mm"] * 1e-3 + OBJ_H) - a_gt)
        a_last = a_gt
    return float(np.mean(offs)), float(np.std(offs)), a_last - a0, steps


res = {}
for recipe in ("A", "B", "C"):
    o0, s0, tr0, st0 = run(recipe, 0.0)
    o1, s1, tr1, st1 = run(recipe, args.v)
    exp_travel = args.v * (st1 - int(round(HZ / 30.0))) * DT      # frames 1..39 -> 39 intervals
    lag_s = -(o1 - o0) / args.v
    res[recipe] = {"offset_v0_mm": round(o0, 3), "offset_v_mm": round(o1, 3), "std_v_mm": round(s1, 3), "lag_s": round(lag_s, 4),
                   "lag_frames_at_30fps": round(lag_s * 30, 2), "gt_travel_mm": round(tr1, 2), "expected_travel_mm_if_no_extra_physics": round(exp_travel, 2)}
    print(recipe, json.dumps(res[recipe]), flush=True)
json.dump({"engine": "isaac", "v_mm_s": args.v, "physics_hz": HZ, "result": res}, open(os.path.join(args.out, "render_lag2.json"), "w"), indent=1)
app.close()
