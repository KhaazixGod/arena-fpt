"""E2: how many render calls after a pose change does the camera image show the NEW pose?  (lockstep: the image must be of the state at capture time)

Teleports the arm between two very different poses, and a dynamic box on the belt; after each change renders repeatedly and reports the pixel difference
to the converged image for k = 0, 1, 2, ... renders, for several render recipes.  Simulation only.
    ~/env_isaac/bin/python arena/scripts/e2_render_lag.py --out arena/runs/e2/render_lag
"""
import argparse, json, os, sys
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
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
from arena import scene as S

ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg); cc = cfg["camera"]
box = S._box(stage, "/World/Box", (0.04, 0.04, 0.03), (0, 0, 0), color=(0.85, 0.12, 0.10)); S.make_dynamic(box, 0.05, 0.8, 0.8)
rp = rep.create.render_product(paths.camera, (cc["width"], cc["height"]))
rgb = rep.AnnotatorRegistry.get_annotator("rgb"); rgb.attach([rp])
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(30): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root)
rb = sim.create_rigid_body_view("/World/Box")
phx = get_physx_interface(); sim_i = get_physx_simulation_interface()
idx0 = np.array([0], np.int32); zero6 = np.zeros((1, 6), np.float32)


def teleport(q5):
    q = np.radians(np.r_[q5, 0.0]).astype(np.float32)[None, :]
    art.set_dof_positions(q, idx0); art.set_dof_velocities(zero6, idx0); art.set_dof_position_targets(q, idx0)
    sim.update_articulations_kinematic()


def put_box(x_mm, y_mm):
    rb.set_transforms(np.array([[x_mm * 1e-3, y_mm * 1e-3, 0.0125, 0, 0, 0, 1]], np.float32), idx0)
    rb.set_velocities(np.zeros((1, 6), np.float32), idx0)


def render(mode):
    phx.update_transformations(False, True, False)
    if mode == "step1":
        rep.orchestrator.step(rt_subframes=1, delta_time=0.0, pause_timeline=False)
    elif mode == "step3":
        rep.orchestrator.step(rt_subframes=3, delta_time=0.0, pause_timeline=False)
    elif mode == "update_then_step1":
        app.update(); rep.orchestrator.step(rt_subframes=1, delta_time=0.0, pause_timeline=False)
    return np.asarray(rgb.get_data())[..., :3].astype(np.int16)


poses = [[0, -49, 48, 91, 0], [-90, -96, 92, 70, 0], [60, -30, 30, 60, 0]]
out = {}
for mode in ("step1", "step3", "update_then_step1"):
    rows = []
    for i in range(6):
        teleport(poses[i % 3]); put_box(150 + 20 * (i % 3), -100 + 100 * (i % 3))
        imgs = [render(mode) for _ in range(8)]
        final = imgs[-1]
        d = [int((np.abs(im - final).max(axis=2) > 25).sum()) for im in imgs[:-1]]       # pixels still differing from the converged image
        rows.append(d)
    arr = np.array(rows)
    # first k at which the image equals the converged one (<= 50 px differing)
    first = [int(np.argmax(r <= 50)) if (r <= 50).any() else None for r in arr]
    out[mode] = {"differing_px_by_render_index": arr.tolist(), "first_converged_render_index": first}
    print(mode, "first converged index per change:", first, flush=True)
json.dump({"engine": "isaac", "result": out}, open(os.path.join(args.out, "render_lag.json"), "w"), indent=1)
app.close()
