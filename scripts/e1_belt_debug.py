"""E1 debug: does PhysxSurfaceVelocityAPI drag an object here, and with which stepping method?  Variants: initial velocity authored before play (init),
set at runtime (runtime); stepping with app.update() (timeline) or direct simulate()."""
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 320, "height": 240})
import omni.usd, omni.timeline
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_simulation_interface
from pxr import Gf, PhysxSchema, UsdPhysics
from arena import scene as S
variant = sys.argv[1]            # init | runtime
local = sys.argv[2] == "local"
stepper = sys.argv[3]            # update | direct
ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg); b = cfg["belt"]; u, v = S.belt_axes(b["dir_deg"])
obj = S._box(stage, "/World/TestObj", (0.040, 0.040, 0.006), (0, 0, 0), yaw_deg=b["dir_deg"])
UsdPhysics.RigidBodyAPI.Apply(obj); UsdPhysics.CollisionAPI.Apply(obj); UsdPhysics.MassAPI.Apply(obj).CreateMassAttr(0.02)
sv = PhysxSchema.PhysxSurfaceVelocityAPI(stage.GetPrimAtPath(paths.belt))
sv.GetSurfaceVelocityLocalSpaceAttr().Set(local)
vec = Gf.Vec3f(0.05, 0, 0) if local else Gf.Vec3f(0.05 * u[0], 0.05 * u[1], 0)
if variant == "init": sv.GetSurfaceVelocityAttr().Set(vec)
for _ in range(5): app.update()
tl = omni.timeline.get_timeline_interface(); tl.play()
for _ in range(20): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
rb = sim.create_rigid_body_view("/World/TestObj"); idx0 = np.array([0], np.int32)
a0 = -240.0; ang = math.radians(b["dir_deg"])
pos = [(a0 * u[0] + b["center_b_mm"] * v[0]) * 1e-3, (a0 * u[1] + b["center_b_mm"] * v[1]) * 1e-3, (b["z_mm"] + 3.5) * 1e-3]
rb.set_transforms(np.array([[*pos, 0, 0, math.sin(ang / 2), math.cos(ang / 2)]], np.float32), idx0)
if variant == "runtime": sv.GetSurfaceVelocityAttr().Set(vec)
si = get_physx_simulation_interface(); DT = 1.0 / cfg["physics"]["hz"]; t = 0.0
def a_now(): p = rb.get_transforms()[0, :3]; return (p[0] * u[0] + p[1] * u[1]) * 1000.0
a_start = a_now()
for _ in range(60 if stepper == "update" else 240):
    if stepper == "update": app.update()
    else: si.simulate(DT, t); si.fetch_results(); t += DT
print(f"RESULT variant={variant} space={'local' if local else 'world'} stepper={stepper}: a {a_start:.1f} -> {a_now():.1f} mm  (commanded 50 mm/s)", flush=True)
app.close()
