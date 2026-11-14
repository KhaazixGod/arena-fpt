"""Check of interface I2 without learning: replay one relabelled demo episode (the to_lerobot_i2.py action labels) open loop through the ACT_I2 executor.
If labels, belt frame, timing and IK are right, the replay picks the object like the ORACLE trial that recorded it.  Run on THAT trial's cell, speed and
arrangement (the episode's meta), in-process:

    $ISAAC -m arena.run_arena --methods arena.methods.replay_i2:make_method --method-arg ep=runs/e6_demos_real/episodes/episode_0001.npz \
        --objects sim --cells train_C0 --speeds L0.25 --first <arrangement index - 1> --n 1 --out runs/<name>
"""
from __future__ import annotations

import json
import os

import numpy as np

from arena.i2 import to_vec
from arena.methods.act_i2 import ACTI2Method


class ReplayI2(ACTI2Method):
    phase = "REPLAY_I2"

    def __init__(self, ctx, ep_path: str):
        cfg = ctx.cfg
        e = np.load(ep_path, allow_pickle=True)
        meta = json.loads(str(e["meta"]))
        g = np.load(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(ep_path))), f"trial_{meta['trial_id']:04d}_gt.npz"))
        cols = [str(c) for c in g["columns"]]
        s = np.interp(e["t"], g["gt"][:, cols.index("t")], g["gt"][:, cols.index("belt_s_gt")])
        self.policy, self.fps, self.replan = None, float(meta["fps"]), 10 ** 9
        self.kin = ctx.kin
        from arena.i2 import belt_unit
        self.u = belt_unit(ctx.calib.belt_dir_deg)
        self.traj = np.stack([to_vec(self.kin, a[:5], a[5], si, self.u) for a, si in zip(e["action"], s)])
        self.t_first = float(e["t"][0])
        self.tilt, self.margin, self.qdot = cfg.robot.tilt_deg, cfg.robot.joint_margin_deg, cfg.robot.q_dot_max_deg_s
        self.z_min = ctx.calib.z_plane_mm + cfg.executor.min_z_above_belt_mm
        self.duration_s, self.ckpt = cfg.executor.trial_timeout_s, f"replay:{os.path.basename(ep_path)}"
        self.reset(0.0, None)

    def _plan(self, img_bgr, vec, t_img):
        return self.traj, self.t0 + self.t_first


def make_method(ctx):
    return ReplayI2(ctx, ctx.extra["ep"])
