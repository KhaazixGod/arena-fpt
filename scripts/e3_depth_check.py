"""E3: the optional depth observation (--depth) is metric and aligned with the colour image.  Camera straight down at z = 510 mm, belt surface z = -2.4 mm:
expected depth 512.4 mm on the belt and 512.4 - h on the top of an object of height h.  Simulation only.
    ~/env_isaac/bin/python arena/scripts/e3_depth_check.py --out arena/runs/e3_depth
"""
import argparse, json, os, sys
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
os.makedirs(args.out, exist_ok=True)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
import cv2
from arena import scene as S
from arena.objects import INTERIM_SPECS
from arena.world import IsaacWorld
from cl0.config import load_config
from cl0.geometry import PlaneCalib
sc = S.load_scene_cfg(); cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
calib = PlaneCalib.load(os.path.join(HERE, "runs", "calib", "calib.json"))
w = IsaacWorld(app, INTERIM_SPECS, sc, depth=True)
w.park_all(); w.teleport_arm(cfg.robot.home_q_deg, cfg.robot.gripper_open); w.step_seconds(0.3)
pl = [{"name": "cube35", "a_mm": 0.0, "b_mm": -190.0, "yaw_deg": 0.0}, {"name": "cyl28", "a_mm": 120.0, "b_mm": -160.0, "yaw_deg": 0.0}]
w.place(pl); w.step_seconds(0.5)
for _ in range(2): img = w.render_bgr()
d = w.last_depth_mm()
cam_z, top = sc["camera"]["xyz_mm"][2], w.belt_top_mm
rows = []
for name, x, y, h in (("belt", 190.0, -100.0, 0.0), ("cube35 top", 190.0, 0.0, 25.0), ("cyl28 top", 160.0, 120.0, 40.0)):
    u, v = calib.world_to_pix(np.array([[x, y]]))[0]
    patch = d[int(round(v)) - 2:int(round(v)) + 3, int(round(u)) - 2:int(round(u)) + 3]
    meas = float(np.median(patch)); exp = cam_z - (top + h)
    rows.append({"where": name, "pixel": [round(u, 1), round(v, 1)], "depth_mm": round(meas, 2), "expected_mm": round(exp, 2), "err_mm": round(meas - exp, 2)})
    print(json.dumps(rows[-1]), flush=True)
dd = np.clip((d - 450.0) / 80.0 * 255.0, 0, 255).astype(np.uint8)
cv2.imwrite(os.path.join(args.out, "depth.png"), cv2.applyColorMap(dd, cv2.COLORMAP_JET)); cv2.imwrite(os.path.join(args.out, "rgb.png"), img)
json.dump({"engine": "isaac", "shape": list(d.shape), "rows": rows}, open(os.path.join(args.out, "depth_check.json"), "w"), indent=1)
app.close()
