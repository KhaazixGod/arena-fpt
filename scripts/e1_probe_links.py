"""E1 helper: load the scene, report DOF/link names and whether the physics-tensor view works (Isaac 6.0)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 640, "height": 480})
import omni.usd, omni.timeline
from arena import scene as S
ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg)
for _ in range(5): app.update()
omni.timeline.get_timeline_interface().play()
for _ in range(10): app.update()
try:
    from omni.physics.tensors import create_simulation_view
except Exception as e:
    print("import omni.physics.tensors failed:", repr(e)); raise
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root)
print("count", art.count, "num_dofs", art.max_dofs, "num_links", art.max_links)
mt = art.shared_metatype
print("dof_names", list(mt.dof_names)); print("link_names", list(mt.link_names))
print("dof limits (rad)", art.get_dof_limits().reshape(-1, 2).round(3).tolist())
print("link tf shape", art.get_link_transforms().shape)
app.close()
