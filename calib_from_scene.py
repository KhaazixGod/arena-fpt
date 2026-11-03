"""Generate calib.json and background.npz for the Isaac arena FROM THE SCENE ITSELF (E2).  Simulation only.

The hardware commands ``cl0.calibrate board|belt|background`` need a real arm/belt/camera.  This script runs the SAME CL-0 functions on simulated data:

  homography   a thin plate is placed at known W positions (ground truth) -> pixel centroid (cl0.calib_tools.find_marker) -> cl0.geometry.fit_plane_homography
  belt         the plate rides the belt: belt direction and mm/pulse from cl0.geometry.fit_belt_motion, camera latency from cl0.calib_tools.estimate_latency
  background   12 renders of the empty belt with the arm at HOME -> cl0.perception.build_background (window cl0.geometry.auto_window, like `calibrate background`)
  check        the plate at 12 other W positions: pixel -> W through the fitted homography vs ground truth (independent of the fit)

Because the points come from ground truth the calibration is PERFECT up to pixel/centroid noise: stronger than a real one.  ``--noise-px`` / ``--noise-mm`` add
noise to the detections / reference positions (default OFF; the value to use is decided in E8 from real calibration errors).
    ~/env_isaac/bin/python arena/calib_from_scene.py --out arena/runs/calib
"""
import argparse, datetime as dt, json, os, sys
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="runs/calib"); ap.add_argument("--config", default="configs/arena.toml")
ap.add_argument("--belt-speed", type=float, default=60.0); ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--static-s", type=float, default=1.5); ap.add_argument("--duration-s", type=float, default=6.0)
ap.add_argument("--bg-frames", type=int, default=12); ap.add_argument("--scene-file", default="")
ap.add_argument("--noise-px", type=float, default=0.0); ap.add_argument("--noise-mm", type=float, default=0.0); ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
OUT = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(args.seed)

from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 1280, "height": 720})
import cv2
from arena import scene as S
from arena.objects import CALIB_PLATE
from arena.platform import IsaacPlatform
from arena.world import IsaacWorld
from cl0 import calib_tools as ct
from cl0.config import load_config
from cl0.geometry import PlaneCalib, Rectifier, auto_window, fit_belt_motion, fit_plane_homography, perp, unit
from cl0.perception import build_background
from cl0.system import file_sha256

cfg = load_config(args.config if os.path.isabs(args.config) else os.path.join(HERE, args.config))
cfg.belt.mm_per_step = 1.0                                     # raw pulse counts (like `calibrate belt`: counts_only)
sc = S.load_scene_cfg(args.scene_file or None); b = sc["belt"]
world = IsaacWorld(app, [CALIB_PLATE], sc)
plat = IsaacPlatform(world, cfg)
size = (cfg.camera.width, cfg.camera.height)
phi_true, mm_true, lat_true = float(b["dir_deg"]), float(b["counter_mm_per_step_true"]), float(sc["camera"]["latency_true_s"])
u, v = unit(phi_true), perp(phi_true)
cb = float(b["center_b_mm"]); ca = float(b["center_a_mm"])
wa = sc["camera"].get("window_a_mm", [ca - 220.0, ca + 220.0])      # CL-0's window along the belt: must lie inside the camera view
ctx_done = {}


def advance_frames(n):
    for _ in range(n): plat.wait_tick()


def settle_and_grab(placement):
    """place the plate (belt stopped), let it rest, return (GT (x,y) mm, frame)"""
    plat.reset_trial([placement])
    for _ in range(3): plat.wait_tick()
    return world.gt_objects()["calib_plate"]["pos_mm"][:2], world.render_bgr()


# ---------------------------------------------------------------- reference: empty belt, arm at home
plat.reset_trial([])
for _ in range(3): plat.wait_tick()
ref = np.mean([world.render_bgr().astype(np.float32) for _ in range(5)], axis=0).astype(np.uint8)
cv2.imwrite(os.path.join(OUT, "empty_belt_home.png"), ref)

# ---------------------------------------------------------------- 1. homography from known plate positions
A = [float(x) for x in np.linspace(wa[0] + 20.0, wa[1] - 20.0, 6)]; Bo = [-90.0, -30.0, 30.0, 90.0]
px, xy, used = [], [], []
for a_ in A:
    for bo in Bo:
        xy_gt, img = settle_and_grab({"name": "calib_plate", "a_mm": a_, "b_mm": cb + bo, "yaw_deg": 0.0})
        m = ct.find_marker(img, ref)
        if m is None:
            print(f"  no marker at a={a_} b={cb + bo}"); continue
        px.append([m[0], m[1]]); xy.append(xy_gt); used.append((a_, cb + bo))
