"""Run methods on the Isaac arena and write results in the G0 format (+ arena columns).  Simulation only.

    cd arena && ~/env_isaac/bin/python -m arena.run_arena --methods CL0,NOOP,ORACLE --cells dev_C0,dev_C2 --speeds L0,L0.25 --n 10 --out runs/<run_id>
    # your own method, no edit of the arena:   --methods CL0,mypkg.mymodule:make_method   (make_method(ctx: MethodContext) -> controller, see arena/methods/base.py)

Per trial: one row in <out>/trials.csv (cl0.run_g0.CSV_COLUMNS + arena columns), trial_XXXX.json (events, phases, labels, timings), trial_XXXX_log.csv (the method's own
log), trial_XXXX_gt.npz (ground truth per tick), optional videos/.  manifest.json once.  Running the same command again RESUMES (skips keys with a valid row).
Plan order: arrangement -> speed -> method, so paired methods see the same arrangement close in time.  Speeds: L<x> = x * w / tau (w = perception.grasp.gripper_w_mm,
tau = --tau), L0 = belt stopped, v<x> = x mm/s.  valid = 0 ONLY for SimFault (rule 7); an exception inside a method is that method's failure.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import glob
import hashlib
import importlib.metadata as md
import json
import os
import subprocess
import sys
import time
import traceback
from collections import OrderedDict

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL0_DIR = os.path.join(os.path.dirname(HERE), "cl0")
if CL0_DIR not in sys.path:
    sys.path.insert(0, CL0_DIR)

ARENA_COLUMNS = ["engine", "seed", "L", "split", "clean", "fail_cause_auto", "t_detect_s", "t_lift_s", "t_success_s", "ms_step_p50", "ms_step_p95", "wall_s",
                 "target", "n_objects", "rep", "task_id"]


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def arena_hash() -> str:
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(HERE, "arena", "**", "*.py"), recursive=True) + glob.glob(os.path.join(HERE, "configs", "*"))):
        h.update(os.path.relpath(p, HERE).encode() + b"\0")
        with open(p, "rb") as f:
            h.update(f.read() + b"\0")
    return h.hexdigest()


def vram_used_mib() -> int:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5).stdout
        return int(out.split()[0])
    except Exception:
        return -1


def parse_speed(tok: str, w_mm: float, tau_s: float):
    """'L0.25' -> (0.25, 37.5); 'L0' -> (0.0, 0.0); 'v50' -> (L, 50.0)"""
    if tok.startswith("L"):
        L = float(tok[1:])
        return L, L * w_mm / tau_s
    if tok.startswith("v"):
        v = float(tok[1:])
        return v * tau_s / w_mm, v
    raise ValueError(f"speed {tok!r}: use L<x> or v<mm/s>")


class GTTap:
    """Ground truth at the instant each frame was CAPTURED, for PRIVILEGED methods only (ORACLE).  Holds the last frames' snapshots keyed by image identity."""

    def __init__(self, world, keep: int = 24):
        self._world, self._keep = world, keep
        self._snaps: "OrderedDict[int, tuple]" = OrderedDict()
        self.belt_top_mm = world.belt_top_mm

    def on_capture(self, t: float, img) -> None:
        self._snaps[id(img)] = (img, self._world.gt_objects())        # keep img alive so its id stays unique
        while len(self._snaps) > self._keep:
            self._snaps.popitem(last=False)

    def objects_at_capture(self, img) -> dict:
        v = self._snaps.get(id(img))
        return v[1] if v is not None else {}

    def spec(self, name: str):
        return self._world.spec_by_name[name]


def build_methods(spec_names, cfg, kin, calib, calib_path, bg_path, tap, extra=None):
    """Instantiate methods; ONLY privileged specs (ORACLE) receive the ground-truth tap, every other method gets gt=None (GT leak rule)."""
    from .methods import MethodContext, check_contract, resolve
    from .trial import TimedMethod
    methods = OrderedDict()
    for spec_s in spec_names:
        spec = resolve(spec_s.strip())
        ctx = MethodContext(copy.deepcopy(cfg), kin, calib, calib_path, bg_path, (cfg.camera.width, cfg.camera.height), cfg.executor.control_hz,
                            gt=tap if spec.privileged else None, extra=dict(extra or {}))
        m = spec.factory(ctx)
        miss = check_contract(m)
        if miss:
            raise SystemExit(f"method {spec.name} does not implement the contract: missing {miss}")
        methods[getattr(m, "method_name", spec.name)] = (TimedMethod(m), spec)      # REMOTE methods announce their own name
    return methods


