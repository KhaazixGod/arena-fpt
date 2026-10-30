"""The generated object set: geometry consistent, graspable widths, disjoint splits with the three hard types in TEST, sheets inside the band."""
import os

import pytest

from conftest import ARENA


def test_catalog_properties():
    from arena.objects_gen import load_catalog
    specs = load_catalog()
    names = [s.name for s in specs]
    assert len(names) == len(set(names)) == 36
    by = {sp: [s for s in specs if s.split == sp] for sp in ("train", "dev", "test")}
    assert (len(by["train"]), len(by["dev"]), len(by["test"])) == (20, 6, 10)
    assert {"concave", "thin", "lowcon"} <= {s.hard_type for s in by["test"]}
    assert not any(s.hard_type for s in by["train"] + by["dev"])
    for s in specs:
        zlo = min(p.pos_mm[2] - p.half_h for p in s.parts); zhi = max(p.pos_mm[2] + p.half_h for p in s.parts)
        assert abs(zlo + s.height_mm / 2) < 1e-6 and abs(zhi - s.height_mm / 2) < 1e-6          # bottom at -H/2: world.place() puts it on the belt
        assert 0 < s.min_width_mm <= 50.0 + 1e-9                                                   # fits the 60 mm jaws with margin
        assert 2 * s.footprint_radius_mm <= 100.0                                                  # fits the 100 mm band
        assert 6.0 <= s.mass_g <= 80.0


def test_reject_locked_cells():
    from arena.run_arena import main
    with pytest.raises(SystemExit):
        main(["--methods", "NOOP", "--cells", "test_C0", "--out", "/tmp/never_used"])