px, xy = np.array(px), np.array(xy)
px_n = px + rng.normal(0, args.noise_px, px.shape); xy_n = xy + rng.normal(0, args.noise_mm, xy.shape)
calib = fit_plane_homography(px_n, xy_n, z_plane_mm=float(b["z_mm"]), image_size=size)
calib.method, calib.note = "points", "generated from the Isaac scene ground truth by arena/calib_from_scene.py (noise_px=%g, noise_mm=%g)" % (args.noise_px, args.noise_mm)
print(f"homography: {len(px)} points, rms {calib.rms_mm:.3f} mm, leave-one-out {calib.loo_rms_mm:.3f} mm", flush=True)

# ---------------------------------------------------------------- 2. belt direction, mm/pulse, camera latency (cl0.calibrate.cmd_belt, simulated)
lat_assumed = cfg.camera.latency_s
runs = []
for r in range(args.runs):
    bo = (-60.0, 0.0, 60.0, 30.0, -30.0)[r % 5]
    plat.reset_trial([{"name": "calib_plate", "a_mm": wa[0] + 10.0, "b_mm": cb + bo, "yaw_deg": 0.0}])
    tr, uvs, t_start, started = [], [], 0.0, False
    n_ticks = int((args.static_s + args.duration_s) * cfg.executor.control_hz)
    for _ in range(n_ticks):
        if not started and plat.now() >= args.static_s:
            plat.start_belt(args.belt_speed); started = True
        fr = plat.poll_frame()
        if fr is not None:
            m = ct.find_marker(fr.img, ref)
            if m is not None:
                tr.append(fr.t_capture + lat_assumed); uvs.append(m[:2])
        plat.wait_tick()
    th, sh = plat.belt.history()
    runs.append((np.asarray(tr), np.asarray(uvs), th, sh))
    print(f"  belt run {r + 1}: {len(tr)} frames with marker", flush=True)
tracks = []
for tr, uv, th, sh in runs:
    sel = tr > (tr[0] + args.static_s + 0.6)
    uvs_sel = uv[sel] + rng.normal(0, args.noise_px, uv[sel].shape)
    tracks.append((np.interp(tr[sel] - lat_assumed, th, sh), calib.pix_to_world(uvs_sel)))
phi, mm_step, lat_rms = fit_belt_motion(tracks)
print(f"belt direction {phi:.3f} deg (true {phi_true}), mm/pulse {mm_step:.5f} (true {mm_true}), lateral rms {lat_rms:.3f} mm", flush=True)
lats, lat_rows = [], []
for k, (tr, uv, th, sh) in enumerate(runs):
    a_obs = calib.pix_to_world(uv) @ unit(phi)
    try:
        d, e, sens = ct.estimate_latency(tr, a_obs, th, sh * mm_step)
    except ValueError as ex:
        print(f"  run {k + 1}: no latency estimate: {ex}"); continue
    lat_rows.append({"run": k + 1, "latency_s": d, "rms_mm": e, "sensitivity_mm": sens})
    print(f"  run {k + 1}: latency {d * 1e3:6.1f} ms (rms {e:.2f} mm, sensitivity {sens:.2f} mm)", flush=True)
    if sens > 0.2: lats.append(d)
lat = float(np.median(lats)) if lats else 0.0
calib.belt_dir_deg, calib.mm_per_step, calib.latency_s = float(phi), float(mm_step), lat
calib_path = os.path.join(OUT, "calib.json"); calib.save(calib_path)
print(f"camera latency {lat * 1e3:.1f} ms (true {lat_true * 1e3:.0f} ms, CL-0 believes {lat_assumed * 1e3:.0f} ms); saved {calib_path}", flush=True)

# ---------------------------------------------------------------- 3. independent check: 12 new positions, pixel -> W with the FITTED homography vs GT
errs, hold = [], []
for i in range(12):
    a_ = float(rng.uniform(wa[0] + 15.0, wa[1] - 15.0)); b_ = float(rng.uniform(cb - 95, cb + 95)); yaw = float(rng.uniform(0, 90))
    xy_gt, img = settle_and_grab({"name": "calib_plate", "a_mm": a_, "b_mm": b_, "yaw_deg": yaw})
    m = ct.find_marker(img, ref)
    if m is None: continue
    e = float(np.linalg.norm(calib.pix_to_world(np.array([[m[0], m[1]]]))[0] - xy_gt)); errs.append(e)
    hold.append({"a_mm": round(a_, 1), "b_mm": round(b_, 1), "err_mm": round(e, 3)})
