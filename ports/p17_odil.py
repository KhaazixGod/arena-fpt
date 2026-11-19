"""P17 ODIL stage 1, re-implemented (component only, like the benchmark's P17_ODIL_STAGE1: "FPFH/FGR/ICP registration only; planar depth foreground
replaces GroundedSAM; reference grasp transfer + shared CL0; no wrist servo/replay/UKF").

Ideal depth (run_arena --depth) -> points over the belt plane in the belt window -> DBSCAN clusters (one per object).  Each cluster is registered to the
reference clouds (reference views, same camera): FPFH features, Fast Global Registration, then point-to-plane ICP (Open3D, MIT).  The best reference
(ICP fitness) gives the rigid transform that moves the reference grasp; the grasp is projected back to the image.  To keep one call short, only the
references whose height and footprint are closest to the cluster's are registered (top_k).
Options (--opt): voxel_mm (2), top_k (3), min_fitness (0.4), max_tilt_deg (25).  Chosen before any run; changed only on DEV (ARENA_TUNING_LOG.md).
"""
from __future__ import annotations

import math
from typing import List

import cv2
import numpy as np
import open3d as o3d

from common import FX, K, Belt, Grasp, belt_depth_mm, load_refs, suppress

VERSION = "p17_odil 1 (2026-11-20)"
REG = o3d.pipelines.registration


def backproject(depth: np.ndarray, mask: np.ndarray) -> np.ndarray:
    v, u = np.nonzero(mask)
    z = depth[v, u].astype(np.float64)
    ok = np.isfinite(z) & (z > 0)
    u, v, z = u[ok], v[ok], z[ok]
    return np.stack([(u - K[0, 2]) * z / FX, (v - K[1, 2]) * z / FX, z], -1)


def project(p: np.ndarray) -> np.ndarray:
    return np.stack([FX * p[:, 0] / p[:, 2] + K[0, 2], FX * p[:, 1] / p[:, 2] + K[1, 2]], -1)


class Detector:
    NAME = "P17_ODIL"

    def __init__(self, ref_dir: str, info: dict, voxel_mm="2", top_k="3", min_fitness="0.4", max_tilt_deg="25"):
        self.vox, self.top_k, self.min_fit, self.max_tilt = float(voxel_mm), int(top_k), float(min_fitness), float(max_tilt_deg)
        self.belt = Belt(info)
        self.region = self.belt.mask()
        self.refs = load_refs(ref_dir)
        self.rdata = []
        for r in self.refs:
            if r.depth is None:
                raise RuntimeError(f"P17 needs reference depth ({r.name})")
            pts = backproject(r.depth, r.mask)
            pc, f = self._prep(pts)
            zb = belt_depth_mm(r.depth, cv2.dilate(r.mask, np.ones((41, 41), np.uint8)))
            g = r.grasp
            zg = float(np.nanmin(r.depth[r.mask > 0]))                    # grasp point on the top of the object (below the grasp pixel)
            a = math.radians(g.angle_deg)
            gp = backproject_pts(np.array([[g.u, g.v], [g.u + 10 * math.cos(a), g.v - 10 * math.sin(a)]]), zg)
            self.rdata.append(dict(pc=pc, f=f, h=zb - zg, ext=self._extent(pts), gp=gp))

    def _prep(self, pts: np.ndarray):
        pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).voxel_down_sample(self.vox)
        pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=3 * self.vox, max_nn=30))
        pc.orient_normals_towards_camera_location(np.zeros(3))
        f = REG.compute_fpfh_feature(pc, o3d.geometry.KDTreeSearchParamHybrid(radius=7.5 * self.vox, max_nn=100))
        return pc, f

    @staticmethod
    def _extent(pts: np.ndarray) -> np.ndarray:
        xy = pts[:, :2] - pts[:, :2].mean(0)
        ev = np.sqrt(np.maximum(np.linalg.eigvalsh(np.cov(xy.T)), 0.0))
        return np.sort(ev)[::-1]

    def __call__(self, img: np.ndarray, depth=None) -> List[Grasp]:
        if depth is None:
            raise RuntimeError("P17_ODIL needs depth: run_arena --depth")
        depth = np.asarray(depth, np.float32)
        zb = belt_depth_mm(depth, self.region)
        fg = ((depth < zb - 3.0) & (self.region > 0)).astype(np.uint8)
        pts = backproject(depth, fg)
        if len(pts) < 50:
            return []
        pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).voxel_down_sample(self.vox)
        lab = np.asarray(pc.cluster_dbscan(eps=3 * self.vox, min_points=10))
        P = np.asarray(pc.points)
        out = []
        for k in range(lab.max() + 1 if len(lab) else 0):
            cp = P[lab == k]
            if len(cp) < 30:
                continue
            h, ext = zb - cp[:, 2].min(), self._extent(cp)
            cost = [abs(d["h"] - h) / 10.0 + float(np.abs(d["ext"] - ext).sum()) / 10.0 for d in self.rdata]
            pcc, fc = self._prep(cp)
            best = None
            for i in np.argsort(cost)[: self.top_k]:
                d = self.rdata[i]
                fgr = REG.registration_fgr_based_on_feature_matching(
                    d["pc"], pcc, d["f"], fc, REG.FastGlobalRegistrationOption(maximum_correspondence_distance=1.5 * self.vox))
                icp = REG.registration_icp(d["pc"], pcc, 2 * self.vox, fgr.transformation, REG.TransformationEstimationPointToPlane())
                T = icp.transformation
                tilt = math.degrees(math.acos(max(-1.0, min(1.0, T[2, 2]))))      # objects stay upright on the belt: reject flipped solutions
                if tilt > self.max_tilt or icp.fitness < self.min_fit:
                    continue
                if best is None or icp.fitness > best[0]:
                    best = (icp.fitness, i, T)
            if best is None:
                continue
            fit, i, T = best
            gp = self.rdata[i]["gp"] @ T[:3, :3].T + T[:3, 3]
            uv = project(gp)
            du, dv = uv[1] - uv[0]
            out.append(Grasp(float(uv[0, 0]), float(uv[0, 1]), math.degrees(math.atan2(-dv, du)) % 180.0, self.refs[i].grasp.width_mm, float(fit)))
        return suppress(out, 25.0)


def backproject_pts(uv: np.ndarray, z: float) -> np.ndarray:
    return np.stack([(uv[:, 0] - K[0, 2]) * z / FX, (uv[:, 1] - K[1, 2]) * z / FX, np.full(len(uv), z)], -1)
