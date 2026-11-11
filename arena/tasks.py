"""E18 (KE_HOACH_TASKS.md): 40 manipulation tasks on the STOPPED belt for one multi-task ACT, their task code, the object catalog and the scene sheets.

Families (all with the vertical gripper of interface I2, tilt 90 deg):
    pick    pick the object of category C (a distractor of another category is on the belt) and hold it      success: label M1 on the TARGET only
    place   pick C and put it down in zone A (downstream) or B (upstream)                                   success: resting upright in the zone, released
    pull    drag C (without lifting) 50 mm toward the robot or downstream                                    success: moved >= 35 mm along it, released
    topple  push C over near its top, in one of 4 directions                                                  success: its vertical axis tilts >= 60 deg
Task code (12 floats, given to the policy as observation.environment_state): family one-hot (4) + category one-hot (6) + param (2) = a direction or zone
offset in the BELT frame (a along travel, b = across), each in {-1, 0, +1}.

    python -m arena.tasks catalog                       # configs/objects_tasks.json (+ .csv): the E5 set + 6 tall "tower" objects for topple
    python -m arena.tasks sheets                        # arrangements/tasks/{pilot_T,train_T}.json, locked/tasks/{test_Tseen,test_Theld}.json
    python -m arena.tasks list                          # the 40 tasks, TRAIN / HELD-OUT
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from collections import OrderedDict
from dataclasses import asdict
from typing import Dict, List

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(HERE, "configs", "objects_tasks.json")

FAMILIES = ["pick", "place", "pull", "topple"]
CATEGORIES = ["box", "cyl", "L", "T", "mug", "ring"]
# belt frame: a = along travel (+ = downstream), b = across (b = -x here: + = toward the robot)
PARAMS = {"A": (1, 0), "B": (-1, 0),                                  # place zones
          "robot": (0, 1), "down": (1, 0), "up": (-1, 0),             # pull directions
          "+a": (1, 0), "-a": (-1, 0), "+b": (0, 1), "-b": (0, -1)}  # topple directions (+b = toward the robot, -b = away)
WORDS = {"A": "zone A", "B": "zone B", "robot": "toward the robot", "down": "downstream", "up": "upstream", "+a": "downstream", "-a": "upstream", "+b": "toward the robot",
         "-b": "away from the robot"}

# geometry of the stopped-belt workspace (belt frame of configs/scene.toml: a = y, b = -x; reach checked with SO101Kinematics, KE_HOACH_TASKS.md §1)
A0, B0 = -40.0, -205.0                 # centre of the start area (belt.static_center_a_mm, middle of the object band x 155..255)
ZONE_DA = 65.0                         # zones A / B at a = A0 +- 65 (a = +25 / -105), b = B0
ZONE_R_MM = 25.0
PULL_MM = 50.0
TOWERS = [("box", 20.0, 20.0, 50.0), ("box", 22.0, 18.0, 55.0), ("box", 24.0, 20.0, 46.0),
          ("cyl", 20.0, 0.0, 52.0), ("cyl", 23.0, 0.0, 47.0), ("cyl", 18.0, 0.0, 55.0)]   # (shape, x or diameter, y, height) mm; tall enough to tip easily
TOPPLE_MIN_RATIO = 1.6                 # height / grasp width of box / cyl objects that may be toppled (smoke 11/11: box01 at 1.39 slid instead)


def task_list() -> "OrderedDict[str, dict]":
    out = OrderedDict()
    for c in CATEGORIES:
        out[f"pick:{c}"] = dict(family="pick", cat=c, param="", text=f"pick up the {c} and hold it")
    for c in CATEGORIES:
        for z in ("A", "B"):
            out[f"place:{c}:{z}"] = dict(family="place", cat=c, param=z, text=f"put the {c} in {WORDS[z]}")
    # expert gate 11/11 (logs/*_e18_gate.txt, pilot_T): pull:mug:down 1/5, topple:box:-b 3/5, topple:cyl:-b 2/5, topple:mug:+a 2/5 failed (>= 4/5 needed)
    # -> replaced, BEFORE any demo or training, by pull:{box,cyl,L,T}:up (gated on pilot_T2: pull:L:up 0/5 -> replaced by pull:ring:up, pilot_T3)
    # see PREREGISTRATION_E18.md section 8
    for c in CATEGORIES:
        for d in ("robot", "down", "up"):
            if (c == "mug" and d == "down") or (d == "up" and c not in ("box", "cyl", "T", "ring")):
                continue
            out[f"pull:{c}:{d}"] = dict(family="pull", cat=c, param=d, text=f"drag the {c} {WORDS[d]} without lifting it")
    for c in ("box", "cyl"):
        for d in ("+a", "-a", "+b"):
            out[f"topple:{c}:{d}"] = dict(family="topple", cat=c, param=d, text=f"knock the {c} over {WORDS[d]}")
    out["topple:mug:+b"] = dict(family="topple", cat="mug", param="+b", text=f"knock the mug over {WORDS['+b']}")
    for tid, t in out.items():
        t["id"] = tid
        t["vec"] = task_vec(t)
    assert len(out) == 40, len(out)
    return out


# compositional hold-out: every family, category and parameter of these appears in some TRAIN task (checked in check_split)
HELD_OUT = ["pick:mug", "place:L:A", "place:cyl:B", "pull:ring:robot", "pull:T:down", "pull:cyl:up", "pull:ring:up", "topple:box:-a"]
DROPPED = ["pull:mug:down", "topple:box:-b", "topple:cyl:-b", "topple:mug:+a", "pull:L:up"]   # failed the expert gate (11/11), never in demos or TEST


def task_vec(t: dict) -> List[float]:
    v = [0.0] * (len(FAMILIES) + len(CATEGORIES) + 2)
    v[FAMILIES.index(t["family"])] = 1.0
    v[len(FAMILIES) + CATEGORIES.index(t["cat"])] = 1.0
    if t["param"]:
        pa, pb = PARAMS[t["param"]]
        v[-2], v[-1] = float(pa), float(pb)
    return v


def split_of(tid: str) -> str:
    return "heldout" if tid in HELD_OUT else "train"


def check_split(tasks=None) -> None:
    tasks = tasks or task_list()
    tr = [t for k, t in tasks.items() if k not in HELD_OUT]
    for k in HELD_OUT:
        t = tasks[k]
        assert any(x["family"] == t["family"] and x["cat"] == t["cat"] for x in tr) or t["family"] == "pick", k
        assert any(x["cat"] == t["cat"] for x in tr), k
        assert any(x["family"] == t["family"] and x["param"] == t["param"] for x in tr), k


# ---------------------------------------------------------------------------------------------------------------- catalog
def build_catalog(seed: int = 18) -> list:
    """The E5 objects (unchanged, from configs/objects_sim.json) + 6 towers (split 'train', category box / cyl)."""
    from .objects import ObjSpec, Part
    from .objects_gen import DENSITY_G_CM3, PALETTE, _centre, _mass, load_catalog
    base = load_catalog()
    r = random.Random(seed)
    out = list(base)
    for i, (shape, x, y, h) in enumerate(TOWERS):
        name = f"tw{shape}{37 + i}"
        if shape == "box":
            parts, grasp = [Part("box", (x, y, h))], (0.0, 0.0, 90.0, min(x, y))
        else:
            parts, grasp = [Part("cyl", (x, h))], (0.0, 0.0, 90.0, x)
        parts, grasp = _centre(parts, grasp)
        out.append(ObjSpec(name, "compound", (), r.choice(PALETTE), round(_mass(parts), 1), 0.8, tuple(parts), tuple(round(g, 2) for g in grasp), shape, "", "train"))
    return out


def write_catalog(path: str = CATALOG) -> None:
    from .objects_gen import DENSITY_G_CM3, to_json
    specs = build_catalog()
    with open(path, "w") as f:
        json.dump({"note": "E18 task catalog = configs/objects_sim.json objects + 6 towers (arena/tasks.py); do not edit by hand",
                   "density_g_cm3": DENSITY_G_CM3, "objects": to_json(specs)}, f, indent=1)
    with open(path.replace(".json", ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "diameter_mm", "split", "category", "height_mm", "grasp_width_mm", "mass_g", "topple_ok"])
        for s in specs:
            w.writerow([s.name, round(2 * s.footprint_radius_mm, 1), s.split, s.category, round(s.height_mm, 1), round(s.min_width_mm, 1), s.mass_g,
                        int(topple_ok(s))])
    print(f"wrote {path}: {len(specs)} objects")


def load_task_catalog(path: str = CATALOG):
    from .objects_gen import load_catalog
    return load_catalog(path)


def topple_ok(s) -> bool:
    if s.category == "mug":
        return True
    return s.category in ("box", "cyl") and s.height_mm >= TOPPLE_MIN_RATIO * s.grasp[3] and s.height_mm >= 30.0


# ---------------------------------------------------------------------------------------------------------------- scene sheets
def _pool(specs, t: dict) -> list:
    """Target candidates: TRAIN-split objects of the task's category (+ topple_ok for topple).  Towers only serve topple / pick / pull (too tall to carry over)."""
    ok = [s for s in specs if s.split == "train" and s.category == t["cat"]]
    if t["family"] == "topple":
        ok = [s for s in ok if topple_ok(s)]
    elif t["family"] == "place":
        ok = [s for s in ok if not s.name.startswith("tw")]
    return ok


