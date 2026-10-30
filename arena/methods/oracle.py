"""ORACLE (upper bound M9, PRIVILEGED): CL-0's own controller (tracker, selection, BeltExecutor) with PERFECT perception and EXACT feasibility.

The CL-0 Detector is replaced by a detector that reads the ground-truth pose of every object resting on the belt at the instant the frame was CAPTURED
(the GT tap snapshots it then), inside the same top-down window as CL-0's background, with the same "arm" exclusion discs and the same width rule
(reject "wide" if width > gripper_w - margin).  Grasp: the object centre; closing axis across the SHORT side of a box (CL-0 treats near-square shapes as
isotropic, the oracle does not); round objects close TANGENTIALLY to the pan circle (the TCP offset, along the closing axis, then does not eat radial
reach; E3: CL-0's fixed isotropic yaw is IK-infeasible at lift height near the base).  Feasibility = exact IK at the target's grasp yaw
(methods/yawfeasible.py) instead of CL-0's roll-0 reach map.  So ORACLE measures what the environment (physics, executor, kinematics) allows.
"""
from __future__ import annotations

import copy
import math
from typing import Sequence, Tuple

import numpy as np

from cl0.perception import BackgroundModel, Detection, DetectResult, window_of

from .base import MethodContext, register


class OracleDetector:
    def __init__(self, ctx: MethodContext):
        self.gt = ctx.gt
        self.cfg = ctx.cfg
        self.phi = ctx.calib.belt_dir_deg
        self.win = window_of(BackgroundModel.load(ctx.background_path))
        g = ctx.cfg.perception.grasp
        self.max_w = g.gripper_w_mm - g.width_margin_mm
        self.iso_theta = g.isotropic_theta_deg
        k = ctx.kin
        self.pan_xy = (float(k._T0[0][0, 3]) * 1000.0, float(k._T0[0][1, 3]) * 1000.0) if hasattr(k, "_T0") else (38.8, 0.0)

    def _grasp(self, spec, yaw_world_deg: float, x_mm: float = 0.0, y_mm: float = 0.0) -> Tuple[float, float, float, float]:
        """(theta_deg in CL-0's convention, width_mm, area_mm2, aspect)"""
        if spec.shape == "compound":                    # the stored good grasp of a generated object (objects_gen.py)
            return (yaw_world_deg + spec.grasp[2] - self.phi) % 180.0, spec.grasp[3], spec.grasp[3] ** 2, 1.0
        if spec.shape == "box":
            lx, ly = spec.dims_mm[0], spec.dims_mm[1]
            if lx >= ly:            # long axis = local x: close across it (along local y)
                ax, w, L = yaw_world_deg + 90.0, ly, lx
            else:
                ax, w, L = yaw_world_deg, lx, ly
            return (ax - self.phi) % 180.0, w, lx * ly, L / w
        d = spec.dims_mm[0]
        radial = math.degrees(math.atan2(y_mm - self.pan_xy[1], x_mm - self.pan_xy[0]))
        return (radial + 90.0 - self.phi) % 180.0, d, math.pi * d * d / 4.0, 1.0

    def detect(self, frame_bgr: np.ndarray, s_mm: float, exclude: Sequence[Tuple[float, float, float]] = ()) -> DetectResult:
        snap = self.gt.objects_at_capture(frame_bgr)
        dets, cid = [], 0
        for name, o in snap.items():
            sp = self.gt.spec(name)
            a, b, z = o["a_mm"], o["b_mm"], o["pos_mm"][2]
            x, y = float(o["pos_mm"][0]), float(o["pos_mm"][1])
            if sp.shape == "compound" and (sp.grasp[0] or sp.grasp[1]):      # grasp point away from the origin: rotate it into the world, re-project on the belt
                c, sn = math.cos(math.radians(o["yaw_deg"])), math.sin(math.radians(o["yaw_deg"]))
                x, y = x + c * sp.grasp[0] - sn * sp.grasp[1], y + sn * sp.grasp[0] + c * sp.grasp[1]
                pu = (math.cos(math.radians(self.phi)), math.sin(math.radians(self.phi)))
                a, b = x * pu[0] + y * pu[1], -x * pu[1] + y * pu[0]
            if abs(z - (self.gt.belt_top_mm + sp.height_mm / 2.0)) > 5.0:          # not resting on the belt (parked, held, falling)
                continue
            if not (self.win.a_min <= a <= self.win.a_max and self.win.b_min <= b <= self.win.b_max):
                continue
            cid += 1
            th, w, area, asp = self._grasp(sp, o["yaw_deg"], x, y)
            rej = "wide" if w > self.max_w else ""
            if not rej and any((a - ea) ** 2 + (b - eb) ** 2 <= er ** 2 for (ea, eb, er) in exclude):
                rej = "arm"
            dets.append(Detection(a, b, th, w, area, w / 2.0, asp, (a, b), rej, cid))
        return DetectResult(dets, np.zeros((1, 1), np.uint8), np.zeros((1, 1, 3), np.uint8), {"oracle": True, "n_comp": len(dets)})


@register("ORACLE", privileged=True, doc="CL-0 controller + ground-truth perception (upper bound)", uses_pixels=False)
def make_oracle(ctx: MethodContext):
    if ctx.gt is None:
        raise RuntimeError("ORACLE needs the ground-truth tap (run_arena gives it only to privileged methods)")
    from .yawfeasible import YawFeasibleController, yaw_reach
    cfg = copy.deepcopy(ctx.cfg)
    return YawFeasibleController(cfg, ctx.kin, OracleDetector(ctx), yaw_reach(ctx), ctx.calib.belt_dir_deg, ctx.calib.z_plane_mm)