print(f"hold-out check: {len(errs)} points, mean {np.mean(errs):.3f} mm, max {np.max(errs):.3f} mm", flush=True)

# ---------------------------------------------------------------- 4. background: empty belt, arm at HOME  (cl0.calibrate.cmd_background, simulated)
ar = (float(wa[0]), float(wa[1])); br = (cb - b["width_mm"] / 2 - 15.0, cb + b["width_mm"] / 2 + 15.0)      # belt + 15 mm across (as cl0.sim.harness), camera.window_a_mm along the belt
win = auto_window(calib, cfg.perception.res_mm, 10.0, ar, br)
rect = Rectifier(calib, win)
plat.reset_trial([])
frames = []
for i in range(args.bg_frames):
    for _ in range(5): plat.wait_tick()                          # 0.1 s apart
    frames.append((world.render_bgr(), 0.0))
bg = build_background(frames, rect, cfg.perception, textured=cfg.belt.textured, period_mm=cfg.belt.period_mm)
bg.meta = dict(calib_sha=file_sha256(calib_path), created=dt.datetime.now().astimezone().isoformat(timespec="seconds"), n_frames=len(frames), textured=cfg.belt.textured)
bg_path = os.path.join(OUT, "background.npz"); bg.save(bg_path)
cv2.imwrite(os.path.join(OUT, "background_preview.png"), np.clip(bg.window(0.0)[0], 0, 255).astype(np.uint8))
img = frames[-1][0].copy()
ab = np.array([[win.a_min, win.b_min], [win.a_max, win.b_min], [win.a_max, win.b_max], [win.a_min, win.b_max]])
xyw = ab[:, :1] * unit(phi) + ab[:, 1:2] * perp(phi)
cv2.polylines(img, [np.round(calib.world_to_pix(xyw)).astype(np.int32).reshape(-1, 1, 2)], True, (0, 255, 0), 2)
c0 = calib.world_to_pix(xyw.mean(axis=0))[0]; c1 = calib.world_to_pix(xyw.mean(axis=0) + 60.0 * unit(phi))[0]
cv2.arrowedLine(img, tuple(int(x) for x in c0), tuple(int(x) for x in c1), (0, 255, 255), 2, tipLength=0.3)
cv2.imwrite(os.path.join(OUT, "background_window.png"), img)
sig = float(np.median(bg.sigma))
print(f"background: window a [{win.a_min:.0f},{win.a_max:.0f}] b [{win.b_min:.0f},{win.b_max:.0f}] ({rect.size[0]}x{rect.size[1]} px), sigma median {sig:.2f}, threshold "
      f"{max(cfg.perception.k_sigma * sig, cfg.perception.t_min):.0f}", flush=True)

report = {"engine": "isaac", "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "noise_px": args.noise_px, "noise_mm": args.noise_mm, "seed": args.seed,
          "homography": {"n_points": int(len(px)), "rms_mm": calib.rms_mm, "loo_rms_mm": calib.loo_rms_mm, "z_plane_mm": calib.z_plane_mm},
          "belt": {"phi_fit_deg": phi, "phi_true_deg": phi_true, "mm_per_step_fit": mm_step, "mm_per_step_true": mm_true,
                   "mm_per_step_err_pct": 100.0 * (mm_step - mm_true) / mm_true, "lateral_rms_mm": lat_rms},
          "latency": {"fit_s": lat, "true_s": lat_true, "assumed_by_cl0_s": lat_assumed, "runs": lat_rows},
          "holdout": {"n": len(errs), "mean_mm": float(np.mean(errs)), "max_mm": float(np.max(errs)), "points": hold},
          "background": {"window": [win.a_min, win.a_max, win.b_min, win.b_max], "size_px": list(rect.size), "sigma_median": sig,
                         "calib_sha": bg.meta["calib_sha"]},
          "files": {"calib": calib_path, "background": bg_path}}
json.dump(report, open(os.path.join(OUT, "calib_report.json"), "w"), indent=1)
app.close()
