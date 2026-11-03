"""Arrangement sheets for the arena: generated with dir1/make_arrangements.py's own ``place()`` and ``LEVELS`` (the tool that will generate the real G0 sheets),
restricted to the object band the user approved (scene.toml belt.object_band_x_mm, x = 130..230 mm on the 200 mm belt).

Sheet format = cl0.arrangements: arrangement_id,first_method,idx,object,x_mm,y_mm,yaw_deg  (x along the belt relative to object 1, y from the LEFT edge, yaw deg).
Here the "belt" handed to place() is the band widened by the tool's 10 mm margin on each side, so every object's enclosing circle lies inside the band.
    python -m arena.arrangements --cell dev_C2 --n 60 --seed 2 [--objects configs/objects_interim.csv] [--out arrangements/dev_C2.csv]
TEST sheets go to locked/ and are not run without the user's order (arena/CLAUDE.md rule 5).
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import random
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dir1"))
from make_arrangements import LEVELS, place  # noqa: E402

MARGIN_MM = 10.0                    # make_arrangements.place() default margin
A_DOWNSTREAM_START_MM = -150.0      # moving belt: the most downstream object starts here (just upstream of CL-0's pick segment, inside the camera window)
A_BELT_START_PAD_MM = 5.0


def band_geometry(scene_cfg: dict):
    """(virtual belt width for place(), b of its LEFT edge) for the approved band."""
    b = scene_cfg["belt"]
    lo, hi = b["object_band_x_mm"]
    if abs(b["dir_deg"] - 90.0) > 1e-6:
        raise NotImplementedError("band mapping written for belt dir 90 deg (x = -b)")
    return (hi - lo) + 2 * MARGIN_MM, -(lo - MARGIN_MM)          # left of travel (+v = -x) is the SMALL-x side


def read_objects(path: str, split: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    return [dict(name=r["name"].strip(), d=float(r["diameter_mm"])) for r in csv.DictReader(lines) if r["split"].strip() == split]


def generate(cell: str, n: int, seed: int, objects_csv: str, scene_cfg: dict) -> List[dict]:
    split, level = cell.split("_", 1)
    pool = read_objects(objects_csv, split)
    (nlo, nhi), gap_rng, min_pair = LEVELS[level]
    width, _ = band_geometry(scene_cfg)
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        for _ in range(500):
            k = rng.randint(nlo, min(nhi, len(pool)))
            objs = rng.sample(pool, k)
            pts = place(rng, objs, gap_rng, min_pair, width, MARGIN_MM)
            if pts is not None:
                break
        else:
            raise SystemExit(f"cannot place {cell} in a {width:.0f} mm band")
        first = rng.choice("AB")
        for j, (o, (x, y, r)) in enumerate(zip(objs, pts), start=1):
            rows.append(dict(arrangement_id=f"{cell}_{i:03d}", first_method=first, idx=j, object=o["name"], x_mm=round(x, 1), y_mm=round(y, 1),
                             yaw_deg=round(rng.uniform(0, 360), 1)))
    return rows


def to_placements(arr, speed_mm_s: float, scene_cfg: dict, specs: Dict[str, object]) -> List[dict]:
    """cl0.arrangements.Arrangement -> [{"name", "a_mm", "b_mm", "yaw_deg"}] in the belt frame of the scene.
    Static belt: the arrangement is centred at belt.static_center_a_mm (inside the pick segment and the camera view).  Moving belt: the most downstream object starts at
    A_DOWNSTREAM_START_MM, shifted downstream if needed so that every object is on the belt."""
    _, b_left = band_geometry(scene_cfg)
    bc = scene_cfg["belt"]
    belt_start = bc["center_a_mm"] - bc["length_mm"] / 2.0
    xs = [it.x_mm for it in arr.items]
    rs = [specs[it.obj].footprint_radius_mm for it in arr.items]
    if speed_mm_s > 0:
        c = A_DOWNSTREAM_START_MM - max(xs)
        lo = min(x - r for x, r in zip(xs, rs)) + c
        if lo < belt_start + A_BELT_START_PAD_MM:
            c += belt_start + A_BELT_START_PAD_MM - lo
    else:
        c = float(bc.get("static_center_a_mm", 0.0)) - 0.5 * (min(xs) + max(xs))
    return [{"name": it.obj, "a_mm": it.x_mm + c, "b_mm": b_left - it.y_mm, "yaw_deg": it.yaw_deg} for it in arr.items]


def main(argv=None):
    from .scene import load_scene_cfg
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cell", required=True, help="dev_C0 .. dev_C3 (split_level)")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--objects", default=os.path.join(HERE, "configs", "objects_interim.csv"))
    ap.add_argument("--out", default="")
    ap.add_argument("--set", default="interim", choices=["interim", "sim"], help="sim: objects_sim.csv, sheets in arrangements/sim (train/dev) or locked/ (test)")
    a = ap.parse_args(argv)
    sc = load_scene_cfg()
    if a.set == "sim":
        if a.objects.endswith("objects_interim.csv"):
            a.objects = os.path.join(HERE, "configs", "objects_sim.csv")
        default_dir = os.path.join(HERE, "locked") if a.cell.startswith("test") else os.path.join(HERE, "arrangements", "sim")
    else:
        if a.cell.startswith("test"):
            raise SystemExit("the interim set has no TEST split")
        default_dir = os.path.join(HERE, "arrangements")
    rows = generate(a.cell, a.n, a.seed, a.objects, sc)
    out = a.out or os.path.join(default_dir, f"{a.cell}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    width, b_left = band_geometry(sc)
    with open(out, "w", newline="", encoding="utf-8") as f:
        f.write(f"# arena arrangement sheet {a.cell}: n={a.n} seed={a.seed} objects={os.path.relpath(a.objects, HERE)}; generated by dir1/make_arrangements.place() "
                f"on a {width:.0f} mm virtual belt = band x {sc['belt']['object_band_x_mm']} + {MARGIN_MM:.0f} mm margins (y from its left edge, b = {b_left:.0f} - y)\n")
        w = csv.DictWriter(f, fieldnames=["arrangement_id", "first_method", "idx", "object", "x_mm", "y_mm", "yaw_deg"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {a.n} arrangements, {len(rows)} objects")


if __name__ == "__main__":
    main()
