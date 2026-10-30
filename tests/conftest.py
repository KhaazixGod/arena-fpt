"""Tests of the arena that do NOT need Isaac Sim (a fake world stands in).  Run:  cd arena && ~/venvs/cl0/bin/python -m pytest tests -q"""
import os
import sys

import numpy as np
import pytest

ARENA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(ARENA)
for p in (ARENA, os.path.join(ROOT, "cl0"), os.path.join(ROOT, "dir1")):
    if p not in sys.path:
        sys.path.insert(0, p)


class FakeWorld:
    """The part of IsaacWorld that IsaacPlatform uses.  Objects ride the belt at the applied surface speed; render_bgr returns the step counter."""

    def __init__(self, scene_cfg, specs):
        self.cfg = scene_cfg
        self.hz = float(scene_cfg["physics"]["hz"])
        self.dt = 1.0 / self.hz
        self.k = 0
        self.belt_top_mm = float(scene_cfg["belt"]["z_mm"])
        self.spec_by_name = {s.name: s for s in specs}
        self.depth_enabled = False
        self.q = np.zeros(6)
        self.targets = np.zeros(6)
        self.belt_v = 0.0
        self.belt_v_log = []
        self.objs = {}

    def set_belt_speed(self, v):
        self.belt_v = float(v)

    def park_all(self):
        self.objs = {}

    def teleport_arm(self, q5, grip_pos):
        self.q[:5] = np.asarray(q5, float)
        self.q[5] = grip_pos
        self.targets = self.q.copy()

    def step(self):
        self.k += 1
        self.belt_v_log.append(self.belt_v)
        for o in self.objs.values():
            o[0] += self.belt_v * self.dt

    def step_seconds(self, s):
        for _ in range(int(round(s * self.hz))):
            self.step()

    def place(self, placements):
        for p in placements:
            self.objs[p["name"]] = [p["a_mm"], p["b_mm"]]

    def finite(self):
        return True

    def joint_deg(self):
        return self.q.copy()

    def grip_deg_to_pos(self, d):
        return float(d)

    def set_targets(self, q5, grip):
        if q5 is not None:
            self.targets[:5] = q5
        if grip is not None:
            self.targets[5] = grip

    def gt_objects(self):
        out = {}
        for n, (a, b) in self.objs.items():
            h = self.spec_by_name[n].height_mm
            out[n] = {"a_mm": a, "b_mm": b, "pos_mm": np.array([-b, a, self.belt_top_mm + h / 2.0]), "yaw_deg": 90.0}
        return out

    def render_bgr(self):
        return np.array([[self.k]], dtype=np.int64)          # the pixel IS the capture step: lets the tests check timing

    def last_depth_mm(self):
        return None

    def hard_reset(self):
        self.belt_v = 0.0


@pytest.fixture
def scene_cfg():
    from arena.scene import load_scene_cfg
    return load_scene_cfg()


@pytest.fixture
def arena_cfg():
    from cl0.config import load_config
    cfg = load_config(os.path.join(ARENA, "configs", "arena.toml"))
    cfg.belt.mm_per_step = 0.05001
    return cfg


@pytest.fixture
def fake_platform(scene_cfg, arena_cfg):
    from arena.objects import INTERIM_SPECS
    from arena.platform import IsaacPlatform
    w = FakeWorld(scene_cfg, INTERIM_SPECS)
    return IsaacPlatform(w, arena_cfg), w
