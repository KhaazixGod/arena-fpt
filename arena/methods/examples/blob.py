"""EXAMPLE plug-in (not a baseline): a deliberately simple colour-blob grasp detector in image pixels, run through arena.methods.pixel_grasp.

    ~/env_isaac/bin/python -m arena.run_arena --methods CL0,arena.methods.examples.blob:make_method --cells dev_C0 --speeds L0 --n 5 --out runs/demo_blob
It shows the shape of a third-party method: a function image -> [PixelGrasp], and a factory make_method(ctx).  Saturated pixels = object (the belt is grey);
centre = blob centroid, closing axis = across the blob's longer side (cv2.minAreaRect), width = the shorter side in mm (local scale from calib.json).
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from arena.methods.base import MethodContext
from arena.methods.pixel_grasp import PixelGrasp, pixel_grasp_method


def make_detector(ctx: MethodContext, s_min: int = 90, min_area_px: int = 400):
    calib = ctx.calib

    def detect(img_bgr, depth_mm=None):
        hsv = cv2.cvtColor(np.ascontiguousarray(img_bgr), cv2.COLOR_BGR2HSV)
        m = ((hsv[..., 1] > s_min) | (hsv[..., 2] > 200)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
        out = []
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < min_area_px:
                continue
            ys, xs = np.nonzero(lab == i)
            (cu, cv_), (w, h), ang = cv2.minAreaRect(np.c_[xs, ys].astype(np.float32))
            long_ang = ang if w >= h else ang + 90.0                                    # OpenCV angle of the side of length w, image coords (y down)
            close_ang = -(long_ang + 90.0)                                              # across the long side; CCW on screen
            mm_px = calib.mm_per_pixel_at((cu, cv_))
            out.append(PixelGrasp(float(cu), float(cv_), close_ang % 180.0, float(min(w, h) * mm_px), float(st[i, cv2.CC_STAT_AREA])))
        return out
    return detect


def make_method(ctx: MethodContext):
    """example colour-blob detector + CL-0 executor (NOT a baseline)"""
    return pixel_grasp_method(ctx, make_detector(ctx))
