"""E5: a procedurally generated, diverse object set for the arena (no download, no licence question): boxes, cylinders, L / T / U shapes, mugs with a
handle, hollow rings, thin plates, low-contrast objects.  Built from primitive colliders (arena.objects.Part), so concave shapes collide exactly.

    python -m arena.objects_gen --seed 5          # writes configs/objects_sim.json + configs/objects_sim.csv
Split (fixed by the seed, disjoint): train 20 / dev 6 / test 10.  TEST holds the three hard types of KE_HOACH_HUONG_1 §3.5:
concave/handle (U, ring, mug), thin/flat (plates), low contrast with the belt (dark grey), plus novel ordinary shapes.
Every object has a graspable width <= gripper_w - margin (56 mm) and a stored "good grasp" (centre, closing axis, width) that only ORACLE uses.
Masses from a density of 0.45 g/cm3 [assumption]; friction 0.8 [assumption].
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from dataclasses import asdict
from typing import List

from .objects import ObjSpec, Part

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENSITY_G_CM3 = 0.45
PALETTE = [(0.85, 0.12, 0.10), (0.10, 0.25, 0.85), (0.95, 0.85, 0.10), (0.12, 0.65, 0.20), (0.95, 0.50, 0.05), (0.92, 0.92, 0.92),
           (0.55, 0.20, 0.75), (0.10, 0.75, 0.80), (0.95, 0.45, 0.70), (0.75, 0.60, 0.40), (0.60, 0.90, 0.20), (0.15, 0.50, 0.50)]
MAX_GRASP_W = 50.0                    # below gripper_w - margin = 56 mm, with room for the pads


def _centre(parts: List[Part], grasp) -> tuple:
    """Shift parts (and the grasp point) so the object's bounding box is centred on the origin (and its bottom at -H/2)."""
    xs = [x for p in parts for x, _ in p.corners_xy()]; ys = [y for p in parts for _, y in p.corners_xy()]
    zlo = min(p.pos_mm[2] - p.half_h for p in parts); zhi = max(p.pos_mm[2] + p.half_h for p in parts)
    cx, cy, cz = 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (zlo + zhi)
    out = tuple(Part(p.shape, p.dims_mm, (p.pos_mm[0] - cx, p.pos_mm[1] - cy, p.pos_mm[2] - cz), p.yaw_deg) for p in parts)
    g = (grasp[0] - cx, grasp[1] - cy, grasp[2], grasp[3])
    return out, g


def _mass(parts) -> float:
    return max(6.0, min(80.0, DENSITY_G_CM3 * sum(p.volume_cm3() for p in parts)))


def make(cat: str, r: random.Random, color, name: str) -> ObjSpec:
    U = r.uniform
    if cat == "box":
        x = U(22, 55); y = U(18, min(x, MAX_GRASP_W)); h = U(12, 40)
        parts, grasp = [Part("box", (x, y, h))], (0.0, 0.0, 90.0, y)
    elif cat == "cyl":
        d = U(18, 48); h = U(12, 45)
        parts, grasp = [Part("cyl", (d, h))], (0.0, 0.0, 90.0, d)
    elif cat == "L":
        l1, l2, w, h = U(42, 60), U(30, 48), U(16, 24), U(15, 30)
        parts = [Part("box", (l1, w, h), (0.0, 0.0, 0.0)), Part("box", (w, l2 - w, h), (l1 / 2 - w / 2, w / 2 + (l2 - w) / 2, 0.0))]
        grasp = (-l1 / 2 + (l1 - w) / 2, 0.0, 90.0, w)
    elif cat == "T":
        l1, l2, w, h = U(40, 58), U(28, 45), U(16, 24), U(15, 30)
        parts = [Part("box", (l1, w, h), (0.0, 0.0, 0.0)), Part("box", (w, l2 - w, h), (0.0, w / 2 + (l2 - w) / 2, 0.0))]
        grasp = (0.0, w / 2 + (l2 - w) / 2, 0.0, w)
    elif cat == "U":
        l, l2, w, h = U(44, 60), U(30, 44), U(14, 20), U(15, 28)
        parts = [Part("box", (l, w, h), (0.0, 0.0, 0.0)), Part("box", (w, l2 - w, h), (-l / 2 + w / 2, w / 2 + (l2 - w) / 2, 0.0)),
                 Part("box", (w, l2 - w, h), (l / 2 - w / 2, w / 2 + (l2 - w) / 2, 0.0))]
        grasp = (0.0, 0.0, 90.0, w)
    elif cat == "mug":
        d, h = U(30, 42), U(30, 42)
        t, hl, hw = 5.0, 12.0, 0.6 * h
        r0 = d / 2
        parts = [Part("cyl", (d, h)), Part("box", (hl, t, hw), (r0 + hl / 2 - 2, 9.0, 0.0)), Part("box", (hl, t, hw), (r0 + hl / 2 - 2, -9.0, 0.0)),
                 Part("box", (t, 18.0 + t, hw), (r0 + hl - 2 - t / 2, 0.0, 0.0))]
        grasp = (0.0, 0.0, 90.0, d)                                 # close across the body, perpendicular to the handle
    elif cat == "ring":
        d, wall, h = U(36, MAX_GRASP_W), U(5, 7), U(14, 24)
        rm, n = d / 2 - wall / 2, 12
        seg = 2 * rm * math.tan(math.pi / n) + 1.0
        parts = [Part("box", (seg, wall, h), (rm * math.cos(2 * math.pi * k / n), rm * math.sin(2 * math.pi * k / n), 0.0), math.degrees(2 * math.pi * k / n) + 90.0)
                 for k in range(n)]
        grasp = (0.0, 0.0, 0.0, d)
    elif cat == "plate":
        x = U(40, 55); y = U(28, 46); h = U(4, 7)
        parts, grasp = [Part("box", (x, y, h))], (0.0, 0.0, 90.0, y)
    else:
        raise ValueError(cat)
    parts, grasp = _centre(parts, grasp)
    return ObjSpec(name, "compound", (), color, round(_mass(parts), 1), 0.8, parts, tuple(round(g, 2) for g in grasp), cat)


