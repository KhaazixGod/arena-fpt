"""E5: picture of every generated object (top-down camera with names + oblique view), 12 objects per picture.  Simulation only.
    ~/env_isaac/bin/python arena/scripts/e5_objects_sheet.py --out arena/runs/e5
"""
import argparse, os, sys
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
os.makedirs(args.out, exist_ok=True)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
import cv2
from arena import scene as S
from arena.objects_gen import load_catalog
from arena.world import IsaacWorld
from cl0.config import load_config
from cl0.geometry import PlaneCalib
sc = S.load_scene_cfg(); cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
calib = PlaneCalib.load(os.path.join(HERE, "runs", "calib", "calib.json"))
specs = load_catalog()
w = IsaacWorld(app, specs, sc, debug_cam=True)
tops, sides = [], []
for k in range(0, len(specs), 12):
    batch = specs[k:k + 12]
    w.park_all(); w.teleport_arm(cfg.robot.home_q_deg, cfg.robot.gripper_open); w.step_seconds(0.2)
    pl = [{"name": s.name, "a_mm": -225.0 + 90.0 * (i % 6), "b_mm": -150.0 - 85.0 * (i // 6), "yaw_deg": 0.0} for i, s in enumerate(batch)]
    w.place(pl); w.step_seconds(0.6)
    for _ in range(2): top = w.render_bgr()
    side = w.render_debug_bgr()
    for p, s in zip(pl, batch):
        u, v = calib.world_to_pix(np.array([[-p["b_mm"], p["a_mm"]]]))[0]
        cv2.putText(top, f"{s.name}", (int(u) - 30, int(v) + 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(top, f"{s.split}{(' ' + s.hard_type) if s.hard_type else ''}", (int(u) - 30, int(v) + 64), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(args.out, f"objects_top_{k // 12}.png"), top); cv2.imwrite(os.path.join(args.out, f"objects_side_{k // 12}.png"), side)
    tops.append(cv2.resize(top, (640, 360))); sides.append(cv2.resize(side, (640, 360)))
cv2.imwrite(os.path.join(args.out, "objects_sheet.png"), np.vstack([np.hstack([t, s]) for t, s in zip(tops, sides)]))
app.close()
