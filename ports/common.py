"""Shared pieces of the P8 paper front-ends (ports/): camera model, belt region, reference views, grasp transfer.  numpy + OpenCV only.

Reference views (written by the arena's REFCAP method, ports/make_refs.sh): one object alone on the stopped belt, seen by the fixed camera:
<name>.png (BGR 1280x720), <name>_depth.npy (ideal depth, mm), <name>.json (grasp in pixels = the object's stored good grasp, ORACLE's choice).
A front-end finds a reference object in the current image and moves the reference grasp with the estimated transform ("reference grasp
transfer", as the benchmark's P05/P07/P17 ports did).  The reference set is fixed per run: train+dev objects (main), or + test objects (labelled).
"""
from __future__ import annotations

import glob
import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# fixed camera of configs/scene.toml: 1280x720, horizontal FOV 69.4 deg (RealSense D435i colour), pinhole, principal point at the centre
IMG_W, IMG_H, HFOV_DEG = 1280, 720, 69.4
FX = (IMG_W / 2.0) / math.tan(math.radians(HFOV_DEG / 2.0))
K = np.array([[FX, 0.0, IMG_W / 2.0], [0.0, FX, IMG_H / 2.0], [0.0, 0.0, 1.0]])


@dataclass
class Grasp:
    u: float
    v: float
    angle_deg: float      # closing axis in the image, CCW from +u, mod 180 (arena.methods.pixel_grasp convention)
    width_mm: float
    score: float = 1.0

    def as_dict(self) -> dict:
        return {"u": self.u, "v": self.v, "angle_deg": self.angle_deg % 180.0, "width_mm": self.width_mm, "score": self.score}


class Belt:
    """CL-0's top-down window (belt frame a, b) mapped to the image with calib.json's plane homography."""

    def __init__(self, info: dict):
        c = info["calib"]
        self.H = np.asarray(c["H"], float).reshape(3, 3)
        self.Hi = np.linalg.inv(self.H)
        self.phi = math.radians(c["belt_dir_deg"])
        self.u_hat = np.array([math.cos(self.phi), math.sin(self.phi)])
        self.v_hat = np.array([-math.sin(self.phi), math.cos(self.phi)])
        self.a0, self.a1, self.b0, self.b1 = info["window"]

    def ab_to_pix(self, ab: np.ndarray) -> np.ndarray:
        ab = np.asarray(ab, float).reshape(-1, 2)
        xy = ab[:, :1] * self.u_hat + ab[:, 1:2] * self.v_hat
        P = np.c_[xy, np.ones(len(xy))] @ self.Hi.T
        return P[:, :2] / P[:, 2:3]

    def roi(self, pad_px: int = 0) -> Tuple[int, int, int, int]:
        """Axis-aligned pixel box (u0, v0, u1, v1) around the window."""
        P = self.ab_to_pix(np.array([[self.a0, self.b0], [self.a0, self.b1], [self.a1, self.b0], [self.a1, self.b1]]))
        u0, v0 = np.floor(P.min(0)).astype(int) - pad_px
        u1, v1 = np.ceil(P.max(0)).astype(int) + pad_px
        return max(0, u0), max(0, v0), min(IMG_W, u1), min(IMG_H, v1)

    def mask(self) -> np.ndarray:
        P = self.ab_to_pix(np.array([[self.a0, self.b0], [self.a1, self.b0], [self.a1, self.b1], [self.a0, self.b1]]))
        m = np.zeros((IMG_H, IMG_W), np.uint8)
        cv2.fillPoly(m, [np.round(P).astype(np.int32)], 255)
        return m


def belt_depth_mm(depth: np.ndarray, region: np.ndarray) -> float:
    """Depth of the belt surface in a region (its most common depth: the belt covers most of the window)."""
    d = depth[region > 0]
    d = d[np.isfinite(d) & (d > 0)]
    hist, edges = np.histogram(d, bins=np.arange(d.min(), d.max() + 2.0, 1.0))
    return float(edges[np.argmax(hist)] + 0.5)


