"""Adapter for grasp detectors that work in IMAGE PIXELS (the usual output of grasp-detection papers: centre (u, v), closing angle, width).

    from arena.methods.pixel_grasp import pixel_grasp_method
    def my_detect(img_bgr, depth_mm):        # depth_mm is None unless run_arena --depth
        return [PixelGrasp(u, v, angle_deg, width_mm, score), ...]
    def make_method(ctx):                    # run_arena --methods mypkg.mymodule:make_method
        return pixel_grasp_method(ctx, my_detect)

The detections are mapped to CL-0's belt frame with calib.json (homography pixel -> belt plane, belt direction) and fed to CL-0's tracker, target
selection and BeltExecutor (feasibility: "yaw" = exact IK at the grasp yaw, default; "cl0" = CL-0's own roll-0 reach map).  So two such methods differ ONLY
in perception.  ``angle_deg``: direction of the CLOSING axis in the image, degrees, counter-clockwise from the image +u axis (right), mod 180.
Width: mm across the closing axis (detections wider than gripper_w - margin are rejected, as CL-0 does).  Pixels outside CL-0's top-down window are ignored.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np

from cl0.controller import CL0Controller
from cl0.perception import BackgroundModel, Detection, DetectResult, window_of
from cl0.system import get_reach

from .base import MethodContext
from .yawfeasible import YawFeasibleController, yaw_reach


@dataclass
class PixelGrasp:
    u: float
    v: float
    angle_deg: float
    width_mm: float
    score: float = 1.0


class PixelGraspDetector:
    def __init__(self, ctx: MethodContext, detect_fn: Callable[[np.ndarray, Optional[np.ndarray]], List[PixelGrasp]], min_score: float = 0.0):
        self.fn, self.calib, self.min_score = detect_fn, ctx.calib, min_score
        self.phi = ctx.calib.belt_dir_deg
        c, s = math.cos(math.radians(self.phi)), math.sin(math.radians(self.phi))
        self.u_hat, self.v_hat = np.array([c, s]), np.array([-s, c])
        self.win = window_of(BackgroundModel.load(ctx.background_path))
        g = ctx.cfg.perception.grasp
        self.max_w = g.gripper_w_mm - g.width_margin_mm
        self.last: List[PixelGrasp] = []

    def to_belt(self, g: PixelGrasp) -> Tuple[float, float, float]:
        """(a, b, theta) in CL-0's W-aligned-to-belt coordinates."""
        r = math.radians(g.angle_deg)
        du, dv = 5.0 * math.cos(r), -5.0 * math.sin(r)               # image v grows DOWNWARDS; angle is CCW as seen on screen
        P = self.calib.pix_to_world(np.array([[g.u, g.v], [g.u + du, g.v + dv]]))
        a, b = float(P[0] @ self.u_hat), float(P[0] @ self.v_hat)
        d = P[1] - P[0]
        theta = (math.degrees(math.atan2(d[1], d[0])) - self.phi) % 180.0
        return a, b, theta

    def detect(self, frame_bgr: np.ndarray, s_mm: float, exclude: Sequence[Tuple[float, float, float]] = ()) -> DetectResult:
        grasps = [g for g in (self.fn(frame_bgr, getattr(frame_bgr, "depth_mm", None)) or []) if g.score >= self.min_score]
        self.last = grasps
        dets = []
        for i, g in enumerate(sorted(grasps, key=lambda g: -g.score), start=1):
            a, b, th = self.to_belt(g)
            if not (self.win.a_min <= a <= self.win.a_max and self.win.b_min <= b <= self.win.b_max):
                continue
            rej = "wide" if g.width_mm > self.max_w else ""
            if not rej and any((a - ea) ** 2 + (b - eb) ** 2 <= er ** 2 for (ea, eb, er) in exclude):
                rej = "arm"
            dets.append(Detection(a, b, th, g.width_mm, g.width_mm ** 2, g.width_mm / 2.0, 1.0, (a, b), rej, i))
        return DetectResult(dets, np.zeros((1, 1), np.uint8), np.zeros((1, 1, 3), np.uint8), {"n_grasps": len(grasps)})


def pixel_grasp_method(ctx: MethodContext, detect_fn, feasibility: str = "yaw", min_score: float = 0.0):
    """A full method (CL-0's tracker / selection / BeltExecutor) around your pixel-space grasp detector."""
    cfg = copy.deepcopy(ctx.cfg)
    det = PixelGraspDetector(ctx, detect_fn, min_score)
    if feasibility == "yaw":
        return YawFeasibleController(cfg, ctx.kin, det, yaw_reach(ctx), ctx.calib.belt_dir_deg, ctx.calib.z_plane_mm)
    if feasibility == "cl0":
        return CL0Controller(cfg, ctx.kin, det, get_reach(ctx.kin, cfg, ctx.cache_dir), ctx.calib.belt_dir_deg, ctx.calib.z_plane_mm)
    raise ValueError(feasibility)
