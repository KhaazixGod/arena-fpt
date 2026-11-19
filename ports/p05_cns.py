"""P05 CNS front-end, re-implemented (component only, like the benchmark's P05_CNS_FRONTEND: "CNS classic matcher only; GNN servo not exercised").

Algorithm and parameters follow CNS's classic front-end (github.com/hhcaz/CNS, MIT, commit 6b42138, cns/frontend/classic.py; read, not imported):
SIFT keypoints + descriptors (cv2.SIFT_create, default parameters), FLANN kd-tree index (trees 5) on the target (= reference view) descriptors, knn 2
with checks 50, Lowe ratio 0.75, then RANSAC with a 5 px threshold.  CNS feeds the matches to its GNN servo (essential-matrix RANSAC); here the paper's
servo is not exercised (as in the benchmark): the inlier matches give a 2D similarity reference -> current image (objects lie flat on the belt under the
top-down camera) that moves the reference grasp.  One detection per reference view; reference views matching the same place are merged.
Options (--opt): min_inliers (8), ratio (0.75), ransac_px (5).  Chosen before any run; changed only on DEV (ARENA_TUNING_LOG.md).
"""
from __future__ import annotations

from typing import List

import cv2
import numpy as np

from common import Belt, Grasp, load_refs, similarity_ransac, suppress, transfer_grasp

VERSION = "p05_cns 1 (2026-11-20)"


class Detector:
    NAME = "P05_CNS"

    def __init__(self, ref_dir: str, info: dict, min_inliers="8", ratio="0.75", ransac_px="5"):
        self.min_inl, self.ratio, self.thr = int(min_inliers), float(ratio), float(ransac_px)
        self.belt = Belt(info)
        self.region = self.belt.mask()
        self.sift = cv2.SIFT_create()
        self.refs = load_refs(ref_dir)
        self.idx = []
        for r in self.refs:
            gray = cv2.cvtColor(r.img, cv2.COLOR_BGR2GRAY)
            kp, des = self.sift.detectAndCompute(gray, r.mask)
            if des is None or len(des) < 4:
                self.idx.append(None)
                continue
            tree = cv2.flann_Index()
            tree.build(des.astype(np.float32), dict(algorithm=1, trees=5))       # FLANN_INDEX_KDTREE, as CNS
            self.idx.append((np.float32([k.pt for k in kp]), tree))

    def __call__(self, img: np.ndarray, depth=None) -> List[Grasp]:
        gray = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_BGR2GRAY)
        kp, des = self.sift.detectAndCompute(gray, self.region)
        if des is None or len(des) < 4:
            return []
        cur = np.float32([k.pt for k in kp])
        des = des.astype(np.float32)
        out = []
        for r, ix in zip(self.refs, self.idx):
            if ix is None:
                continue
            tar_pos, tree = ix
            ind, dist = tree.knnSearch(des, knn=2, params=dict(checks=50))
            good = dist[:, 0] < self.ratio * dist[:, 1]
            if good.sum() < self.min_inl:
                continue
            M, n_in = similarity_ransac(tar_pos[ind[good, 0]], cur[good], self.thr)
            if M is None or n_in < self.min_inl:
                continue
            s = float(np.hypot(M[0, 0], M[1, 0]))
            if not 0.8 <= s <= 1.25:                       # same camera, same belt plane: a large scale change is a false match
                continue
            g = transfer_grasp(r.grasp, M)
            g.score = float(n_in)
            out.append(g)
        return suppress(out, 25.0)
