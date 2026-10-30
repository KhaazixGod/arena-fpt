"""E7: how large is the frame-to-frame rendering noise of a STATIC scene (same physics state rendered repeatedly)?  Simulation only."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
from arena import scene as S
from arena.objects import INTERIM_SPECS
from arena.world import IsaacWorld
from cl0.config import load_config
sc = S.load_scene_cfg(); cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
w = IsaacWorld(app, INTERIM_SPECS, sc)
w.park_all(); w.teleport_arm(cfg.robot.home_q_deg, cfg.robot.gripper_open); w.step_seconds(0.3)
w.place([{"name": "cyl35", "a_mm": -100.0, "b_mm": -180.0, "yaw_deg": 0.0}]); w.step_seconds(0.5)
imgs = [w.render_bgr().astype(np.int16) for _ in range(12)]
out = {}
for k in (1, 2, 4, 8, 11):
    d = np.abs(imgs[k] - imgs[k - 1])
    out[f"render {k} vs {k - 1}"] = {"max": int(d.max()), "mean": round(float(d.mean()), 4), "frac_pixels_changed": round(float((d.max(axis=2) > 0).mean()), 4),
                                     "frac_changed_by_more_than_2": round(float((d.max(axis=2) > 2).mean()), 5)}
w.hard_reset(); w.park_all(); w.teleport_arm(cfg.robot.home_q_deg, cfg.robot.gripper_open); w.step_seconds(0.3)
w.place([{"name": "cyl35", "a_mm": -100.0, "b_mm": -180.0, "yaw_deg": 0.0}]); w.step_seconds(0.5)
for _ in range(8): w.render_bgr()
again = w.render_bgr().astype(np.int16)
d = np.abs(again - imgs[-1]); out["after hard reset, same scene"] = {"max": int(d.max()), "mean": round(float(d.mean()), 4), "frac_pixels_changed": round(float((d.max(axis=2) > 0).mean()), 4),
                                                                   "frac_changed_by_more_than_2": round(float((d.max(axis=2) > 2).mean()), 5)}
print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(HERE, "runs", "e7_render_noise.json"), "w"), indent=1)
app.close()
