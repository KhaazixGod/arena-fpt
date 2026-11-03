"""Bản đồ tầm với của SO-101 cho kẹp có góc chúc cố định (mặc định thẳng đứng), tính bằng lấy mẫu thuận (FK).

Với mỗi ô (x, y) trong W lưu khoảng độ cao [zmin, zmax] mà TCP với tới được khi ba khớp phẳng thoả
``lift + elbow + flex = tilt`` và mọi khớp cách biên >= margin. Tra cứu O(1), thay cho gọi IK khi chỉ cần biết "có với tới không"
(chọn vật, vẽ bản đồ để đặt băng). Quyết định cuối cùng khi ra lệnh vẫn dùng IK.

Giới hạn: chỉ động học, KHÔNG xét va chạm với đế/bàn/băng, và bỏ qua ảnh hưởng của roll lên TCP (lệch tối đa ~8 mm do
điểm TCP của URDF lệch 7,9 mm khỏi trục roll); ô sát biên nên coi là không chắc.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import cv2
import numpy as np

from .kinematics import SO101Kinematics


class TopDownReach:
    def __init__(self, K: SO101Kinematics, tilt_deg: float = 90.0, step_mm: float = 4.0, margin_deg: float = 3.0,
                 xlim=(-150.0, 450.0), ylim=(-350.0, 350.0), angle_step_deg: float = 1.0):
        self.K, self.tilt, self.step, self.margin = K, tilt_deg, step_mm, margin_deg
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim
        self.nx = int(math.ceil((self.x1 - self.x0) / step_mm)) + 1
        self.ny = int(math.ceil((self.y1 - self.y0) / step_mm)) + 1
        self.angle_step = angle_step_deg
        self.zmin = np.full((self.ny, self.nx), np.inf, np.float32)
        self.zmax = np.full((self.ny, self.nx), -np.inf, np.float32)
        self._built = False

    def build(self) -> "TopDownReach":
        K = self.K
        if not K._pitch_linear:
            raise RuntimeError("URDF không có cấu trúc lift+elbow+flex = góc chúc; không dựng được bản đồ thuận")
        lo, hi = K.limits_deg
        m = self.margin
        st = self.angle_step
        pans = np.arange(lo[0] + m, hi[0] - m + 1e-9, st)
        lifts = np.arange(lo[1] + m, hi[1] - m + 1e-9, st)
        elbows = np.arange(lo[2] + m, hi[2] - m + 1e-9, st)
        LL, EE = np.meshgrid(lifts, elbows, indexing="ij")
        FF = self.tilt - LL - EE - K._pitch_c0
        ok = (FF >= lo[3] + m) & (FF <= hi[3] - m)
        LL, EE, FF = LL[ok], EE[ok], FF[ok]
        roll = float(np.clip(0.0, lo[4] + m, hi[4] - m))
        for pan in pans:
            Q = np.radians(np.stack([np.full_like(LL, pan), LL, EE, FF, np.full_like(LL, roll)], axis=1))
            P = K._fk_batch(Q)[:, :3, 3] * 1000.0
            ix = np.floor((P[:, 0] - self.x0) / self.step + 0.5).astype(int)
            iy = np.floor((P[:, 1] - self.y0) / self.step + 0.5).astype(int)
            inb = (ix >= 0) & (ix < self.nx) & (iy >= 0) & (iy < self.ny)
            ix, iy, z = ix[inb], iy[inb], P[inb, 2].astype(np.float32)
            np.minimum.at(self.zmin, (iy, ix), z)
            np.maximum.at(self.zmax, (iy, ix), z)
        # lấp lỗ do lấy mẫu thưa: đóng hình thái 3x3 trên mặt nạ, z lấy theo lân cận
        valid = np.isfinite(self.zmin)
        zmn = np.where(valid, self.zmin, 1e6).astype(np.float32)
        zmx = np.where(valid, self.zmax, -1e6).astype(np.float32)
        k = np.ones((3, 3), np.uint8)
        zmn_f = cv2.erode(zmn, k)
        zmx_f = cv2.dilate(zmx, k)
        closed = cv2.morphologyEx(valid.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0
        self.zmin = np.where(closed, zmn_f, np.inf).astype(np.float32)
        self.zmax = np.where(closed, zmx_f, -np.inf).astype(np.float32)
        self._built = True
        return self

    def _cell(self, x: float, y: float):
        ix = int(round((x - self.x0) / self.step))
        iy = int(round((y - self.y0) / self.step))
        return ix, iy

    def z_range(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        ix, iy = self._cell(x, y)
        if not (0 <= ix < self.nx and 0 <= iy < self.ny) or not np.isfinite(self.zmin[iy, ix]):
            return None
        return float(self.zmin[iy, ix]), float(self.zmax[iy, ix])

    def contains(self, x: float, y: float, z: float, inner_mm: float = 0.0) -> bool:
        """Với tới được (x,y,z)? ``inner_mm`` > 0: yêu cầu cả vòng quanh bán kính này cũng với tới được (an toàn biên)."""
        if not self._built:
            raise RuntimeError("gọi build() trước")
        n = int(math.ceil(inner_mm / self.step))
        offs = [(0, 0)] if n == 0 else [(dx, dy) for dx in (-n, 0, n) for dy in (-n, 0, n)]
        for dx, dy in offs:
            r = self.z_range(x + dx * self.step, y + dy * self.step)
            if r is None or not (r[0] <= z <= r[1]):
                return False
        return True

    def mask_at_z(self, z: float) -> np.ndarray:
        return (self.zmin <= z) & (z <= self.zmax)

    def save(self, path: str) -> None:
        np.savez_compressed(path, zmin=self.zmin, zmax=self.zmax, tilt=self.tilt, step=self.step, margin=self.margin,
                            x0=self.x0, y0=self.y0)

    def load_into(self, path: str) -> "TopDownReach":
        d = np.load(path)
        if abs(float(d["tilt"]) - self.tilt) > 1e-6 or abs(float(d["step"]) - self.step) > 1e-6:
            raise ValueError("bản đồ lưu khác tilt/step")
        self.zmin, self.zmax = d["zmin"], d["zmax"]
        self._built = True
        return self