PLAN = {   # split -> list of (category, hard_type)
    "train": [("box", "")] * 6 + [("cyl", "")] * 6 + [("L", "")] * 3 + [("T", "")] * 2 + [("mug", "")] * 2 + [("ring", "")],
    "dev": [("box", ""), ("cyl", ""), ("L", ""), ("mug", ""), ("box", ""), ("cyl", "")],
    "test": [("U", "concave"), ("ring", "concave"), ("mug", "concave"), ("plate", "thin"), ("plate", "thin"), ("box", "lowcon"), ("cyl", "lowcon"),
             ("T", ""), ("box", ""), ("cyl", "")],
}


def generate(seed: int) -> List[ObjSpec]:
    r = random.Random(seed)
    out, n = [], 0
    for split, items in PLAN.items():
        for cat, hard in items:
            n += 1
            color = (lambda g: (g, g, g * 1.08))(r.uniform(0.16, 0.21)) if hard == "lowcon" else r.choice(PALETTE)
            sp = make(cat, r, color, f"{cat.lower()}{n:02d}")
            out.append(ObjSpec(sp.name, sp.shape, sp.dims_mm, tuple(round(c, 3) for c in sp.color), sp.mass_g, sp.mu, sp.parts, sp.grasp, cat, hard, split))
    return out


def to_json(specs: List[ObjSpec]) -> list:
    return [asdict(s) for s in specs]


def from_json(rows: list) -> List[ObjSpec]:
    out = []
    for d in rows:
        parts = tuple(Part(p["shape"], tuple(p["dims_mm"]), tuple(p["pos_mm"]), p["yaw_deg"]) for p in d.get("parts", []))
        out.append(ObjSpec(d["name"], d["shape"], tuple(d["dims_mm"]), tuple(d["color"]), d["mass_g"], d.get("mu", 0.8), parts, tuple(d.get("grasp", ())),
                           d.get("category", ""), d.get("hard_type", ""), d.get("split", "")))
    return out


def load_catalog(path: str = "") -> List[ObjSpec]:
    with open(path or os.path.join(HERE, "configs", "objects_sim.json")) as f:
        return from_json(json.load(f)["objects"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args(argv)
    specs = generate(a.seed)
    jp, cp = os.path.join(HERE, "configs", "objects_sim.json"), os.path.join(HERE, "configs", "objects_sim.csv")
    with open(jp, "w") as f:
        json.dump({"seed": a.seed, "density_g_cm3": DENSITY_G_CM3, "note": "generated by arena/objects_gen.py; do not edit by hand", "objects": to_json(specs)}, f, indent=1)
    with open(cp, "w", newline="") as f:
        f.write(f"# generated by arena/objects_gen.py --seed {a.seed}; diameter_mm = 2 x radius of the circle around the object origin that encloses it\n")
        w = csv.writer(f)
        w.writerow(["name", "diameter_mm", "split", "hard_type", "category", "height_mm", "grasp_width_mm", "mass_g"])
        for s in specs:
            w.writerow([s.name, round(2 * s.footprint_radius_mm, 1), s.split, s.hard_type, s.category, round(s.height_mm, 1), round(s.min_width_mm, 1), s.mass_g])
    print(f"wrote {jp} and {cp}: {len(specs)} objects")
    for split in PLAN:
        ss = [s for s in specs if s.split == split]
        print(f"  {split:5s} {len(ss):2d}: " + ", ".join(f"{s.name}({s.hard_type or s.category}, h={s.height_mm:.0f}, w={s.min_width_mm:.0f}, D={2 * s.footprint_radius_mm:.0f})" for s in ss))


if __name__ == "__main__":
    main()
