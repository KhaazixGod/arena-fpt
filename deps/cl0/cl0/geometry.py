"""Hình học: homography ảnh -> mặt phẳng băng, hệ toạ độ băng, ảnh "nhìn từ trên" (rectified) theo hệ băng.

Quy ước (ghi sẵn để không nhầm dấu):

* W: hệ thế giới = khung đế robot (mm). Mặt băng là mặt phẳng z = ``z_plane_mm`` trong W.
* ``u_hat = (cos phi, sin phi)``: hướng băng chạy, phi tính từ +x của W, ngược chiều kim đồng hồ nhìn từ trên xuống (độ).
  ``v_hat = (-sin phi, cos phi)`` (quay u_hat +90°).
* Toạ độ căn theo băng: ``a = p . u_hat``, ``b = p . v_hat`` (p trong W, gốc là gốc W, KHÔNG phải gốc băng).
* Độ dịch băng ``s(t)`` (mm) dương khi băng chạy theo +u_hat; mốc 0 lúc đặt lại bộ đếm.
  Toạ độ trong hệ băng (vật liệu băng): ``a_b = a - s``, ``b_b = b``  <=>  ``p_b = p_w - s * u_hat``  (đúng công thức §3.2 của kế hoạch).
* Góc kẹp ``theta``: phương của trục khép hai má kẹp so với u_hat, ngược chiều kim đồng hồ, tính theo độ, mod 180.
  Yaw trong W = ``phi + theta`` (mod 180).
* Ảnh rectified: cột = a, hàng = b (tâm điểm ảnh tại a = a_min + col*res, b = b_min + row*res), nên góc tính trong
  (cột, hàng) trùng với góc theta (không đổi dấu).
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from typing import Optional, Sequence, Tuple

import cv2
import numpy as np


def wrap180(deg: float) -> float:
    """Gói góc của một trục (đối xứng 180°) về [0, 180)."""
    return float(deg % 180.0)


def wrap_axis_diff(deg: float) -> float:
    """Hiệu hai góc trục, gói về (-90, 90]."""
    return float((deg + 90.0) % 180.0 - 90.0)


def unit(phi_deg: float) -> np.ndarray:
    r = math.radians(phi_deg)
    return np.array([math.cos(r), math.sin(r)])


def perp(phi_deg: float) -> np.ndarray:
    r = math.radians(phi_deg)
    return np.array([-math.sin(r), math.cos(r)])


def to_belt_frame(p_w_xy: np.ndarray, s_mm: float, phi_deg: float) -> np.ndarray:
    """p_b = p_w - s * u_hat (vector 2 chiều hoặc (N,2))."""
    return np.asarray(p_w_xy, float) - s_mm * unit(phi_deg)


def to_world_frame(p_b_xy: np.ndarray, s_mm: float, phi_deg: float) -> np.ndarray:
    """p_w = p_b + s * u_hat."""
    return np.asarray(p_b_xy, float) + s_mm * unit(phi_deg)


@dataclass
class PlaneCalib:
    """Kết quả hiệu chuẩn camera -> mặt băng + hướng băng. Lưu/đọc JSON (``calib.json``)."""
    H: list                        # 3x3, pixel (u,v,1) -> W (X,Y,1) [mm] trên mặt phẳng z = z_plane_mm
    z_plane_mm: float = 0.0
    belt_dir_deg: float = 0.0
    mm_per_step: float = 0.0       # 0 = chưa biết
    image_size: Tuple[int, int] = (640, 480)
    rms_mm: float = 0.0            # sai số khớp trên các điểm hiệu chuẩn
    loo_rms_mm: float = 0.0        # leave-one-out (ước lượng trung thực hơn)
    n_points: int = 0
    note: str = ""
    latency_s: float = 0.0         # độ trễ ảnh<->băng đo được bằng `calibrate belt` (0 = chưa đo); chép vào camera.latency_s
    method: str = "points"         # "points" (chạm từng điểm) | "board" (bàn cờ + vài điểm chạm)
    touch_rms_mm: float = 0.0      # sai số khớp rigid board->robot trên các điểm chạm (chỉ với method = "board")
    n_touch: int = 0

    def H_np(self) -> np.ndarray:
        return np.asarray(self.H, float).reshape(3, 3)

    def pix_to_world(self, uv: np.ndarray) -> np.ndarray:
        uv = np.asarray(uv, float).reshape(-1, 2)
        P = np.c_[uv, np.ones(len(uv))] @ self.H_np().T
        return P[:, :2] / P[:, 2:3]

    def world_to_pix(self, xy: np.ndarray) -> np.ndarray:
        xy = np.asarray(xy, float).reshape(-1, 2)
        Hi = np.linalg.inv(self.H_np())
        P = np.c_[xy, np.ones(len(xy))] @ Hi.T
        return P[:, :2] / P[:, 2:3]

    def mm_per_pixel_at(self, uv: Sequence[float]) -> float:
        """Kích thước điểm ảnh (mm/px) quanh uv, trung bình theo hai trục."""
        u, v = uv
        P = self.pix_to_world(np.array([[u, v], [u + 1, v], [u, v + 1]]))
        return float(0.5 * (np.linalg.norm(P[1] - P[0]) + np.linalg.norm(P[2] - P[0])))

    def to_json(self) -> str:
        d = asdict(self)
        d["H"] = np.asarray(self.H, float).reshape(3, 3).tolist()
        return json.dumps(d, indent=2, ensure_ascii=False)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @staticmethod
    def load(path: str) -> "PlaneCalib":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        d["image_size"] = tuple(d.get("image_size", (640, 480)))
        return PlaneCalib(**d)


def fit_plane_homography(px: np.ndarray, xy: np.ndarray, z_plane_mm: float = 0.0, ransac_thresh_mm: float = 0.0,
                         image_size=(640, 480)) -> PlaneCalib:
    """Khớp homography pixel -> W(x,y) từ các cặp (pixel, toạ độ mm). Cần >= 4 cặp, nên >= 8 phân bố khắp vùng nhặt.
    Trả về PlaneCalib (belt_dir_deg để mặc định, điền bằng fit_belt_motion)."""
    px = np.asarray(px, np.float64).reshape(-1, 2)
    xy = np.asarray(xy, np.float64).reshape(-1, 2)
    n = len(px)
    if n < 4:
        raise ValueError("cần ít nhất 4 điểm hiệu chuẩn")
    method = cv2.RANSAC if (ransac_thresh_mm > 0 and n >= 8) else 0
    H, _ = cv2.findHomography(px, xy, method, ransac_thresh_mm if method else 0)
    if H is None:
        raise ValueError("findHomography thất bại (điểm thẳng hàng?)")
    calib = PlaneCalib(H=H.tolist(), z_plane_mm=float(z_plane_mm), image_size=tuple(image_size), n_points=n)
    pred = calib.pix_to_world(px)
    calib.rms_mm = float(np.sqrt(np.mean(np.sum((pred - xy) ** 2, axis=1))))
    if n >= 6:
        errs = []
        for i in range(n):
            m = np.ones(n, bool)
            m[i] = False
            Hi, _ = cv2.findHomography(px[m], xy[m], 0)
            if Hi is None:
                continue
            P = np.array([px[i, 0], px[i, 1], 1.0]) @ Hi.T
            errs.append(np.sum((P[:2] / P[2] - xy[i]) ** 2))
        calib.loo_rms_mm = float(np.sqrt(np.mean(errs))) if errs else 0.0
    return calib


@dataclass
class RigidFit:
    """dst ≈ s·M·src + t, với M = R (quay) hoặc R·diag(1,−1) (quay + phản xạ, khi ``reflected``)."""
    M: np.ndarray
    t: np.ndarray
    s: float
    rms: float
    reflected: bool

    def apply(self, xy: np.ndarray) -> np.ndarray:
        return (self.s * (self.M @ np.asarray(xy, float).reshape(-1, 2).T)).T + self.t


def _umeyama(src: np.ndarray, dst: np.ndarray, allow_scale: bool):
    mu_s, mu_d = src.mean(axis=0), dst.mean(axis=0)
    A, B = src - mu_s, dst - mu_d
    U, S, Vt = np.linalg.svd(B.T @ A)
    D = np.diag([1.0, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    sc = float(np.trace(np.diag(S) @ D) / np.sum(A ** 2)) if allow_scale else 1.0
    t = mu_d - sc * R @ mu_s
    pred = (sc * (R @ src.T)).T + t
    return R, t, sc, float(np.sqrt(np.mean(np.sum((pred - dst) ** 2, axis=1))))


def fit_rigid_2d(src: np.ndarray, dst: np.ndarray, allow_scale: bool = False, allow_reflection: bool = False) -> RigidFit:
    """Khớp dst ≈ s·M·src + t (Umeyama 2D). ``allow_reflection``: thử cả bản phản xạ gương và chọn bản sai số nhỏ hơn
    (cần khi hệ toạ độ bàn cờ có chiều ngược hệ W nhìn từ trên xuống, hoặc ảnh camera bị lật gương)."""
    src = np.asarray(src, float).reshape(-1, 2)
    dst = np.asarray(dst, float).reshape(-1, 2)
    if len(src) < 3:
        raise ValueError("cần ít nhất 3 điểm chạm để khớp phép biến đổi cứng")
    R, t, sc, rms = _umeyama(src, dst, allow_scale)
    best = RigidFit(R, t, sc, rms, False)
    if allow_reflection:
        F = np.diag([1.0, -1.0])
        R2, t2, sc2, rms2 = _umeyama(src @ F, dst, allow_scale)
        if rms2 < rms:
            best = RigidFit(R2 @ F, t2, sc2, rms2, True)
    return best


def calib_from_board(px_corners: np.ndarray, board_xy: np.ndarray, touch_board_xy: np.ndarray, touch_world_xy: np.ndarray,
                     z_plane_mm: float, image_size=(640, 480), allow_scale: bool = False) -> PlaneCalib:
    """Hiệu chuẩn bằng bàn cờ đặt trên băng đứng yên.

    * ``px_corners`` (N,2) và ``board_xy`` (N,2): pixel của các góc bàn cờ và toạ độ mm của chúng trong hệ bàn cờ (in chính xác).
    * ``touch_board_xy`` (K,2), ``touch_world_xy`` (K,2): K >= 3 góc mà TCP đã chạm, toạ độ trong hệ bàn cờ và toạ độ W do FK cho.
    Homography cuối cùng đi pixel -> bàn cờ -> W. Sai số FK trơn quanh vùng chạm được hấp thụ vào phép biến đổi cứng.
    Cho phép phản xạ gương (hệ bàn cờ (cột, hàng) ngược chiều W nhìn từ trên xuống là bình thường).
    """
    fit = fit_rigid_2d(touch_board_xy, touch_world_xy, allow_scale=allow_scale, allow_reflection=True)
    world = fit.apply(board_xy)
    cal = fit_plane_homography(px_corners, world, z_plane_mm=z_plane_mm, image_size=image_size)
    cal.method, cal.touch_rms_mm, cal.n_touch = "board", fit.rms, len(touch_board_xy)
    cal.note = f"board: scale={fit.s:.4f}, reflected={fit.reflected}"
    return cal


def fit_belt_motion(tracks: Sequence[Tuple[np.ndarray, np.ndarray]]) -> Tuple[float, float, float]:
    """Khớp hướng băng và mm/xung từ các quỹ đạo của vạch đánh dấu.

    ``tracks``: danh sách (steps (K,), xy (K,2)) — mỗi quỹ đạo là cùng một vạch được quan sát ở K số xung khác nhau
    (xy tính bằng mm trong W qua homography). Trả về (belt_dir_deg, mm_per_step, lateral_rms_mm).
    """
    C, S = [], []
    for steps, xy in tracks:
        steps = np.asarray(steps, float)
        xy = np.asarray(xy, float).reshape(-1, 2)
        C.append(xy - xy.mean(axis=0))
        S.append(steps - steps.mean())
    C, S = np.vstack(C), np.concatenate(S)
    # hướng chính của dịch chuyển: vector riêng lớn nhất; dấu sao cho xung tăng <=> dọc +u_hat
    w, V = np.linalg.eigh(C.T @ C)
    d = V[:, 1]
    if float(np.dot(C @ d, S)) < 0:
        d = -d
    along = C @ d
    m = float(np.dot(along, S) / np.dot(S, S))      # mm / xung
    lat = C @ np.array([-d[1], d[0]])
    return float(math.degrees(math.atan2(d[1], d[0]))), m, float(np.sqrt(np.mean(lat ** 2)))


@dataclass
class Window:
    """Cửa sổ nhìn từ trên (mm, toạ độ căn theo băng a/b, gốc là gốc W) và độ phân giải."""
    a_min: float
    a_max: float
    b_min: float
    b_max: float
    res_mm: float = 0.5

    @property
    def cols(self) -> int:
        return int(math.ceil((self.a_max - self.a_min) / self.res_mm)) + 1

    @property
    def rows(self) -> int:
        return int(math.ceil((self.b_max - self.b_min) / self.res_mm)) + 1


class Rectifier:
    """Warp khung camera -> ảnh nhìn từ trên căn theo băng (cột = a, hàng = b)."""

    def __init__(self, calib: PlaneCalib, window: Window):
        self.calib, self.win = calib, window
        c, s = math.cos(math.radians(calib.belt_dir_deg)), math.sin(math.radians(calib.belt_dir_deg))
        Rm = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
        r = window.res_mm
        Sm = np.array([[1 / r, 0.0, -window.a_min / r], [0.0, 1 / r, -window.b_min / r], [0.0, 0.0, 1.0]])
        self.M = Sm @ Rm @ calib.H_np()
        self.size = (window.cols, window.rows)

    def rectify(self, frame: np.ndarray, interp: int = cv2.INTER_LINEAR) -> np.ndarray:
        return cv2.warpPerspective(frame, self.M, self.size, flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    def valid_mask(self, image_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Điểm ảnh rectified nằm trong khung camera (uint8 0/255)."""
        w, h = image_size or self.calib.image_size
        ones = np.full((h, w), 255, np.uint8)
        return cv2.warpPerspective(ones, self.M, self.size, flags=cv2.INTER_NEAREST, borderValue=0)

    def ab_from_px(self, col: float, row: float) -> Tuple[float, float]:
        return self.win.a_min + col * self.win.res_mm, self.win.b_min + row * self.win.res_mm

    def px_from_ab(self, a: float, b: float) -> Tuple[float, float]:
        return (a - self.win.a_min) / self.win.res_mm, (b - self.win.b_min) / self.win.res_mm

    def ab_to_world(self, a: float, b: float) -> np.ndarray:
        phi = self.calib.belt_dir_deg
        return a * unit(phi) + b * perp(phi)

    def world_to_ab(self, xy: np.ndarray) -> Tuple[float, float]:
        phi = self.calib.belt_dir_deg
        xy = np.asarray(xy, float)
        return float(xy @ unit(phi)), float(xy @ perp(phi))


