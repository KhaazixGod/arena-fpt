"""Điểm kẹp và hướng kẹp cho CL-0 (bước 3 của §3.4): cực đại biến đổi khoảng cách + yaw vuông góc trục dài (PCA),
bỏ vật rộng hơn w. Hàm chạy trên mặt nạ nhị phân trong ảnh nhìn từ trên (cột = a, hàng = b, mm/px = ``res``).

Hai nút tinh chỉnh KHÔNG thuộc CL-0 gốc (mặc định tắt, chỉ bật nếu bạn quyết định trong 2 ngày tinh chỉnh trên tập dev và ghi lại):
  * ``yaw_mode="local"``: PCA chỉ trên phần mặt nạ quanh điểm kẹp (hợp với vật có quai / dính nhau);
  * ``split="watershed"`` (ở perception): tách các vật dính nhau bằng watershed trên biến đổi khoảng cách.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class GraspParams:
    dt_plateau_frac: float = 0.95        # vùng "cao nguyên" DT: DT >= frac * DT_max; điểm kẹp = điểm cao nguyên gần tâm cao nguyên nhất
    isotropic_ratio: float = 1.15        # tỉ lệ trục (căn bậc hai tỉ số trị riêng) dưới ngưỡng này => coi là đẳng hướng
    isotropic_theta_deg: float = 90.0    # góc trục khép (hệ băng) dùng cho vật đẳng hướng; 90 = khép ngang băng
    yaw_mode: str = "pca"                # "pca" | "local"
    local_radius_mm: float = 25.0
    gripper_w_mm: float = 40.0           # độ mở kẹp hữu dụng w  [điền sau khi đo, §3.1 dòng 3]
    width_margin_mm: float = 4.0         # bỏ vật nếu bề ngang tại điểm kẹp > w - margin
    min_dt_mm: float = 1.5               # bán kính nội tiếp tối thiểu: mỏng hơn thì không kẹp được


@dataclass
class GraspCandidate:
    a_mm: float                 # điểm kẹp, toạ độ a của W-căn-theo-băng (đã gồm s) — do Detector điền
    b_mm: float
    theta_deg: float            # trục khép so với u_hat, mod 180
    width_mm: float             # bề ngang liên tục dọc trục khép qua điểm kẹp
    area_mm2: float
    dt_r_mm: float              # bán kính nội tiếp tại điểm kẹp
    aspect: float               # tỉ lệ trục dài/ngắn
    centroid_ab: Tuple[float, float]
    isotropic: bool
    col: float = 0.0            # vị trí điểm kẹp trong ảnh rectified (px)
    row: float = 0.0
    reject: str = ""            # "" = hợp lệ; "wide" | "thin" | "edge" | "arm" | "area" | ...


def _pca(xs: np.ndarray, ys: np.ndarray) -> Tuple[float, float, np.ndarray]:
    """(góc trục dài (rad, trong hệ cột/hàng), tỉ lệ trục, vector trục dài)."""
    if len(xs) < 3:
        return 0.0, 1.0, np.array([1.0, 0.0])
    c = np.cov(np.vstack([xs, ys]).astype(np.float64))
    w, V = np.linalg.eigh(c)
    w = np.maximum(w, 1e-9)
    v = V[:, 1]
    return math.atan2(v[1], v[0]), math.sqrt(w[1] / w[0]), v


def chord_width_px(mask: np.ndarray, col: float, row: float, theta_rad: float, step: float = 0.5, max_len: float = 400.0) -> float:
    """Độ dài đoạn liên tục của mặt nạ dọc đường qua (col,row) với hướng theta, chứa điểm đó (px)."""
    h, w = mask.shape
    d = np.array([math.cos(theta_rad), math.sin(theta_rad)])
    total = 0.0
    for sgn in (+1.0, -1.0):
        t = 0.0
        while t < max_len:
            t += step
            x, y = col + sgn * d[0] * t, row + sgn * d[1] * t
            xi, yi = int(round(x)), int(round(y))
            if xi < 0 or yi < 0 or xi >= w or yi >= h or not mask[yi, xi]:
                t -= step
                break
        total += t
    return total + 1.0       # +1 px: bề dày của điểm xuất phát


def analyze_component(mask: np.ndarray, res_mm: float, p: GraspParams) -> Optional[GraspCandidate]:
    """``mask``: bool/uint8 của MỘT thành phần (toàn ảnh hoặc ảnh cắt). Trả về GraspCandidate với (col,row) trong ảnh ``mask``
    (a_mm, b_mm để Detector điền). None nếu rỗng."""
    m8 = (mask > 0).astype(np.uint8)
    ys, xs = np.nonzero(m8)
    if len(xs) < 5:
        return None
    area_px = len(xs)
    # --- điểm kẹp: cực đại biến đổi khoảng cách (cao nguyên, điểm gần tâm cao nguyên nhất)
    dt = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    dmax = float(dt.max())
    plateau = np.argwhere(dt >= p.dt_plateau_frac * dmax)            # (row, col)
    cen = plateau.mean(axis=0)
    gp = plateau[int(np.argmin(((plateau - cen) ** 2).sum(axis=1)))]
    grow, gcol = float(gp[0]), float(gp[1])
    # --- hướng: PCA toàn thành phần hoặc cục bộ
    ang_long, aspect, _ = _pca(xs.astype(np.float64), ys.astype(np.float64))
    if p.yaw_mode == "local":
        r_px = p.local_radius_mm / res_mm
        sel = (xs - gcol) ** 2 + (ys - grow) ** 2 <= r_px ** 2
        if sel.sum() >= 10:
            al, asp, _ = _pca(xs[sel].astype(np.float64), ys[sel].astype(np.float64))
            if asp >= p.isotropic_ratio:
                ang_long, aspect = al, asp
    iso = aspect < p.isotropic_ratio
    theta_close = math.radians(p.isotropic_theta_deg) if iso else ang_long + math.pi / 2
    theta_deg = math.degrees(theta_close) % 180.0
    width = chord_width_px(m8 > 0, gcol, grow, theta_close) * res_mm
    cand = GraspCandidate(
        a_mm=0.0, b_mm=0.0, theta_deg=theta_deg, width_mm=width, area_mm2=area_px * res_mm * res_mm,
        dt_r_mm=dmax * res_mm, aspect=aspect, centroid_ab=(float(xs.mean()), float(ys.mean())), isotropic=iso,
        col=gcol, row=grow)
    if cand.dt_r_mm < p.min_dt_mm:
        cand.reject = "thin"
    elif width > p.gripper_w_mm - p.width_margin_mm:
        cand.reject = "wide"
    return cand


def watershed_split(mask: np.ndarray, frac: float = 0.55, min_dt_px: float = 3.0) -> List[np.ndarray]:
    """Tách một thành phần thành nhiều phần bằng watershed trên biến đổi khoảng cách. Trả về danh sách mặt nạ bool.
    Nếu chỉ có một đỉnh, trả về [mask]."""
    m8 = (mask > 0).astype(np.uint8)
    dt = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    if dt.max() < min_dt_px:
        return [m8 > 0]
    # hạt giống: vùng DT >= frac * max cục bộ — dùng ngưỡng toàn cục trên phiên bản làm mịn để tránh nhiễu biên
    dts = cv2.GaussianBlur(dt, (0, 0), 1.0)
    sure_fg = (dts >= frac * dts.max()).astype(np.uint8)
    n, markers = cv2.connectedComponents(sure_fg)
    if n <= 2:
        return [m8 > 0]
    markers = markers.astype(np.int32) + 1               # nền = 1, hạt giống >= 2
    markers[(m8 == 0)] = 1
    markers[(m8 > 0) & (sure_fg == 0)] = 0               # vùng chưa biết
    img = cv2.cvtColor(np.clip(dts / dts.max() * 255, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    cv2.watershed(img, markers)
    # watershed có thể để nền (nhãn 1) tràn vào mép vật và có đường biên (-1): gán lại điểm ảnh trong mặt nạ cho hạt giống gần nhất
    lab = np.where((markers >= 2) & (m8 > 0), markers, 0).astype(np.int32)
    src = (lab == 0).astype(np.uint8)
    _, idx = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    zero_vals = lab.ravel()[np.flatnonzero(src.ravel() == 0)]          # nhãn của điểm 0 thứ k (theo thứ tự quét hàng)
    full = zero_vals[np.clip(idx - 1, 0, len(zero_vals) - 1)]
    out = []
    for l in range(2, n + 1):
        part = (full == l) & (m8 > 0)
        if part.sum() >= 5:
            out.append(part)
    return out or [m8 > 0]
