"""Hàm thuần (không chạm phần cứng) cho các bước hiệu chuẩn — để test được. Giao diện dòng lệnh nằm ở calibrate.py."""
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

import cv2
import numpy as np


# --------------------------------------------------------------------------------------------------------- bàn cờ
def board_object_points(cols: int, rows: int, square_mm: float) -> np.ndarray:
    """Toạ độ mm của góc k trong hệ bàn cờ: (cột·sq, hàng·sq). (Chiều có thể ngược W nhìn từ trên xuống: đã xử lý ở calib_from_board.)"""
    k = np.arange(cols * rows)
    return np.c_[(k % cols) * square_mm, (k // cols) * square_mm].astype(float)


def detect_board(img_bgr: np.ndarray, cols: int, rows: int) -> Optional[np.ndarray]:
    """Góc trong của bàn cờ (cols × rows góc trong), thứ tự hàng trước; (N,2) float hoặc None."""
    g = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if img_bgr.ndim == 3 else img_bgr
    ok, c = False, None
    if hasattr(cv2, "findChessboardCornersSB"):
        ok, c = cv2.findChessboardCornersSB(g, (cols, rows), cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_EXHAUSTIVE | cv2.CALIB_CB_ACCURACY)
    if not ok:
        ok, c = cv2.findChessboardCorners(g, (cols, rows), cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE)
        if ok:
            c = cv2.cornerSubPix(g, c, (7, 7), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.01))
    return c.reshape(-1, 2).astype(float) if ok else None


def default_touch_indices(cols: int, rows: int) -> List[int]:
    """9 điểm chạm: 4 góc, 4 trung điểm cạnh, tâm — thứ tự đi vòng quanh viền rồi vào tâm (ít phải di chuyển tay nhất).
    Nhiều điểm hơn => trung bình bớt nhiễu đặt tay (~1 mm mỗi lần chạm) trong phép xoay/tịnh tiến bàn cờ -> W."""
    cm, rm = cols // 2, rows // 2
    idx = [0, cm, cols - 1, rm * cols + cols - 1, rows * cols - 1, (rows - 1) * cols + cm, (rows - 1) * cols, rm * cols, rm * cols + cm]
    out: List[int] = []
    for k in idx:
        if k not in out:
            out.append(k)
    return out


def reject_touch_outliers(board_pts: np.ndarray, world_pts: np.ndarray, min_k: int = 6, abs_mm: float = 3.0, ratio: float = 3.0):
    """Phát hiện MỘT điểm chạm sai (chạm nhầm góc / trượt tay) bằng leave-one-out trên phép biến đổi cứng (có phản xạ).

    Trả (keep: bool (K,), loo: sai số leave-one-out (K,) [mm]). Chỉ loại khi K >= min_k, điểm tệ nhất có sai số LOO > abs_mm
    và > ratio × trung vị sai số LOO của các điểm còn lại — để không loại oan khi mọi điểm đều nhiễu như nhau."""
    from .geometry import fit_rigid_2d
    B, Wd = np.asarray(board_pts, float).reshape(-1, 2), np.asarray(world_pts, float).reshape(-1, 2)
    K = len(B)
    loo = np.zeros(K)
    for i in range(K):
        m = np.arange(K) != i
        f = fit_rigid_2d(B[m], Wd[m], allow_reflection=True)
        loo[i] = float(np.linalg.norm(f.apply(B[i:i + 1])[0] - Wd[i]))
    keep = np.ones(K, bool)
    if K >= min_k:
        j = int(np.argmax(loo))
        others = np.delete(loo, j)
        if loo[j] > abs_mm and loo[j] > ratio * max(float(np.median(others)), 0.3):
            keep[j] = False
    return keep, loo


def draw_board_preview(img: np.ndarray, corners: np.ndarray, touch_idx: Sequence[int]) -> np.ndarray:
    out = img.copy()
    for k, (u, v) in enumerate(corners):
        cv2.circle(out, (int(round(u)), int(round(v))), 3, (0, 200, 0), -1)
    for n, k in enumerate(touch_idx):
        u, v = corners[k]
        cv2.circle(out, (int(round(u)), int(round(v))), 12, (0, 0, 255), 2)
        cv2.putText(out, f"#{k} (lan {n + 1})", (int(u) + 14, int(v) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    return out


# --------------------------------------------------------------------------------------------------------- vạch đánh dấu
def find_marker(img: np.ndarray, ref: np.ndarray, thr: float = 30.0, min_area_px: int = 25) -> Optional[Tuple[float, float, float]]:
    """Vạch đánh dấu = thành phần lớn nhất của |ảnh − ảnh nền trống|. Trả (u, v, diện tích px) hoặc None. Tâm trọng số theo cường độ."""
    d = cv2.absdiff(img, ref)
    d = d.max(axis=2) if d.ndim == 3 else d
    d = cv2.GaussianBlur(d, (0, 0), 1.2)
    m = (d > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[i, cv2.CC_STAT_AREA] < min_area_px:
        return None
    ys, xs = np.nonzero(lab == i)
    w = d[ys, xs].astype(float)
    return float((xs * w).sum() / w.sum()), float((ys * w).sum() / w.sum()), float(len(xs))


# --------------------------------------------------------------------------------------------------------- độ trễ ảnh <-> băng
def estimate_latency(t_recv: np.ndarray, a_obs: np.ndarray, t_hist: np.ndarray, s_hist: np.ndarray,
                     lo: float = -0.05, hi: float = 0.8, step: float = 0.002, move_eps_mm: float = 0.05) -> Tuple[float, float, float]:
    """Độ trễ ảnh ↔ băng δ. Vạch phẳng nằm yên trong hệ băng, ghi từ lúc băng ĐỨNG YÊN rồi khởi động:

        a_obs(t_i) − a_tĩnh = s(t_i − δ) − s_tĩnh,    a_tĩnh = trung bình a_obs của các khung chắc chắn trước khi băng nhúc nhích.

    (Nếu không có đoạn đứng yên thì δ không xác định được: băng tốc độ hằng khiến δ lẫn vào a_b0.)
    Trả (δ [s], rms sai dư tại δ [mm], độ nhạy = rms trung bình ở δ ± 20 ms trừ rms tại δ [mm]); độ nhạy ≲ 0,2 mm: băng quá chậm / quá ít dữ liệu.
    """
    t_recv, a_obs = np.asarray(t_recv, float), np.asarray(a_obs, float)
    t_hist, s_hist = np.asarray(t_hist, float), np.asarray(s_hist, float)
    s0 = float(s_hist[0])
    moving = np.nonzero(s_hist > s0 + move_eps_mm)[0]
    if len(moving) == 0:
        raise ValueError("băng không chạy trong lúc ghi (bộ đếm/mô hình không đổi)")
    onset = float(t_hist[moving[0]])
    static = t_recv < (onset + lo - 0.01)
    if static.sum() < 5:
        raise ValueError(f"cần >= 5 khung ghi TRƯỚC khi băng chạy (có {int(static.sum())}); để vạch đứng yên ≥ 1 s rồi mới bật băng")
    a0 = float(np.mean(a_obs[static]))

    def rms_at(d):
        pred = np.interp(t_recv - d, t_hist, s_hist) - s0
        r = (a_obs - a0) - pred
        return float(np.sqrt(np.mean(r ** 2)))

    grid = np.arange(lo, hi + 1e-9, step)
    errs = np.array([rms_at(d) for d in grid])
    j = int(np.argmin(errs))
    d0 = float(grid[j])
    if 0 < j < len(grid) - 1:                            # tinh chỉnh parabol
        y0, y1, y2 = errs[j - 1], errs[j], errs[j + 1]
        den = y0 - 2 * y1 + y2
        if den > 1e-12:
            d0 += float(0.5 * step * (y0 - y2) / den)
    e0 = rms_at(d0)
    sens = 0.5 * (rms_at(d0 - 0.02) + rms_at(d0 + 0.02)) - e0
    return d0, e0, sens


# --------------------------------------------------------------------------------------------------------- độ trễ cánh tay
def estimate_arm_lag(t: np.ndarray, cmd_along: np.ndarray, meas_along: np.ndarray, v_mm_s: float, t_skip: float = 1.0) -> Tuple[float, float]:
    """Tay bám đoạn lệnh vận tốc hằng v: độ tụt ổn định ≈ v·τ. Trả (τ [s], độ lệch chuẩn của τ theo từng mẫu [s]).
    Bỏ ``t_skip`` giây đầu (quá độ)."""
    t, c, m = np.asarray(t, float), np.asarray(cmd_along, float), np.asarray(meas_along, float)
    sel = t >= (t[0] + t_skip)
    if sel.sum() < 5 or abs(v_mm_s) < 1e-6:
        raise ValueError("đoạn đo quá ngắn hoặc v = 0")
    tau = (c[sel] - m[sel]) / v_mm_s
    return float(np.mean(tau)), float(np.std(tau))