def foreground(depth: np.ndarray, region: np.ndarray, above_mm: float = 3.0) -> np.ndarray:
    """Planar-depth foreground (the benchmark's P17 note: "planar depth foreground replaces GroundedSAM"): pixels > above_mm over the belt."""
    zb = belt_depth_mm(depth, region)
    return ((depth < zb - above_mm) & (region > 0) & np.isfinite(depth)).astype(np.uint8) * 255


@dataclass
class Ref:
    name: str
    img: np.ndarray            # BGR full frame
    depth: Optional[np.ndarray]
    mask: np.ndarray           # uint8 0/255, the object
    bbox: Tuple[int, int, int, int]
    grasp: Grasp
    meta: dict


def load_refs(ref_dir: str, pad_mm: float = 15.0) -> List[Ref]:
    """Reference views of ref_dir (sorted by name).  Object mask = depth foreground around the reference grasp (one object per view)."""
    out = []
    for jf in sorted(glob.glob(os.path.join(ref_dir, "*.json"))):
        if os.path.basename(jf) == "index.json":
            continue
        m = json.load(open(jf))
        img = cv2.imread(os.path.join(ref_dir, m["image"]), cv2.IMREAD_COLOR)
        depth = np.load(os.path.join(ref_dir, m["depth"])) if m.get("depth") else None
        g = m["grasp_px"]
        grasp = Grasp(g["u"], g["v"], g["angle_deg"], g["width_mm"])
        px_per_mm = FX / max(1.0, float(np.nanmedian(depth))) if depth is not None else 1.85
        r = int((m["footprint_radius_mm"] + pad_mm) * px_per_mm)
        roi = np.zeros(img.shape[:2], np.uint8)
        cv2.circle(roi, (int(round(g["u"])), int(round(g["v"]))), r, 255, -1)
        if depth is not None:
            ring = np.zeros_like(roi)
            cv2.circle(ring, (int(round(g["u"])), int(round(g["v"]))), r + 40, 255, -1)
            fg = foreground(depth, ring)
            fg = cv2.bitwise_and(fg, roi)
        else:
            fg = roi
        n, lab, stats, _ = cv2.connectedComponentsWithStats(fg)
        if n > 1:                                         # keep the largest component (the object)
            k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            fg = (lab == k).astype(np.uint8) * 255
        ys, xs = np.nonzero(fg)
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else (0, 0, 1, 1)
        out.append(Ref(m["name"], img, depth, fg, bbox, grasp, m))
    if not out:
        raise RuntimeError(f"no reference views in {ref_dir}")
    return out


def transfer_grasp(g: Grasp, M: np.ndarray) -> Grasp:
    """Move a reference grasp with a 2x3 similarity / affine M (reference pixels -> current pixels)."""
    p = M @ np.array([g.u, g.v, 1.0])
    r = math.radians(g.angle_deg)
    d = M[:, :2] @ np.array([math.cos(r), -math.sin(r)])          # image v grows downwards: direction (cos, -sin) is CCW on screen
    ang = math.degrees(math.atan2(-d[1], d[0])) % 180.0
    return Grasp(float(p[0]), float(p[1]), ang, g.width_mm)


def similarity_ransac(src: np.ndarray, dst: np.ndarray, thresh_px: float = 5.0) -> Tuple[Optional[np.ndarray], int]:
    """2D similarity (rotation, scale, translation) with RANSAC; (M 2x3 or None, inliers).  Objects lie flat on the belt under a top-down camera."""
    if len(src) < 3:
        return None, 0
    M, inl = cv2.estimateAffinePartial2D(src.astype(np.float32), dst.astype(np.float32), method=cv2.RANSAC, ransacReprojThreshold=thresh_px,
                                         maxIters=2000, confidence=0.99)
    if M is None:
        return None, 0
    return M, int(inl.sum())


def suppress(grasps: List[Grasp], radius_px: float) -> List[Grasp]:
    """Keep the best grasp among those closer than radius_px (two references matched to the same object)."""
    keep: List[Grasp] = []
    for g in sorted(grasps, key=lambda x: -x.score):
        if all((g.u - k.u) ** 2 + (g.v - k.v) ** 2 > radius_px ** 2 for k in keep):
            keep.append(g)
    return keep