def _distractors(specs, t: dict) -> list:
    return [s for s in specs if s.split == "train" and s.category != t["cat"] and not s.name.startswith("tw") and s.height_mm <= 45.0]


def _target_start(t: dict, rng) -> tuple:
    j = lambda w: rng.uniform(-w, w)
    if t["family"] == "pull" and t["param"] == "robot":
        return A0 + j(15), B0 - 30.0 + j(8)                   # starts farther from the robot (x ~ 235) so it ends inside the band
    if t["family"] == "pull" and t["param"] == "down":
        return A0 - 20.0 + j(10), B0 + j(15)
    if t["family"] == "pull" and t["param"] == "up":
        return A0 + 20.0 + j(10), B0 + j(15)
    return A0 + j(15), B0 + j(12)


def _clear(t: dict, ta: float, tb: float) -> List[tuple]:
    """Belt-frame points (a, b, radius) that must stay free of the distractor: the target's path / landing area."""
    if t["family"] == "place":
        za = A0 + ZONE_DA * PARAMS[t["param"]][0]
        return [((ta + za) / 2, B0, abs(za - ta) / 2 + 30.0), (za, B0, ZONE_R_MM + 35.0)]
    if t["family"] in ("pull", "topple"):
        pa, pb = PARAMS[t["param"]]
        L = PULL_MM if t["family"] == "pull" else 60.0
        return [(ta + pa * L * k / 3, tb + pb * L * k / 3, 30.0) for k in range(4)] + [(ta - pa * 45.0, tb - pb * 45.0, 25.0)]   # path + where the pusher comes from
    return []