def auto_window(calib: PlaneCalib, res_mm: float = 0.5, shrink_mm: float = 10.0,
                a_range: Optional[Tuple[float, float]] = None, b_range: Optional[Tuple[float, float]] = None) -> Window:
    """Cửa sổ lớn nhất căn theo băng nằm trong ảnh camera (hình bao của 4 góc ảnh chiếu xuống mặt băng, co lại shrink_mm).
    Có thể ép a_range / b_range (giao với phần nhìn thấy)."""
    w, h = calib.image_size
    corners = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], float)
    W = calib.pix_to_world(corners)
    phi = calib.belt_dir_deg
    a, b = W @ unit(phi), W @ perp(phi)
    # hình chữ nhật căn trục lớn nhất nằm trong tứ giác: xấp xỉ bằng cận trong (median các cặp cạnh đối)
    a_lo, a_hi = float(np.sort(a)[1]), float(np.sort(a)[2])
    b_lo, b_hi = float(np.sort(b)[1]), float(np.sort(b)[2])
    a_lo, a_hi, b_lo, b_hi = a_lo + shrink_mm, a_hi - shrink_mm, b_lo + shrink_mm, b_hi - shrink_mm
    if a_range:
        a_lo, a_hi = max(a_lo, a_range[0]), min(a_hi, a_range[1])
    if b_range:
        b_lo, b_hi = max(b_lo, b_range[0]), min(b_hi, b_range[1])
    if a_hi <= a_lo or b_hi <= b_lo:
        raise ValueError("cửa sổ rỗng: kiểm tra homography hoặc a_range/b_range")
    return Window(a_lo, a_hi, b_lo, b_hi, res_mm)
