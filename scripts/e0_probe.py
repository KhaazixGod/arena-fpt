"""E0: probe Isaac Sim (headless) -- versions, extensions, empty scene with one camera, ms per physics step, ms per rendered frame.

    ~/env_isaac/bin/python arena/scripts/e0_probe.py --out arena/runs/e0 [--width 1920 --height 1080] [--physics-hz 240]

Simulation only. Writes <out>/e0_probe.json and <out>/e0_frame_<W>x<H>.png. Nothing here touches the real robot, belt or camera.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--width", type=int, default=1920)
ap.add_argument("--height", type=int, default=1080)
ap.add_argument("--physics-hz", type=float, default=240.0)
ap.add_argument("--steps", type=int, default=600)
ap.add_argument("--frames", type=int, default=60)
ap.add_argument("--enable-ext", default="", help="comma list of extensions to enable at runtime before the scene is built (e.g. isaacsim.asset.gen.conveyor); enabling BOTH conveyor and ros2.bridge segfaulted once at the first timeline updates (29/10)")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)


def vram_used_mib() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    return int(out.split()[0])


report: dict = {"python": sys.version.split()[0], "platform": platform.platform(), "args": vars(args)}
report["vram_mib_before_app"] = vram_used_mib()

t0 = time.perf_counter()
from isaacsim import SimulationApp  # noqa: E402  (must precede every other omni import)

app = SimulationApp({"headless": True, "width": args.width, "height": args.height})
report["app_start_s"] = round(time.perf_counter() - t0, 1)

import carb  # noqa: E402
import numpy as np  # noqa: E402
import omni.kit.app  # noqa: E402
import omni.timeline  # noqa: E402
import omni.usd  # noqa: E402
from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdLux, UsdPhysics  # noqa: E402

try:
    import importlib.metadata as md
    report["isaacsim"] = md.version("isaacsim")
except Exception as e:  # noqa: BLE001
    report["isaacsim"] = f"? ({e})"
report["numpy_in_isaac_python"] = np.__version__
report["vram_mib_after_app"] = vram_used_mib()

ext_mgr = omni.kit.app.get_app().get_extension_manager()
want = ["isaacsim.asset.gen.conveyor", "isaacsim.ros2.bridge", "omni.replicator.core", "isaacsim.sensors.camera", "omni.physx", "isaacsim.core.api"]
report["extensions"] = {}
for name in want:
    try:
        was = bool(ext_mgr.is_extension_enabled(name))
        if not was and name in args.enable_ext.split(","):
            ext_mgr.set_extension_enabled_immediate(name, True)
        report["extensions"][name] = {"enabled_at_start": was, "enabled_now": bool(ext_mgr.is_extension_enabled(name))}
    except Exception as e:  # noqa: BLE001
        report["extensions"][name] = f"error: {type(e).__name__}: {e}"

# ---- scene: ground, light, one dynamic cube, one camera
ctx = omni.usd.get_context()
ctx.new_stage()
stage = ctx.get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())

scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
scene.CreateGravityMagnitudeAttr(9.81)
px = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
px.CreateTimeStepsPerSecondAttr(args.physics_hz)
px.CreateEnableCCDAttr(False)

ground = UsdGeom.Cube.Define(stage, "/World/Ground")
ground.GetSizeAttr().Set(1.0)
UsdGeom.XformCommonAPI(ground).SetScale(Gf.Vec3f(4, 4, 0.1))
UsdGeom.XformCommonAPI(ground).SetTranslate(Gf.Vec3d(0, 0, -0.05))
UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

cube = UsdGeom.Cube.Define(stage, "/World/Cube")
cube.GetSizeAttr().Set(0.04)
UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(0, 0, 0.3))
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(0.05)

# A DistantLight alone renders BLACK here (arena/scripts/e0_black_diag.py, 29/10); a DomeLight is what lights the scene.
dome = UsdLux.DomeLight.Define(stage, "/World/Dome")
dome.CreateIntensityAttr(300.0)
ground.CreateDisplayColorAttr([(0.55, 0.55, 0.55)])
cube.CreateDisplayColorAttr([(0.85, 0.15, 0.15)])

cam = UsdGeom.Camera.Define(stage, "/World/Camera")
cam.GetFocalLengthAttr().Set(18.0)
cam.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 20.0))   # USD default near plane is 1 STAGE UNIT = 1 m here: the ground at 0.8 m was clipped away (black/flat frames)
cam.GetHorizontalApertureAttr().Set(20.955)
cam.GetVerticalApertureAttr().Set(20.955 * args.height / args.width)
xf = UsdGeom.XformCommonAPI(cam)
xf.SetTranslate(Gf.Vec3d(0, 0, 0.8))   # USD camera looks down its -Z: straight down, +Y up

for _ in range(5):
    app.update()

# ---- render product + RGB annotator
import omni.replicator.core as rep  # noqa: E402

rp = rep.create.render_product("/World/Camera", (args.width, args.height))
rgb = rep.AnnotatorRegistry.get_annotator("rgb")
rgb.attach([rp])

tl = omni.timeline.get_timeline_interface()
tl.play()
for _ in range(30):                      # warm-up: the first rendered frames are black while shaders/textures stream in
    app.update()
rep.orchestrator.step(rt_subframes=4, delta_time=0.0, pause_timeline=False)

# ---- ms per rendered frame (app.update + annotator readback)
ts = []
for _ in range(args.frames):
    a = time.perf_counter()
    rep.orchestrator.step(rt_subframes=1, delta_time=None, pause_timeline=False)
    data = rgb.get_data()
    ts.append((time.perf_counter() - a) * 1e3)
img = np.asarray(data)
report["frame"] = {
    "shape": list(img.shape), "dtype": str(img.dtype),
    "orchestrator_step_plus_readback_ms": {"p50": round(float(np.percentile(ts, 50)), 1), "p95": round(float(np.percentile(ts, 95)), 1), "n": len(ts)},
    "mean_pixel": [round(float(x), 1) for x in img[..., :3].reshape(-1, 3).mean(0)] if img.size else None,
}
report["vram_mib_after_render"] = vram_used_mib()
try:
    import cv2
    if img.size:
        cv2.imwrite(os.path.join(args.out, f"e0_frame_{args.width}x{args.height}.png"), cv2.cvtColor(img[..., :3], cv2.COLOR_RGB2BGR))
except Exception as e:  # noqa: BLE001
    report["png_error"] = str(e)

# ---- physics-only stepping rate: how many physics steps does one app.update run, and how long does it take
cube_prim = stage.GetPrimAtPath("/World/Cube")
rep_ = {}
try:
    from omni.physx import get_physx_simulation_interface
    sim = get_physx_simulation_interface()
    rep_["physx_simulation_interface"] = True
    dt = 1.0 / args.physics_hz
    t = 0.0
    a = time.perf_counter()
    for _ in range(args.steps):
        sim.simulate(dt, t)
        sim.fetch_results()
        t += dt
    ms = (time.perf_counter() - a) * 1e3 / args.steps
    rep_["simulate_fetch_ms_per_step"] = round(ms, 3)
    rep_["note"] = "simulate()/fetch_results() called directly while the timeline is playing; may not be the lockstep path (to confirm in E2)"
except Exception as e:  # noqa: BLE001
    rep_["error"] = f"{type(e).__name__}: {e}"
report["physics_direct"] = rep_

# physics steps per app.update, from the cube's fall (timeline-driven)
tl.stop()
app.update()
tl.play()
app.update()
z = []
for _ in range(30):
    app.update()
    tr = UsdGeom.XformCommonAPI(cube_prim).GetXformVectors(0)[0]
    z.append(float(tr[2]))
report["cube_z_after_30_updates"] = round(z[-1], 4)

report["vram_mib_peak_seen"] = max(report["vram_mib_after_render"], vram_used_mib())
with open(os.path.join(args.out, "e0_probe.json"), "w") as f:
    json.dump(report, f, indent=2)
print(json.dumps(report, indent=2))
app.close()
