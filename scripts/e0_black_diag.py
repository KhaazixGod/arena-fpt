"""E0 diagnostic: why is the first Replicator RGB frame black? Print mean pixel and alpha as updates accumulate, with/without a dome light."""
import sys, time
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 640, "height": 480})
import numpy as np, omni.usd, omni.timeline
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdPhysics, UsdShade
import omni.replicator.core as rep

ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.Xform.Define(stage, "/World")
g = UsdGeom.Cube.Define(stage, "/World/Ground"); g.GetSizeAttr().Set(1.0)
UsdGeom.XformCommonAPI(g).SetScale(Gf.Vec3f(4, 4, 0.1)); UsdGeom.XformCommonAPI(g).SetTranslate(Gf.Vec3d(0, 0, -0.05))
g.CreateDisplayColorAttr([(0.7, 0.7, 0.7)])
c = UsdGeom.Cube.Define(stage, "/World/Cube"); c.GetSizeAttr().Set(0.1); UsdGeom.XformCommonAPI(c).SetTranslate(Gf.Vec3d(0, 0, 0.05))
c.CreateDisplayColorAttr([(0.9, 0.1, 0.1)])
def paint(prim_path, rgb, name):
    m = UsdShade.Material.Define(stage, f"/World/Looks/{name}")
    sh = UsdShade.Shader.Define(stage, f"/World/Looks/{name}/Shader"); sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb)); sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.8)
    m.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
    UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath(prim_path)).Bind(m)
if "--paint" in sys.argv:
    paint("/World/Ground", (0.35, 0.35, 0.35), "grey"); paint("/World/Cube", (0.85, 0.1, 0.1), "red")
use_dome = "--dome" in sys.argv
if use_dome:
    UsdLux.DomeLight.Define(stage, "/World/Dome").CreateIntensityAttr(1000.0)
UsdLux.DistantLight.Define(stage, "/World/Sun").CreateIntensityAttr(3000.0)
cam = UsdGeom.Camera.Define(stage, "/World/Camera"); cam.GetFocalLengthAttr().Set(18.0)
if "--clip" in sys.argv: cam.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 20.0))
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
cam.GetHorizontalApertureAttr().Set(20.955); cam.GetVerticalApertureAttr().Set(15.7)
UsdGeom.XformCommonAPI(cam).SetTranslate(Gf.Vec3d(0, 0, 0.8))
rp = rep.create.render_product("/World/Camera", (640, 480)); a = rep.AnnotatorRegistry.get_annotator("rgb"); a.attach([rp])
omni.timeline.get_timeline_interface().play()
print("dome:", use_dome)
for i in range(1, 91):
    app.update()
    if i % 30 == 0:
        rep.orchestrator.step(rt_subframes=4, delta_time=0.0, pause_timeline=False)
        d = np.asarray(a.get_data())
        print(f"update {i:3d}: shape {d.shape} rgb mean {d[..., :3].mean():6.2f}  alpha mean {d[..., 3].mean() if d.ndim==3 and d.shape[-1]==4 else float('nan'):6.2f}", flush=True)
import cv2; cv2.imwrite("runs/e0/diag_" + "_".join(a for a in sys.argv[1:]).replace("--","") + ".png", cv2.cvtColor(np.asarray(a.get_data())[..., :3], cv2.COLOR_RGB2BGR))
app.close()
