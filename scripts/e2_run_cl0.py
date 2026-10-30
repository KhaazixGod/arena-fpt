"""E2: run CL-0 (unchanged, arena.toml) on the Isaac arena with the interim objects: STATIC belt and SLOW belt, one object per trial.  Simulation only.

    ~/env_isaac/bin/python arena/scripts/e2_run_cl0.py --out arena/runs/e2/cl0_dev --static 20 --belt 20 --speed 38
Trial i is fully determined by (--seed, kind, i).  Results: <out>/trials.csv (one row per trial), trial_XXXX.json, trial_XXXX_gt.npz, videos/trial_XXXX.mp4.
Ground-truth success = an object's bottom >= 25 mm above the belt for >= 2 s (arena/trial.py).  valid = 0 only for SimFault (rule 7).
"""
import argparse, csv, json, os, sys, time, traceback
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--static", type=int, default=20); ap.add_argument("--belt", type=int, default=20)
ap.add_argument("--speed", type=float, default=38.0, help="belt speed mm/s for the belt trials (L = 0.25 with w = 60 mm, tau = 0.4 s)")
ap.add_argument("--seed", type=int, default=1); ap.add_argument("--start", type=int, default=0, help="skip the first N trials of the list (resume)")
ap.add_argument("--limit", type=int, default=0); ap.add_argument("--no-video", action="store_true")
ap.add_argument("--debug-video", action="store_true", help="also record the oblique debug camera (videos/debug_trial_XXXX.mp4); doubles the render cost")
ap.add_argument("--rebuild-ctrl", action="store_true", help="diagnosis: build a fresh CL-0 stack before every trial")
ap.add_argument("--config", default="configs/arena.toml"); ap.add_argument("--calib-dir", default="runs/calib")
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
rel = lambda p: p if os.path.isabs(p) else os.path.join(HERE, p)
OUT = rel(args.out); os.makedirs(OUT, exist_ok=True)

from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
from arena import scene as S
from arena.objects import INTERIM_SPECS
from arena.platform import IsaacPlatform
from arena.trial import run_cl0_trial
from arena.world import IsaacWorld, SimFault
from cl0.config import load_config
from cl0.system import build_stack, code_sha256, file_sha256

cfg = load_config(rel(args.config))
calib_path, bg_path = os.path.join(rel(args.calib_dir), "calib.json"), os.path.join(rel(args.calib_dir), "background.npz")
stack = build_stack(cfg, calib_path, bg_path, cache_dir=os.path.expanduser("~/.cache/cl0"))
sc = S.load_scene_cfg(); world = IsaacWorld(app, INTERIM_SPECS, sc, debug_cam=args.debug_video); plat = IsaacPlatform(world, cfg)
band = sc["belt"]["object_band_x_mm"]                                   # object centres inside x in [130, 230] mm  <=>  b = -x
print(f"mm_per_step from calib: {cfg.belt.mm_per_step:.5f}  window {stack.rect.size}  band x {band}", flush=True)

trials = [("static", i) for i in range(args.static)] + [("belt", i) for i in range(args.belt)]
trials = trials[args.start:]
if args.limit: trials = trials[:args.limit]
cols = ["engine", "trial", "kind", "seed", "object", "speed_mm_s", "a0_mm", "b0_mm", "yaw_deg", "outcome", "grasp_reason_gt", "success_gt", "success_t_s", "valid", "fault",
        "t_end_s", "wall_s", "renders", "max_lift_mm"]
csv_path = os.path.join(OUT, "trials.csv")
new = not os.path.exists(csv_path)
f = open(csv_path, "a", newline=""); wr = csv.DictWriter(f, cols)
if new: wr.writeheader(); f.flush()
manifest = {"engine": "isaac", "date": time.strftime("%Y-%m-%d %H:%M:%S"), "args": vars(args), "cl0_code_sha256": code_sha256(), "arena_toml_sha256": file_sha256(rel(args.config)),
            "scene_toml_sha256": file_sha256(os.path.join(HERE, "configs", "scene.toml")), "calib_sha256": file_sha256(calib_path), "background_sha256": file_sha256(bg_path),
            "usd_sha256": file_sha256(os.path.join(HERE, sc["robot"]["usd"])), "objects": [s.__dict__ for s in INTERIM_SPECS]}
json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1, default=str)

faults = 0
for n, (kind, i) in enumerate(trials):
    tid = args.start + n
    rng = np.random.default_rng([args.seed, 0 if kind == "static" else 1, i])
    spec = INTERIM_SPECS[i % len(INTERIM_SPECS)]
    a0 = float(rng.uniform(-100, 100)) if kind == "static" else -190.0
    b0 = float(rng.uniform(-band[1], -band[0])); yaw = float(rng.uniform(0, 180))
    speed = 0.0 if kind == "static" else args.speed
    pl = [{"name": spec.name, "a_mm": a0, "b_mm": b0, "yaw_deg": yaw}]
    row = {"engine": "isaac", "trial": tid, "kind": kind, "seed": args.seed, "object": spec.name, "speed_mm_s": speed, "a0_mm": round(a0, 1), "b0_mm": round(b0, 1), "yaw_deg": round(yaw, 1)}
    vid = None if args.no_video else os.path.join(OUT, "videos", f"trial_{tid:04d}.mp4")
    try:
        dvid = os.path.join(OUT, "videos", f"debug_trial_{tid:04d}.mp4") if args.debug_video else None
        if args.rebuild_ctrl:
            stack.ctrl.close(); stack = build_stack(cfg, calib_path, bg_path, cache_dir=os.path.expanduser("~/.cache/cl0"))
        r = run_cl0_trial(plat, stack.ctrl, cfg, pl, speed, vid, dvid)
        row.update(outcome=r["outcome"], success_gt=int(r["gt"]["success"]), success_t_s=r["gt"]["success_t"], valid=1, fault="", t_end_s=round(r["t_end_s"], 2),
                   wall_s=r["wall_s"], renders=r["renders"], max_lift_mm=json.dumps(r["gt"]["max_lift_mm"]))
        np.savez_compressed(os.path.join(OUT, f"trial_{tid:04d}_gt.npz"), gt=r.pop("gt_array"), columns=np.array(r["gt_columns"]))
        json.dump({"trial": tid, "kind": kind, "seed": args.seed, "placements": pl, "speed_mm_s": speed, **r}, open(os.path.join(OUT, f"trial_{tid:04d}.json"), "w"), indent=1)
        faults = 0
    except SimFault as e:
        faults += 1
        row.update(outcome="", success_gt=0, valid=0, fault=str(e)[:200])
        print("SIMFAULT", e, flush=True)
    except Exception:                                                       # a bug of ours: stop loudly, never record it as a method failure
        traceback.print_exc(); f.close(); app.close(); sys.exit(2)
    wr.writerow(row); f.flush()
    print(f"[{n + 1}/{len(trials)}] #{tid:03d} {kind:6s} {spec.name:10s} a0={a0:6.1f} b0={b0:7.1f}: outcome={row.get('outcome')} gt={row.get('success_gt')} valid={row['valid']} "
          f"t_end={row.get('t_end_s')} wall={row.get('wall_s')}s", flush=True)
    if faults >= 3:
        print("3 consecutive sim faults: stopping (rule 7)", flush=True); break
f.close(); app.close()