def make_items(tasks: List[str], n_per: int, seed: int, prefix: str, specs) -> list:
    T = task_list()
    rng = random.Random(seed)
    items = []
    lo_b, hi_b = -255.0, -155.0                                 # object band (centres + radius kept inside)
    for tid in tasks:
        t = T[tid]
        pool, dis = _pool(specs, t), _distractors(specs, t)
        if not pool:
            raise SystemExit(f"no target object for {tid}")
        for k in range(1, n_per + 1):
            for _ in range(2000):
                tg = rng.choice(pool)
                ta, tb = _target_start(t, rng)
                rt = tg.footprint_radius_mm
                if not (-248.0 <= tb <= -160.0):                # target centre within reach at grasp height (x 160..248); its footprint may leave the band
                    continue
                d = rng.choice(dis)
                rd = d.footprint_radius_mm
                da, db = ta + rng.uniform(-90, 90), rng.uniform(lo_b + rd, hi_b - rd)
                if math.hypot(da - ta, db - tb) < rt + rd + 15.0:
                    continue
                if any(math.hypot(da - ca, db - cb) < cr + rd for ca, cb, cr in _clear(t, ta, tb)):
                    continue
                if not (-115.0 <= da <= 45.0):
                    continue
                break
            else:
                raise SystemExit(f"cannot place a scene for {tid}")
            items.append({"arrangement_id": f"{prefix}_{tid.replace(':', '_').replace('+', 'p').replace('-', 'm')}_{k:02d}", "task_id": tid,
                          "placements": [{"name": tg.name, "a_mm": round(ta, 1), "b_mm": round(tb, 1), "yaw_deg": round(rng.uniform(0, 360), 1)},
                                         {"name": d.name, "a_mm": round(da, 1), "b_mm": round(db, 1), "yaw_deg": round(rng.uniform(0, 360), 1)}]})
    return items


def write_sheet(path: str, cell: str, seed: int, items: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"cell": cell, "seed": seed, "generated_by": "arena/tasks.py", "catalog": os.path.relpath(CATALOG, HERE), "items": items}, f, indent=1)
    print(f"wrote {path}: {len(items)} scenes")


SHEETS = {   # cell -> (dir, tasks, scenes per task, seed)
    "pilot_T": ("arrangements/tasks", "all", 5, 181),         # NOT rewritten: the gate ran on the first version (40 tasks incl. DROPPED); see write_sheets
    "pilot_T2": ("arrangements/tasks", ["pull:box:up", "pull:cyl:up", "pull:L:up", "pull:T:up"], 5, 185),   # gate of the 4 replacement tasks (kept as run)
    "pilot_T3": ("arrangements/tasks", ["pull:ring:up"], 5, 186),                                           # gate of the replacement of pull:L:up
    "train_T": ("arrangements/tasks", "train", 25, 182),
    "test_Tseen": ("locked/tasks", "train", 5, 183),
    "test_Theld": ("locked/tasks", "heldout", 10, 184),
}


def write_sheets() -> None:
    specs = load_task_catalog()
    T = task_list()
    for cell, (d, which, n, seed) in SHEETS.items():
        if cell.startswith("pilot_T") and os.path.exists(os.path.join(HERE, d, f"{cell}.json")):
            continue                                            # keep the scenes the gate ran on
        if isinstance(which, list):
            T = dict(T, **{k: dict(family=k.split(":")[0], cat=k.split(":")[1], param=k.split(":")[2], id=k) for k in which if k not in T})
            ids = which
        else:
            ids = [k for k in T if which == "all" or split_of(k) == which]
        write_sheet(os.path.join(HERE, d, f"{cell}.json"), cell, seed, make_items(ids, n, seed, cell, specs))


def read_sheet(path: str) -> "OrderedDict[str, dict]":
    d = json.load(open(path))
    return OrderedDict((it["arrangement_id"], it) for it in d["items"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["catalog", "sheets", "list"])
    a = ap.parse_args(argv)
    if a.what == "catalog":
        write_catalog()
    elif a.what == "sheets":
        check_split()
        write_sheets()
    else:
        check_split()
        for k, t in task_list().items():
            print(f"{split_of(k):8s} {k:20s} {t['vec']}  '{t['text']}'")


if __name__ == "__main__":
    main()
