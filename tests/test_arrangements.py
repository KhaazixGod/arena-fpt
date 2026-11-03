"""The DEV sheets respect the approved band and the clutter levels; placements put objects on the belt."""
import math
import os

import pytest

from conftest import ARENA


CASES = [("interim", c) for c in ("dev_C0", "dev_C1", "dev_C2", "dev_C3")] + [("sim", c) for c in ("train_C0", "train_C3", "dev_C0", "dev_C2", "dev_C3")] + \
        [("locked", c) for c in ("test_C0", "test_C2", "test_C3")]


@pytest.mark.parametrize("objset,cell", CASES)
def test_sheet_in_band_and_levels(objset, cell, scene_cfg):
    import csv
    from cl0.arrangements import read_arrangements
    from make_arrangements import LEVELS

    from arena.arrangements import band_geometry, to_placements
    from arena.objects import INTERIM_SPECS
    from arena.objects_gen import load_catalog
    specs = {s.name: s for s in (INTERIM_SPECS if objset == "interim" else load_catalog())}
    csvp = os.path.join(ARENA, "configs", "objects_interim.csv" if objset == "interim" else "objects_sim.csv")
    diam = {r["name"]: float(r["diameter_mm"]) for r in csv.DictReader(ln for ln in open(csvp) if not ln.startswith("#"))}
    d = {"interim": "arrangements", "sim": os.path.join("arrangements", "sim"), "locked": "locked"}[objset]
    sheet = read_arrangements(os.path.join(ARENA, d, f"{cell}.csv"))
    lo, hi = scene_cfg["belt"]["object_band_x_mm"]
    _, b_left = band_geometry(scene_cfg)
    (nlo, nhi), _, min_pair = LEVELS[cell.split("_")[1]]
    belt_start = scene_cfg["belt"]["center_a_mm"] - scene_cfg["belt"]["length_mm"] / 2
    for arr in sheet.values():
        assert nlo <= len(arr.items) <= nhi
        for it in arr.items:
            x, r = -(b_left - it.y_mm), diam[it.obj] / 2
            assert lo + r - 0.11 <= x <= hi - r + 0.11, (arr.arrangement_id, it.obj, x)
        for i, p in enumerate(arr.items):
            for q in arr.items[i + 1:]:
                assert math.hypot(p.x_mm - q.x_mm, p.y_mm - q.y_mm) >= diam[p.obj] / 2 + diam[q.obj] / 2 + min_pair - 0.2
        st = to_placements(arr, 0.0, scene_cfg, specs)
        a = [p["a_mm"] for p in st]
        assert abs(0.5 * (min(a) + max(a)) - scene_cfg["belt"].get("static_center_a_mm", 0.0)) < 1e-6
        mv = to_placements(arr, 37.5, scene_cfg, specs)
        assert min(p["a_mm"] - specs[p["name"]].footprint_radius_mm for p in mv) >= belt_start + 5.0 - 1e-6
        assert max(p["a_mm"] for p in mv) >= -150.0 - 1e-6