def write_log_csv(path: str, log: list) -> None:
    if not log:
        open(path, "w").close()
        return
    keys = []
    for r in log:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for r in log:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, tuple, dict)) else v) for k, v in r.items()})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--methods", required=True, help="comma list: CL0,NOOP,ORACLE or module.path:factory")
    ap.add_argument("--cells", required=True, help="comma list of arrangement sheets in --arrangements-dir (dev_C0 ...)")
    ap.add_argument("--speeds", default="L0", help="comma list: L0, L0.25, v50 ...")
    ap.add_argument("--n", type=int, default=10, help="arrangements per cell (first N of the sheet, after --first)")
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--reps", type=int, default=1, help="repetitions of every (arrangement, speed, method)")
    ap.add_argument("--seed", type=int, default=0, help="recorded; the sheets are fixed files, the simulation has no random draws")
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=os.path.join(HERE, "configs", "arena.toml"))
    ap.add_argument("--calib-dir", default=os.path.join(HERE, "runs", "calib"))
    ap.add_argument("--scene-file", default="", help="another scene TOML (with its own --calib-dir), default configs/scene.toml")
    ap.add_argument("--objects", default="interim", choices=["interim", "sim", "tasks"],
                    help="interim = 6 E2 primitives; sim = the E5 generated set (configs/objects_sim.json); tasks = E5 set + towers (configs/objects_tasks.json, E18)")
    ap.add_argument("--tasks", action="store_true", help="E18: --cells are task sheets <cell>.json (arena/tasks.py); the method gets set_task(); labels by arena/task_labeler.py")
    ap.add_argument("--arrangements-dir", default="", help="default: arrangements/ (interim) or arrangements/sim/ (sim)")
    ap.add_argument("--tau", type=float, default=0.4, help="tau_s in L = v tau / w [assumption 0.4 s, E1 report]")
    ap.add_argument("--video", action="store_true"); ap.add_argument("--debug-video", action="store_true")
    ap.add_argument("--depth", action="store_true", help="also give methods frame.depth_mm (ideal depth)")
    ap.add_argument("--method-arg", action="append", default=[], help="key=value passed to every method in ctx.extra")
    ap.add_argument("--t-limit", type=float, default=None, help="virtual seconds per trial (default executor.hard_timeout_s + 10)")
    ap.add_argument("--report", action="store_true", help="write metrics_report.md at the end (arena.report)")
    ap.add_argument("--shuffle-seed", type=int, default=None, help="run the plan in a shuffled order (M8: does a trial depend on the trials before it?)")
    ap.add_argument("--allow-locked", action="store_true", help="REQUIRED to run test_* cells (locked/): only on the user's explicit order (arena/CLAUDE.md rule 5)")
    ap.add_argument("--no-hard-reset", action="store_true", help="do NOT rebuild the PhysX scene before every trial (default: rebuild; M8 runs/e3_repeat: with it 40/40 trials "
                                                                   "give the same result in any order, without it 38/40; it costs no measurable time)")
    ap.add_argument("--frame-hashes", action="store_true", help="diagnosis: store an md5 of every captured camera image in trial_XXXX.json (repeatability of rendering)")
    ap.add_argument("--scene-set", action="append", default=[], help="override a scene.toml key for this run: section.key=value (recorded in manifest.json)")
    ap.add_argument("--record-demos", default="", help="E6: directory for raw demo episodes (arena/demos.py); convert with arena/to_lerobot.py")
    ap.add_argument("--demo-size", default="640x360"); ap.add_argument("--demo-all", action="store_true", help="also keep failed episodes (default: successes only)")
    a = ap.parse_args(argv)
    if any(c.strip().startswith("test") for c in a.cells.split(",")) and not a.allow_locked:
        raise SystemExit("test_* cells are LOCKED: they run only on the user's explicit order (arena/CLAUDE.md rule 5); add --allow-locked when that order exists")
    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    os.makedirs(out, exist_ok=True)

    from isaacsim import SimulationApp
    app = SimulationApp({"headless": True, "width": 1280, "height": 720})
    from cl0.arrangements import read_arrangements
    from cl0.config import load_config
    from cl0.geometry import PlaneCalib
    from cl0.kinematics import SO101Kinematics
    from cl0.run_g0 import CSV_COLUMNS
    from cl0.system import code_sha256
    from . import scene as S
    from .arrangements import to_placements
    from .labeler import label
    from .objects import INTERIM_SPECS
    from .platform import IsaacPlatform
    from .trial import run_trial
    from .world import IsaacWorld, SimFault

    cfg = load_config(a.config)
    calib_path, bg_path = os.path.join(a.calib_dir, "calib.json"), os.path.join(a.calib_dir, "background.npz")
    calib = PlaneCalib.load(calib_path)
    if cfg.belt.mm_per_step <= 0:
        cfg.belt.mm_per_step = calib.mm_per_step              # what build_stack does: the platform's belt readout uses the calibrated mm/pulse
    sc = S.load_scene_cfg(a.scene_file or None)
    for kv in a.scene_set:
        k, val = kv.split("=", 1); sec, key = k.split(".")
        sc.setdefault(sec, {})
        old_v = sc[sec].get(key)
        sc[sec][key] = val if isinstance(old_v, str) else (int(float(val)) if key.endswith("iters") else float(val))
    if a.objects == "sim":
        from .objects_gen import load_catalog
        pool = load_catalog()
    elif a.objects == "tasks":
        from .tasks import load_task_catalog
        pool = load_task_catalog()
    else:
        pool = INTERIM_SPECS
    if a.tasks and a.objects != "tasks":
        raise SystemExit("--tasks needs --objects tasks")
    if not a.arrangements_dir:
        a.arrangements_dir = os.path.join(HERE, {"sim": "arrangements/sim", "tasks": "arrangements/tasks"}.get(a.objects, "arrangements"))
    world = IsaacWorld(app, pool, sc, debug_cam=a.debug_video, depth=a.depth)
    plat = IsaacPlatform(world, cfg)
    tap = GTTap(world)
    plat.frame_hooks.append(tap.on_capture)
    kin = SO101Kinematics(urdf=cfg.robot.urdf or None, tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
    extra = dict(kv.split("=", 1) for kv in a.method_arg)
    methods = build_methods(a.methods.split(","), cfg, kin, calib, calib_path, bg_path, tap, extra)
    speeds = [(tok, *parse_speed(tok, cfg.perception.grasp.gripper_w_mm, a.tau)) for tok in a.speeds.split(",")]
    sheet_ext = ".json" if a.tasks else ".csv"
    if a.tasks:
        from .tasks import read_sheet, task_list
        from .task_labeler import label_task
        TASKS = task_list()
        sheets = {c: read_sheet(os.path.join(a.arrangements_dir, f"{c}.json")) for c in a.cells.split(",")}
        if a.t_limit is None:
            a.t_limit = 25.0                                  # virtual s per task trial (the expert needs <= 16 s; ACT stops itself at ACT_T_S)
    else:
        sheets = {c: read_arrangements(os.path.join(a.arrangements_dir, f"{c}.csv")) for c in a.cells.split(",")}
    specs = world.spec_by_name
    belt_end = sc["belt"]["center_a_mm"] + sc["belt"]["length_mm"] / 2.0

    manifest = {"engine": "isaac", "isaacsim": md.version("isaacsim"), "date": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "argv": sys.argv if argv is None else argv, "arena_sha256": arena_hash(), "cl0_code_sha256": code_sha256(),
                "arena_toml_sha256": sha256_file(a.config), "scene_toml_sha256": sha256_file(a.scene_file or os.path.join(HERE, "configs", "scene.toml")), "scene_file": a.scene_file or "configs/scene.toml",
                "usd_sha256": sha256_file(os.path.join(HERE, sc["robot"]["usd"])), "calib_sha256": sha256_file(calib_path), "background_sha256": sha256_file(bg_path),
                "sheets_sha256": {c: sha256_file(os.path.join(a.arrangements_dir, f"{c}{sheet_ext}")) for c in sheets},
                "gpu": subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip(),
                "methods": {n: {"spec": s.name, "privileged": s.privileged, "uses_pixels": s.uses_pixels, "doc": s.doc} for n, (_, s) in methods.items()},
                "speeds": [{"token": t, "L": L, "mm_s": v} for t, L, v in speeds], "tau_s": a.tau, "w_mm": cfg.perception.grasp.gripper_w_mm,
                "objects": ("E5 generated set configs/objects_sim.json sha256 " + sha256_file(os.path.join(HERE, "configs", "objects_sim.json"))[:12]) if a.objects == "sim"
                           else ("E18 task catalog configs/objects_tasks.json sha256 " + sha256_file(os.path.join(HERE, "configs", "objects_tasks.json"))[:12]) if a.objects == "tasks"
                           else "INTERIM primitives (arena/arena/objects.py), not the E5 object set", "depth": a.depth, "tasks": a.tasks,
                "scene_overrides": a.scene_set, "hard_reset": not a.no_hard_reset, "shuffle_seed": a.shuffle_seed,
                "manual": {"demos": None, "train_steps": None, "gpu_hours": None, "tuning_hours": None}}
    mpath = os.path.join(out, "manifest.json")
    if os.path.exists(mpath):
        old = json.load(open(mpath))
        manifest["previous_runs"] = old.get("previous_runs", []) + [{k: old.get(k) for k in ("date", "argv", "arena_sha256")}]
    json.dump(manifest, open(mpath, "w"), indent=1)

    csv_path = os.path.join(out, "trials.csv")
    cols = CSV_COLUMNS + ARENA_COLUMNS
    done, next_id = set(), 0
    if os.path.exists(csv_path):
        for r in csv.DictReader(open(csv_path)):
            next_id = max(next_id, int(r["trial_id"]) + 1)
            if r["valid"] == "1":
                done.add((r["method"], r["cell"], r["arrangement_id"], r["speed_mm_s"], r["rep"]))
    f = open(csv_path, "a", newline="")
    wr = csv.DictWriter(f, cols, extrasaction="ignore")
    if next_id == 0:
        wr.writeheader(); f.flush()
    plan = []
    for cell, sheet in sheets.items():
        ids = list(sheet)[a.first:a.first + a.n]
        for aid in ids:
            for tok, L, v in speeds:
                for rep in range(a.reps):
                    for mname in methods:
                        plan.append((cell, aid, tok, L, v, rep, mname))
    todo = [p for p in plan if (p[6], p[0], p[1], f"{p[4]:.1f}", str(p[5])) not in done]
    if a.shuffle_seed is not None:
        import random
        random.Random(a.shuffle_seed).shuffle(todo)
    print(f"run_arena: {len(plan)} trials planned, {len(plan) - len(todo)} already done, {len(todo)} to run -> {out}", flush=True)
    vram_peak, faults, t_run0 = vram_used_mib(), 0, time.perf_counter()
    for n_i, (cell, aid, tok, L, v, rep, mname) in enumerate(todo):
        tid = next_id + n_i
        m, spec = methods[mname]
        arr = sheets[cell][aid]
        task = None
        if a.tasks:
            if v > 0:
                raise SystemExit("E18 task sheets are for the stopped belt (L0) only")
            task = TASKS[arr["task_id"]]
            pl = [dict(p) for p in arr["placements"]]
            inner = getattr(m, "inner", m)
            if hasattr(inner, "set_task"):
                inner.set_task(task)
        else:
            pl = to_placements(arr, v, sc, specs)
        row = dict(trial_id=tid, method=mname, cell=cell, arrangement_id=aid, speed_mm_s=f"{v:.1f}", engine="isaac", seed=a.seed, L=f"{L:g}",
                   split=cell.split("_")[0], session=os.path.basename(out), config_sha=manifest["arena_toml_sha256"][:12], code_sha=manifest["cl0_code_sha256"][:12],
                   operator="arena", time_iso=dt.datetime.now().astimezone().isoformat(timespec="seconds"), n_objects=len(pl), rep=rep, picked_hint="",
                   task_id=task["id"] if task else "")
        vid = os.path.join(out, "videos", f"trial_{tid:04d}.mp4") if a.video else None
        dvid = os.path.join(out, "videos", f"debug_trial_{tid:04d}.mp4") if a.debug_video else None
        plat.render_enabled = spec.uses_pixels or bool(vid or dvid or a.record_demos)
        hashes = []
        taps_extra = []
        if a.frame_hashes:
            import hashlib as _hl
            taps_extra.append(lambda t, img: hashes.append(_hl.md5(np.ascontiguousarray(img).tobytes()).hexdigest()[:12]))
        rec = None
        if a.record_demos:
            from .demos import DemoRecorder
            rec = DemoRecorder(plat, m, tuple(int(x) for x in a.demo_size.split("x")))
        try:
            r = run_trial(plat, m, cfg, pl, v, vid, dvid, a.t_limit, extra_taps=([rec] if rec else []) + taps_extra, hard_reset=not a.no_hard_reset)
            if a.frame_hashes:
                r["frame_md5"] = hashes
            if task is not None:
                lab = label_task(r["gt_array"], r["gt_columns"], pl, task, specs, world.belt_top_mm, cfg.perception.grasp.gripper_w_mm, sc["belt"]["dir_deg"])
            else:
                lab = label(r["gt_array"], r["gt_columns"], r["events"], r["phases"], r["outcome"], r["diag"], pl, v, specs, world.belt_top_mm, belt_end,
                            cfg.perception.grasp.gripper_w_mm, sc["belt"]["dir_deg"])
            row.update(success=lab["success"], valid=1, fail_cause=lab["fail_cause_auto"], fail_cause_auto=lab["fail_cause_auto"], clean=lab["clean"],
                       outcome=r["outcome"], t_end_s=f"{r['t_end_s']:.2f}", t_detect_s=lab["t_detect_s"], t_lift_s=lab["t_lift_s"], t_success_s=lab["t_success_s"],
                       ms_step_p50=f"{r['ms_step_p50']:.2f}", ms_step_p95=f"{r['ms_step_p95']:.2f}", wall_s=r["wall_s"], target=lab["target"],
                       video=os.path.relpath(vid, out) if vid else "", note="")
            np.savez_compressed(os.path.join(out, f"trial_{tid:04d}_gt.npz"), gt=r.pop("gt_array"), columns=np.array(r["gt_columns"]))
            write_log_csv(os.path.join(out, f"trial_{tid:04d}_log.csv"), r.pop("log"))
            json.dump({"trial_id": tid, "method": mname, "cell": cell, "arrangement_id": aid, "speed_mm_s": v, "L": L, "rep": rep, "placements": pl, "task": task,
                       "label": lab, **r}, open(os.path.join(out, f"trial_{tid:04d}.json"), "w"), indent=1, default=float)
            if rec is not None and (lab["success"] or a.demo_all):
                rd = a.record_demos if os.path.isabs(a.record_demos) else os.path.join(HERE, a.record_demos)
                n_fr = rec.save(os.path.join(rd, f"episode_{tid:04d}.npz"), {"trial_id": tid, "method": mname, "cell": cell, "arrangement_id": aid, "L": L,
                                "speed_mm_s": v, "success": lab["success"], "objects": [p["name"] for p in pl], "engine": "isaac", "fps": cfg.camera.fps,
                                "task": task["text"] if task else ("pick the object from the moving belt and hold it" if v > 0 else "pick the object from the belt and hold it"),
                                "task_id": task["id"] if task else "", "task_vec": task["vec"] if task else None})
                row["note"] = f"demo {n_fr} frames"
            faults = 0
        except SimFault as e:
            faults += 1
            row.update(success=0, valid=0, fail_cause="", outcome="", note=f"SimFault: {str(e)[:150]}")
            print("SIMFAULT", e, flush=True)
        except Exception:
            traceback.print_exc()
            f.close(); app.close()
            return 2                                   # a bug of the arena: stop loudly, never record it as a method result
        wr.writerow(row); f.flush()
        vram_peak = max(vram_peak, vram_used_mib())
        el = time.perf_counter() - t_run0
        print(f"[{n_i + 1}/{len(todo)}] #{tid:04d} {mname:8s} {cell} {aid} {tok:6s} -> success={row['success']} valid={row['valid']} outcome={row.get('outcome')} "
              f"cause={row.get('fail_cause')} wall={row.get('wall_s')}s  (eta {el / (n_i + 1) * (len(todo) - n_i - 1) / 60:.0f} min)", flush=True)
        if faults >= 3:
            print("3 consecutive SimFaults: stopping (arena/CLAUDE.md rule 7)", flush=True)
            break
    f.close()
    manifest["vram_peak_mib_seen"] = vram_peak
    manifest["render_wall_s_per_frame"] = plat.stats["render_wall_s"] / max(plat.stats["renders"], 1)
    json.dump(manifest, open(mpath, "w"), indent=1)
    for m, _ in methods.values():
        if hasattr(m, "close"):
            m.close()
    if a.report:                                       # before app.close(): closing the Kit app may end the process
        from .report import main as report_main
        report_main([csv_path, "--out", os.path.join(out, "metrics_report.md")])
    app.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
