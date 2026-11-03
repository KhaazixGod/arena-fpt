"""Detection error of the real CL-0 detector against ground truth, one object at a time on a static belt, along the belt.  Tests the parallax explanation for cyl22.  Simulation only.
    env -u PYTHONPATH -u VIRTUAL_ENV ~/env_isaac/bin/python scripts/e9_parallax_probe.py runs/e9_parallax_probe
"""
import csv, json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
from arena import scene as S
from arena.world import IsaacWorld
from arena.platform import IsaacPlatform
from arena.objects_gen import load_catalog
from cl0.config import load_config
from cl0.system import build_stack
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
sc = S.load_scene_cfg(); cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
w = IsaacWorld(app, load_catalog(), sc); plat = IsaacPlatform(w, cfg)
det = build_stack(cfg, os.path.join(HERE, "runs/calib/calib.json"), os.path.join(HERE, "runs/calib/background.npz"), cache_dir=os.path.join(HERE, "runs/calib")).ctrl.det
cam = sc["camera"]["xyz_mm"]
rows = []
for name in ("cyl22", "cyl26", "box25", "mug24"):
    for a in (-280.0, -200.0, -120.0, -70.0, -40.0, 0.0):
        for b in (-205.0, -175.0):
            plat.reset_trial([{"name": name, "a_mm": a, "b_mm": b, "yaw_deg": 0.0}], hard=True)
            gt = w.gt_objects()[name]
            r = det.detect(w.render_bgr(), 0.0)
            d = next((x for x in r.dets if x.reject == ""), None)
            row = dict(name=name, a=a, b=b, gt_a=round(gt["a_mm"], 1), gt_b=round(gt["b_mm"], 1), reject=",".join(x.reject or "ok" for x in r.dets))
            if d is not None:
                row.update(det_a=round(d.a_mm, 1), det_b=round(d.b_mm, 1), err_a=round(d.a_mm - gt["a_mm"], 1), err_b=round(d.b_mm - gt["b_mm"], 1), err=round(math.hypot(d.a_mm - gt["a_mm"], d.b_mm - gt["b_mm"]), 1), width=round(d.width_mm, 1), theta=round(d.theta_deg, 1))
            rows.append(row); print(json.dumps(row), flush=True)
json.dump({"engine": "isaac", "camera_xyz_mm": cam, "rows": rows}, open(os.path.join(OUT, "parallax.json"), "w"), indent=1)
app.close()
