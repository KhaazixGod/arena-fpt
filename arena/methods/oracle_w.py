"""ORACLE_W and CL0_W (paper-dev; KE_HOACH_PAPER.md P2): ORACLE and CL0 with W1, the wrist-roll-aware grasp-yaw branch (arena/wrist_branch.py).

ORACLE_W = ORACLE (ground-truth perception, yaw-aware feasibility, CL-0's tracker/selection/executor) + W1.  It is the fixed teacher for the new demos.
CL0_W    = CL0 (the frozen baseline, unchanged perception and reach map) + W1, so the modular baseline gets the same executor fix as the teacher of the
           learned policies (approved by the user on 15/11/2026, arena/CLAUDE.md rule 8).  CL0 and ORACLE stay registered unchanged.
W1 changes only the attempts whose predicted wrist roll on CL-0's branch comes within h_min of a joint limit; every attempt logs a ``w1_branch`` event.
The object's future belt travel is predicted from the measured belt speed, the PC's own commanded speed and the firmware ramp (cfg.belt.accel_mm_s2):
each trial starts the belt from rest, so the measured speed at selection (t = 0.18 s) is only ~25 of 75 mm/s at L0.5 (first run, v1, used it as is).
Method args (``--method-arg``): ``w1_window_s`` (4.0), ``w1_h_min_deg`` (10.0).
"""
from __future__ import annotations

import copy

from cl0.controller import CL0Controller
from cl0.system import build_stack
from cl0.types import Command

from ..wrist_branch import BranchExecutor, WristModel, commanded_speed, free_roll, plan_branch
from .base import MethodContext, register
from .yawfeasible import YawFeasibleController, yaw_reach


class W1Mixin:
    """W1 on top of a CL-0 controller class: BranchExecutor + a branch plan when a target is selected.  Everything else is the base class's code."""

    w1_window_s = 4.0
    w1_h_min_deg = 10.0

    def _w1_init(self, extra=None) -> None:
        extra = extra or {}
        self.w1_window_s = float(extra.get("w1_window_s", self.w1_window_s))
        self.w1_h_min_deg = float(extra.get("w1_h_min_deg", self.w1_h_min_deg))
        self.wm = WristModel(self.kin, self.cfg.robot.tilt_deg)
        self.kin_free = free_roll(self.kin)
        self.exe = BranchExecutor(self.cfg, self.kin, self.phi, self.zb, self.wm)
        self.reset(0.0, None)

    def step(self, t, frame, belt, state) -> Command:                 # keep the belt object for the commanded speed (wrist_branch.commanded_speed)
        self._w1_belt = belt
        return super().step(t, frame, belt, state)

    def _do_wait(self, t, dt, s_now, sdot, state, tcp) -> Command:      # = CL0Controller._do_wait + the W1 plan line
        if self.tracker.confirmed() and self._select(t, s_now, sdot):
            self.exe.start(tcp, s_now, sdot)
            self._w1_plan(t, s_now, sdot, tcp)
            self._settle = 0.0
            self._goto(t, "APPROACH")
            return self._do_approach(t, dt, s_now, sdot, state, tcp)
        return Command(None, self.cfg.robot.gripper_open, "WAIT")

    def _w1_plan(self, t, s_now, sdot, tcp) -> None:
        a, b, th = self.target_est
        v_cmd = commanded_speed(getattr(self, "_w1_belt", None))
        plan = plan_branch(self.kin, self.kin_free, self.wm, self.cfg, self.phi, self.zb, self.exe.q_last, float(self.exe.fth.x),
                           a, b, th, s_now, sdot, window_s=self.w1_window_s, h_min_deg=self.w1_h_min_deg,
                           v_cmd=v_cmd, accel_mm_s2=float(self.cfg.belt.accel_mm_s2))
        self.exe.set_plan(plan.th_plan, plan.m0)
        self._event(t, "w1_branch", **plan.event())


class OracleW(W1Mixin, YawFeasibleController):
    def __init__(self, *a, extra=None, **k):
        super().__init__(*a, **k)
        self._w1_init(extra)


class CL0W(W1Mixin, CL0Controller):
    def __init__(self, *a, extra=None, **k):
        super().__init__(*a, **k)
        self._w1_init(extra)


@register("ORACLE_W", privileged=True, doc="ORACLE + W1 (wrist-roll-aware grasp-yaw branch); teacher for the paper demos", uses_pixels=False)
def make_oracle_w(ctx: MethodContext):
    if ctx.gt is None:
        raise RuntimeError("ORACLE_W needs the ground-truth tap (run_arena gives it only to privileged methods)")
    from .oracle import OracleDetector
    cfg = copy.deepcopy(ctx.cfg)
    return OracleW(cfg, ctx.kin, OracleDetector(ctx), yaw_reach(ctx), ctx.calib.belt_dir_deg, ctx.calib.z_plane_mm, extra=ctx.extra)


@register("CL0_W", doc="CL-0 baseline + W1 (wrist-roll-aware grasp-yaw branch); modular baseline of the paper")
def make_cl0_w(ctx: MethodContext):
    cfg = copy.deepcopy(ctx.cfg)
    st = build_stack(cfg, ctx.calib_path, ctx.background_path, cache_dir=ctx.cache_dir)
    st.ctrl.close()
    return CL0W(st.cfg, st.kin, st.det, st.reach, st.calib.belt_dir_deg, st.calib.z_plane_mm, extra=ctx.extra)
