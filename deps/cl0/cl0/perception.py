"""Nhận thức của CL-0: mô hình nền của băng trống -> mặt nạ -> thành phần liên thông -> điểm kẹp (bước 2–3 của §3.4).

Mọi thứ chạy trong ảnh "nhìn từ trên" căn theo băng (xem geometry.py): 1 điểm ảnh = ``res_mm`` mm, cột = a, hàng = b.
Nhờ đó dịch chuyển của băng là phép tịnh tiến theo cột, nên băng có texture được bù chính xác bằng cách dịch mô hình nền
theo s(t) (đúng ý "nhớ bù độ dịch băng nếu mặt băng có texture").

* Băng trơn (khuyến nghị): ``textured=False``, nền là trung bình của các khung băng trống, không phụ thuộc s.
* Băng có texture: ``textured=True`` + ``period_mm`` = chu vi băng; nền là tấm canvas tuần hoàn theo toạ độ vật liệu băng
  a_b = a - s, dựng từ các khung băng trống quay ít nhất một vòng. Cần căn thời gian ảnh <-> s tốt (sai 30 ms ở 100 mm/s = 3 mm);
  ``shift_search_mm`` > 0 bật tìm lệch nhỏ để bù.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from .geometry import Rectifier
from .grasp import GraspCandidate, GraspParams, analyze_component, watershed_split


@dataclass
class PerceptionParams:
    res_mm: float = 0.5
    k_sigma: float = 4.0                  # ngưỡng = max(k_sigma * sigma_nền, t_min)
    t_min: float = 18.0                   # mức xám tối thiểu (tối đa trên 3 kênh)
    sigma_floor: float = 3.0
    photometric_comp: bool = True         # trừ độ lệch trung vị toàn ảnh (bù đổi sáng/phơi sáng)
    open_mm: float = 1.5
    close_mm: float = 3.0
    min_area_mm2: float = 150.0
    max_area_mm2: float = 12000.0         # lớn hơn: coi là cánh tay/bàn tay, bỏ
    edge_margin_px: int = 3
    split: str = "none"                   # "none" (CL-0 gốc) | "watershed" (nút tinh chỉnh)
    shift_search_mm: float = 0.0
    grasp: GraspParams = field(default_factory=GraspParams)


class BackgroundModel:
    """Nền băng trống trong toạ độ ảnh rectified (băng trơn) hoặc canvas tuần hoàn theo toạ độ vật liệu băng (băng texture)."""

    def __init__(self, rows: int, cols: int, res_mm: float, a_min: float, textured: bool = False, period_mm: float = 0.0,
                 b_min: float = 0.0):
        if textured and period_mm <= 0:
            raise ValueError("băng có texture cần period_mm (chu vi băng, mm)")
        self.rows, self.cols, self.res, self.a_min, self.b_min = rows, cols, res_mm, a_min, b_min
        self.meta: dict = {}
        self.textured, self.period_mm = textured, period_mm
        self.Wc = int(round(period_mm / res_mm)) if textured else cols
        if textured and self.Wc < cols:
            raise ValueError("chu vi băng ngắn hơn cửa sổ nhìn")
        self._sum = np.zeros((rows, self.Wc, 3), np.float64)
        self._sq = np.zeros((rows, self.Wc, 3), np.float64)
        self._cnt = np.zeros((rows, self.Wc), np.float64)
        self.mean: Optional[np.ndarray] = None
        self.sigma: Optional[np.ndarray] = None
        self.cov: Optional[np.ndarray] = None

    def _idx(self, s_mm: float) -> np.ndarray:
        if not self.textured:
            return np.arange(self.cols)
        return (np.arange(self.cols) + int(round((self.a_min - s_mm) / self.res))) % self.Wc

    def add_frame(self, plane_img: np.ndarray, s_mm: float, valid: Optional[np.ndarray] = None) -> None:
        idx = self._idx(s_mm)
        v = np.ones((self.rows, self.cols), np.float64) if valid is None else (valid > 0).astype(np.float64)
        P = plane_img.astype(np.float64)
        self._sum[:, idx, :] += P * v[..., None]
        self._sq[:, idx, :] += (P * P) * v[..., None]
        self._cnt[:, idx] += v

    def finalize(self, sigma_floor: float = 3.0, min_count: int = 3) -> None:
        c = np.maximum(self._cnt, 1.0)[..., None]
        mean = self._sum / c
        var = np.maximum(self._sq / c - mean ** 2, 0.0)
        sig = np.sqrt(var).max(axis=2)
        sig = cv2.GaussianBlur(sig.astype(np.float32), (0, 0), 2.0)
        self.mean = mean.astype(np.float32)
        self.sigma = np.maximum(sig, sigma_floor).astype(np.float32)
        self.cov = self._cnt >= min_count
        self._sum = self._sq = self._cnt = None

    def window(self, s_mm: float, extra_shift_px: int = 0):
        idx = self._idx(s_mm)
        if self.textured and extra_shift_px:
            idx = (idx + extra_shift_px) % self.Wc
        return self.mean[:, idx, :], self.sigma[:, idx], self.cov[:, idx]

    def save(self, path: str) -> None:
        import json
        np.savez_compressed(path, mean=self.mean, sigma=self.sigma, cov=self.cov, rows=self.rows, cols=self.cols,
                            res=self.res, a_min=self.a_min, b_min=self.b_min, textured=self.textured, period_mm=self.period_mm,
                            meta=json.dumps(self.meta))

    @staticmethod
    def load(path: str) -> "BackgroundModel":
        import json
        d = np.load(path)
        bg = BackgroundModel(int(d["rows"]), int(d["cols"]), float(d["res"]), float(d["a_min"]), bool(d["textured"]),
                             float(d["period_mm"]), float(d["b_min"]) if "b_min" in d else 0.0)
        bg.meta = json.loads(str(d["meta"])) if "meta" in d else {}
        bg.mean, bg.sigma, bg.cov = d["mean"], d["sigma"], d["cov"]
        bg._sum = bg._sq = bg._cnt = None
        return bg


def build_background(frames: Iterable[Tuple[np.ndarray, float]], rect: Rectifier, params: PerceptionParams,
                     textured: bool = False, period_mm: float = 0.0) -> BackgroundModel:
    """``frames``: dãy (khung camera BGR, s_mm tại thời điểm chụp) của BĂNG TRỐNG. Với băng texture, s phải phủ >= một vòng."""
    bg = BackgroundModel(rect.size[1], rect.size[0], rect.win.res_mm, rect.win.a_min, textured, period_mm, rect.win.b_min)
    valid = rect.valid_mask()
    for fr, s in frames:
        bg.add_frame(rect.rectify(fr), s, valid)
    bg.finalize(params.sigma_floor)
    return bg


def window_of(bg: BackgroundModel):
    """Cửa sổ nhìn từ trên mà nền này được dựng cho (để dựng đúng Rectifier lúc chạy)."""
    from .geometry import Window
    return Window(bg.a_min, bg.a_min + (bg.cols - 1) * bg.res - 1e-6, bg.b_min, bg.b_min + (bg.rows - 1) * bg.res - 1e-6, bg.res)


@dataclass
class Detection:
    a_mm: float                 # điểm kẹp trong W-căn-theo-băng (a gồm cả s tại thời điểm chụp)
    b_mm: float
    theta_deg: float
    width_mm: float
    area_mm2: float
    dt_r_mm: float
    aspect: float
    centroid_ab: Tuple[float, float]
    reject: str = ""
    comp_id: int = 0

    @property
    def ok(self) -> bool:
        return self.reject == ""


@dataclass
class DetectResult:
    dets: List[Detection]
    mask: np.ndarray            # mặt nạ cuối (uint8 0/255) trong ảnh rectified
    plane: np.ndarray           # ảnh rectified (BGR)
    info: dict = field(default_factory=dict)


class Detector:
    def __init__(self, rect: Rectifier, bg: BackgroundModel, params: Optional[PerceptionParams] = None,
                 image_valid: Optional[np.ndarray] = None):
        self.rect, self.bg, self.p = rect, bg, params or PerceptionParams()
        if bg.rows != rect.size[1] or bg.cols != rect.size[0]:
            raise ValueError("nền và cửa sổ rectified khác kích thước; dựng lại nền")
        valid = rect.valid_mask() if image_valid is None else image_valid
        self._valid = valid > 0
        k = max(1, int(round(self.p.edge_margin_px)))
        self._valid_in = cv2.erode(self._valid.astype(np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8)) > 0
        r = self.p.res_mm
        self._k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, int(round(self.p.open_mm / r))) | 1,) * 2)
        self._k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, int(round(self.p.close_mm / r))) | 1,) * 2)

    # ------------------------------------------------------------------ lõi
    def _foreground(self, P: np.ndarray, s_mm: float):
        p = self.p
        shift_px = 0
        mean, sigma, cov = self.bg.window(s_mm)
        if self.bg.textured and p.shift_search_mm > 0:
            shift_px = self._best_shift(P, s_mm)
            if shift_px:
                mean, sigma, cov = self.bg.window(s_mm, shift_px)
        Pf = P.astype(np.float32)
        d = Pf - mean
        use = self._valid & cov
        if p.photometric_comp:
            sub = d[::4, ::4][use[::4, ::4]]
            if sub.shape[0] > 100:
                off = np.median(sub, axis=0)
                d = d - off
        dm = np.abs(d).max(axis=2)
        thr = np.maximum(p.k_sigma * sigma, p.t_min)
        m = (dm > thr) & self._valid_in & cov
        m8 = m.astype(np.uint8) * 255
        m8 = cv2.morphologyEx(m8, cv2.MORPH_OPEN, self._k_open)
        m8 = cv2.morphologyEx(m8, cv2.MORPH_CLOSE, self._k_close)
        return m8, shift_px

    def _best_shift(self, P: np.ndarray, s_mm: float) -> int:
        k = int(round(self.p.shift_search_mm / self.p.res_mm))
        g = cv2.cvtColor(P, cv2.COLOR_BGR2GRAY).astype(np.float32)[::2, ::2]
        best, best_c = 0, None
        for sh in range(-k, k + 1):
            mean, _, cov = self.bg.window(s_mm, sh)
            gb = mean.mean(axis=2)[::2, ::2]
            c = float(np.median(np.abs(g - gb)))
            if best_c is None or c < best_c:
                best, best_c = sh, c
        return best

    def detect(self, frame_bgr: np.ndarray, s_mm: float, exclude: Sequence[Tuple[float, float, float]] = ()) -> DetectResult:
        """``exclude``: danh sách đĩa (a, b, r_mm) trong W-căn-theo-băng (ví dụ quanh đầu kẹp) — thành phần có tâm trong đĩa bị bỏ."""
        p, rect = self.p, self.rect
        if frame_bgr.ndim == 2:
            frame_bgr = cv2.cvtColor(frame_bgr, cv2.COLOR_GRAY2BGR)
        P = rect.rectify(frame_bgr)
        m8, shift_px = self._foreground(P, s_mm)
        n, lab, stats, cent = cv2.connectedComponentsWithStats(m8, connectivity=8)
        res = p.res_mm
        dets: List[Detection] = []
        H, W = m8.shape
        em = p.edge_margin_px
        comps = []
        for i in range(1, n):
            x, y, w, h, area_px = stats[i]
            comps.append((i, x, y, w, h, area_px))
        cid = 0
        for (i, x, y, w, h, area_px) in comps:
            area_mm2 = area_px * res * res
            cid += 1
            base = Detection(0, 0, 0, 0, area_mm2, 0, 0, (0, 0), "", cid)
            cc = cent[i]
            ca, cb = rect.ab_from_px(float(cc[0]), float(cc[1]))
            base.centroid_ab = (ca, cb)
            if area_mm2 < p.min_area_mm2:
                continue                                     # nhiễu hạt: không báo
            touches = x <= em or y <= em or x + w >= W - em or y + h >= H - em
            sub = (lab[y:y + h, x:x + w] == i)
            # ra ngoài vùng ảnh hợp lệ (mép khung camera)
            vin = self._valid_in[y:y + h, x:x + w]
            if touches or (sub & ~vin).any():
                base.reject = "edge"
                base.a_mm, base.b_mm = ca, cb
                dets.append(base)
                continue
            if area_mm2 > p.max_area_mm2:
                base.reject = "area"
                base.a_mm, base.b_mm = ca, cb
                dets.append(base)
                continue
            if any((ca - ea) ** 2 + (cb - eb) ** 2 <= er ** 2 for (ea, eb, er) in exclude):
                base.reject = "arm"
                base.a_mm, base.b_mm = ca, cb
                dets.append(base)
                continue
            pad = 3
            crop = np.pad(sub, pad)
            parts = watershed_split(crop) if p.split == "watershed" else [crop]
            for part in parts:
                cand = analyze_component(part, res, p.grasp)
                if cand is None:
                    continue
                col, row = cand.col - pad + x, cand.row - pad + y
                a, b = rect.ab_from_px(col, row)
                cen_a, cen_b = rect.ab_from_px(x - pad + cand.centroid_ab[0], y - pad + cand.centroid_ab[1])
                dets.append(Detection(a, b, cand.theta_deg, cand.width_mm, cand.area_mm2, cand.dt_r_mm, cand.aspect,
                                      (cen_a, cen_b), cand.reject, cid))
        return DetectResult(dets, m8, P, {"shift_px": shift_px, "n_comp": n - 1})
