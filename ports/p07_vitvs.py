"""P07 ViT-VS front-end, re-implemented (component only, like the benchmark's P07_VITVS: "DINOv2 correspondences only; IBVS loop not exercised").

ViT-VS (Scherl et al. 2025, arXiv 2503.04545) matches DINOv2 patch features of the desired and current images: DINOv2 ViT-S/14, input 308 px, patch
and stride 14, layer-11 tokens, best-buddy (mutual nearest neighbour, cosine) correspondences.  Written from the paper (the authors' repository has no
licence file); DINOv2 weights from facebookresearch/dinov2 (Apache-2.0) through torch.hub.  Here the "desired image" is the reference view of an object
(its bounding box), the "current image" the belt window; both are resized by the same factor (window height -> 308 px) so a patch covers the same
belt area.  The IBVS loop is not exercised: the best-buddy pairs give a 2D similarity with RANSAC (threshold one patch) that moves the reference grasp.
Input size: ViT-VS uses 308 px for whole views; here the objects are small in the belt window (30-80 mm, ~4 patches across at 308 px), so the
window height is resized to 518 px, the largest size the paper allows (fixed on a plumbing test before any arena run: 308 px gave 2 best buddies
on an octagon, 518 px gave 7).  Rotation comes from a one-shot patch-level fit (no servo loop), so the grasp angle is coarse.
Options (--opt): min_inliers (4), min_sim (0.5), side (518), device (cuda).  Chosen before any arena run; changed only on DEV (ARENA_TUNING_LOG.md).
"""
from __future__ import annotations

import math
from typing import List

import cv2
import numpy as np
import torch

from common import Belt, Grasp, load_refs, similarity_ransac, suppress, transfer_grasp

VERSION = "p07_vitvs 1 (2026-11-20)"
P = 14
MEAN, STD = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])


class Detector:
    NAME = "P07_VITVS"

    def __init__(self, ref_dir: str, info: dict, min_inliers="4", min_sim="0.5", device="cuda", side="518"):
        self.min_inl, self.min_sim, self.dev = int(min_inliers), float(min_sim), device
        self.belt = Belt(info)
        self.u0, self.v0, self.u1, self.v1 = self.belt.roi(pad_px=8)
        self.f = int(side) / float(self.v1 - self.v0)                 # window height -> 518 px (the largest input ViT-VS allows; see the docstring)
        self.model = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14", trust_repo=True).to(device).eval()
        self.refs = load_refs(ref_dir)
        self.rfeat = []
        for r in self.refs:
            x0, y0, x1, y1 = r.bbox
            pad = int(math.ceil(P / self.f))
            x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(r.img.shape[1], x1 + pad), min(r.img.shape[0], y1 + pad)
            F, (hp, wp), (sx, sy) = self._features(r.img[y0:y1, x0:x1])
            m = cv2.resize(r.mask[y0:y1, x0:x1], (wp, hp), interpolation=cv2.INTER_AREA) > 127   # patches whose area is mostly the object
            jj, ii = np.meshgrid(np.arange(wp), np.arange(hp))
            pos = np.stack([x0 + (jj + 0.5) * P / sx, y0 + (ii + 0.5) * P / sy], -1)            # patch centres, full-image pixels
            self.rfeat.append((F[m.ravel()], pos[m]))

    @torch.inference_mode()
    def _features(self, bgr: np.ndarray):
        h, w = bgr.shape[:2]
        hp, wp = max(1, int(round(h * self.f / P))), max(1, int(round(w * self.f / P)))
        rgb = cv2.cvtColor(cv2.resize(bgr, (wp * P, hp * P), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        x = torch.from_numpy(((rgb - MEAN) / STD).transpose(2, 0, 1)).float()[None].to(self.dev)
        tok = self.model.get_intermediate_layers(x, n=[11], return_class_token=False)[0][0]      # (hp*wp, 384), layer 11
        tok = torch.nn.functional.normalize(tok, dim=-1)
        return tok, (hp, wp), (wp * P / w, hp * P / h)

    def __call__(self, img: np.ndarray, depth=None) -> List[Grasp]:
        crop = np.ascontiguousarray(img[self.v0:self.v1, self.u0:self.u1])
        Fc, (hp, wp), (sx, sy) = self._features(crop)
        jj, ii = np.meshgrid(np.arange(wp), np.arange(hp))
        cpos = np.stack([self.u0 + (jj + 0.5) * P / sx, self.v0 + (ii + 0.5) * P / sy], -1).reshape(-1, 2)
        out = []
        for r, (Fr, rpos) in zip(self.refs, self.rfeat):
            if len(Fr) < self.min_inl:
                continue
            S = Fr @ Fc.T                                   # cosine similarity (unit vectors)
            j = S.argmax(1)                                 # reference patch -> nearest current patch
            i_back = S.argmax(0)[j]                         # ... and back
            bb = (i_back == torch.arange(len(Fr), device=S.device)) & (S[torch.arange(len(Fr), device=S.device), j] >= self.min_sim)
            bb = bb.cpu().numpy()
            if bb.sum() < self.min_inl:
                continue
            M, n_in = similarity_ransac(rpos[bb], cpos[j.cpu().numpy()[bb]], P / self.f)
            if M is None or n_in < self.min_inl:
                continue
            s = float(np.hypot(M[0, 0], M[1, 0]))
            if not 0.75 <= s <= 1.33:
                continue
            g = transfer_grasp(r.grasp, M)
            g.score = float(n_in)
            out.append(g)
        return suppress(out, 25.0)
