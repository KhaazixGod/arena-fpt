"""E5: are C3 arrangements (objects touching) stable?  Place each arrangement on the STOPPED belt (as run_arena does for L0), step 1 s, measure every object's
drift; an arrangement passes if no object moves > 2 mm [de xuat] (and none tips: z change > 2 mm).  Train/dev sheets only: test sheets are locked.  No render.
    ~/env_isaac/bin/python arena/scripts/e5_c3_stability.py --out arena/runs/e5 --cells train_C3,dev_C3
"""
import argparse, json, os, sys
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--cells", default="train_C3,dev_C3"); ap.add_argument("--tol", type=float, default=2.0)
args = ap.parse_args()
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
os.makedirs(args.out, exist_ok=True)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 320, "height": 240})
from arena import scene as S
from arena.arrangements import to_placements
from arena.objects_gen import load_catalog
from arena.world import IsaacWorld
from cl0.arrangements import read_arrangements
from cl0.config import load_config
sc = S.load_scene_cfg(); cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
specs = load_catalog(); by = {s.name: s for s in specs}
w = IsaacWorld(app, specs, sc)
report = {}
for cell in args.cells.split(","):
    assert not cell.startswith("test"), "test sheets are locked"
    sheet = read_arrangements(os.path.join(HERE, "arrangements", "sim", f"{cell}.csv"))
    rows = []
    for aid, arr in sheet.items():
        pl = to_placements(arr, 0.0, sc, by)
        w.set_belt_speed(0.0); w.park_all(); w.teleport_arm(cfg.robot.home_q_deg, cfg.robot.gripper_open); w.step_seconds(0.3)
        w.place(pl); w.step()
        g0 = w.gt_objects(); w.step_seconds(1.0); g1 = w.gt_objects()
        drift = {p["name"]: float(np.linalg.norm(np.asarray(g1[p["name"]]["pos_mm"][:2]) - np.asarray(g0[p["name"]]["pos_mm"][:2]))) for p in pl}
        dz = {p["name"]: float(abs(g1[p["name"]]["pos_mm"][2] - g0[p["name"]]["pos_mm"][2])) for p in pl}
        ok = all(v <= args.tol for v in drift.values()) and all(v <= args.tol for v in dz.values()) and w.finite()
        rows.append({"arrangement_id": aid, "ok": ok, "max_drift_mm": round(max(drift.values()), 2), "max_dz_mm": round(max(dz.values()), 2), "n": len(pl)})
    n_ok = sum(r["ok"] for r in rows)
    report[cell] = {"n": len(rows), "ok": n_ok, "rate": n_ok / len(rows), "worst": sorted(rows, key=lambda r: -r["max_drift_mm"])[:5]}
    print(cell, f"{n_ok}/{len(rows)} stable (drift <= {args.tol} mm in 1 s)", "worst:", report[cell]["worst"][:3], flush=True)
json.dump({"engine": "isaac", "tol_mm": args.tol, "cells": report}, open(os.path.join(args.out, "c3_stability.json"), "w"), indent=1)
app.close()
