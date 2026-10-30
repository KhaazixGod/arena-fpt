"""E2: after a joint teleport, does the USD world pose of the gripper link (what the renderer draws) equal the PhysX pose?  Simulation only."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 640, "height": 360})
import omni.usd, omni.timeline
import omni.replicator.core as rep
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface, get_physx_simulation_interface
from pxr import Usd, UsdGeom
from arena import scene as S
ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg); cc = cfg["camera"]
rp = rep.create.render_product(paths.camera, (cc["width"], cc["height"]))
rgb = rep.AnnotatorRegistry.get_annotator("rgb"); rgb.attach([rp])
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(30): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root)
ln = list(art.shared_metatype.link_names); gi = ln.index("gripper_frame_link")
prim = [p for p in stage.Traverse() if p.GetName() == "gripper_frame_link"]
print("prims named gripper_frame_link:", [str(p.GetPath()) for p in prim])
phx = get_physx_interface(); idx0 = np.array([0], np.int32); zero = np.zeros((1, 6), np.float32)
def teleport(q5):
    q = np.radians(np.r_[q5, 0.0]).astype(np.float32)[None, :]
    art.set_dof_positions(q, idx0); art.set_dof_velocities(zero, idx0); art.set_dof_position_targets(q, idx0)
    sim.update_articulations_kinematic()
def usd_pos():
    c = UsdGeom.XformCache(); m = c.GetLocalToWorldTransform(prim[0]); return np.array(m.ExtractTranslation()) 
rows = []
for q5 in ([0, -49, 48, 91, 0], [-90, -49, 48, 91, 0], [-90, -96, 92, 70, 0], [90, -96, 92, 70, 0], [0, -49, 48, 91, 0], [-60, -30, 30, 60, 0]):
    teleport(q5)
    px = art.get_link_transforms()[0, gi, :3].astype(float)
    out = {"q": q5, "physx_mm": (px * 1000).round(1).tolist()}
    for k in range(5):
        phx.update_transformations(False, True, False)
        up = usd_pos()
        out[f"usd_after_update{k}_mm"] = (up * 1000).round(1).tolist()
        out[f"err{k}_mm"] = round(float(np.linalg.norm(up - px) * 1000), 2)
        rep.orchestrator.step(rt_subframes=1, delta_time=0.0, pause_timeline=False)
    rows.append(out); print(json.dumps({k: v for k, v in out.items() if k in ("q", "physx_mm", "err0_mm", "err1_mm", "err4_mm")}), flush=True)
app.close()
