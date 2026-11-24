"""M1 of the thesis: CV + IK, open loop (plain kinematic baseline).

Camera -> background subtraction -> object centroid and long axis (the Detector and the Tracker of CL-0, unchanged) -> the most downstream object that is still inside the
reach of the arm (CL-0's selection rule) -> its position in the belt frame -> inverse kinematics with the belt counter (s(t)) to move above the object, descend, close, lift.
The one difference from CL-0: the estimate of the object is FROZEN at the moment of selection and is never updated afterwards (no closed loop on the camera, no correction
while approaching).  No wrist-branch planner W1 (the nearest wrist branch is always used).  No learning.  No access to the simulator state.

    --methods m4v2.kin_cv_ik:make_method
"""
from __future__ import annotations

import copy

from cl0.controller import CL0Controller
from cl0.system import build_stack


class OpenLoopCVIK(CL0Controller):
    def _select(self, t, s_now, sdot):
        ok = super()._select(t, s_now, sdot)
        if ok:
            self.frozen = True                     # _ingest() returns early from now on: the target estimate is never updated
            self._event(t, "kin_freeze", est=self.target_est)
        return ok


def make_method(ctx):
    """M1: CV + IK (open loop)"""
    cfg = copy.deepcopy(ctx.cfg)
    ctrl = build_stack(cfg, ctx.calib_path, ctx.background_path, cache_dir=ctx.cache_dir).ctrl
    ctrl.__class__ = OpenLoopCVIK
    return ctrl
