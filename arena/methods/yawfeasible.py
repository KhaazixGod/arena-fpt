"""CL-0's controller with ONE change: the feasibility checks (_pick_a_grasp, _lift_feasible) ask "reachable at the grasp yaw of this target?" (exact IK,
arena.reach_yaw.YawReach) instead of CL-0's roll-0 reach map.  Everything else (tracker, selection order, timing checks, BeltExecutor) is CL-0's code.

Used by ORACLE.  Also registered as CL0_YAW = CL-0 perception + this feasibility: NOT the baseline (an algorithm change of CL-0 needs the user's approval);
it exists to measure what the roll-0 reach map costs CL-0 before the user decides whether to change CL-0 (arena/CLAUDE.md rule 4).
"""
from __future__ import annotations

import copy

from cl0.controller import CL0Controller
from cl0.system import build_stack

from ..reach_yaw import YawReach
from .base import MethodContext, register


class YawFeasibleController(CL0Controller):
    """Overrides only _select (to set the yaw of each candidate before CL-0's own _pick_a_grasp) and _lift_feasible (target yaw)."""

    def _select(self, t, s_now, sdot) -> bool:                       # = CL0Controller._select + the yaw line
        best, best_a = None, -1e18
        for tr in self.tracker.confirmed():
            a_b, b, th, w, std = tr.estimate()
            self.reach.yaw_deg = self.phi + th
            a_g = self._pick_a_grasp(a_b, b, s_now, sdot)
            if a_g is not None and a_g > best_a:
                best, best_a = tr, a_g
        if best is None:
            return False
        self.target_tid = best.tid
        a, b, th, w, std = best.estimate()
        self.target_est = (a, b, th)
        self._event(t, "select", tid=best.tid, a_b=a, b=b, theta=th, width=w, std=std)
        return True

    def _lift_feasible(self, s_now: float, sdot: float, ahead_s: float) -> bool:
        _, th = self._target()
        self.reach.yaw_deg = self.phi + th
        return super()._lift_feasible(s_now, sdot, ahead_s)


def yaw_reach(ctx: MethodContext) -> YawReach:
    return YawReach(ctx.kin, ctx.cfg.robot.joint_margin_deg, ctx.cfg.robot.tilt_deg)


@register("CL0_YAW", doc="NOT the baseline: CL-0 perception + yaw-aware IK feasibility (measures the cost of CL-0's roll-0 reach map)")
def make_cl0_yaw(ctx: MethodContext):
    cfg = copy.deepcopy(ctx.cfg)
    st = build_stack(cfg, ctx.calib_path, ctx.background_path, cache_dir=ctx.cache_dir)
    return YawFeasibleController(cfg, ctx.kin, st.det, yaw_reach(ctx), st.calib.belt_dir_deg, st.calib.z_plane_mm)
