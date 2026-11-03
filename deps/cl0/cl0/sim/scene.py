"""Cảnh tổng hợp: băng chuyền + vật + camera pinhole, để thử CL-0 khi chưa có robot.

Chỉ kiểm LOGIC (hệ toạ độ, dấu, thời gian, cắt/ghép mặt nạ, điểm kẹp...). Không nói gì về tỉ lệ thành công ngoài đời:
ánh sáng, bóng đổ, phản xạ, lệch hiệu chuẩn thật, vật trượt... đều đơn giản hoá hoặc không có.

Quy ước góc/hệ toạ độ theo geometry.py (toạ độ căn theo băng (a, b); cột = a, hàng = b; góc từ +a sang +b).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

OBJ_RES = 0.5          # mm / điểm ảnh của bitmap vật
BELT_BGR = (46, 43, 41)


# ----------------------------------------------------------------------------------------------- vật
@dataclass
class SimObject:
    name: str
    mask: np.ndarray            # uint8 0/255, kích thước (n,n), gốc vật tại tâm ảnh
    color: np.ndarray           # (n,n,3) uint8
    height_mm: float
    gx: np.ndarray = None       # gradient của mặt nạ làm mịn (để tính pháp tuyến)
    gy: np.ndarray = None

    def __post_init__(self):
        sm = cv2.GaussianBlur(self.mask.astype(np.float32) / 255.0, (0, 0), 1.2 / OBJ_RES)
        self.gx = cv2.Sobel(sm, cv2.CV_32F, 1, 0, ksize=3)
        self.gy = cv2.Sobel(sm, cv2.CV_32F, 0, 1, ksize=3)

    @property
    def n(self) -> int:
        return self.mask.shape[0]

    def radius_mm(self) -> float:
        ys, xs = np.nonzero(self.mask)
        c = self.n // 2
        return float(np.max(np.hypot(xs - c, ys - c))) * OBJ_RES

    def _px(self, x_mm: float, y_mm: float) -> Tuple[int, int]:
        c = self.n // 2
        return int(round(c + x_mm / OBJ_RES)), int(round(c + y_mm / OBJ_RES))

    def contains_local(self, x_mm: float, y_mm: float) -> bool:
        px, py = self._px(x_mm, y_mm)
        return 0 <= px < self.n and 0 <= py < self.n and self.mask[py, px] > 0

    def normal_local(self, x_mm: float, y_mm: float) -> Optional[np.ndarray]:
        px, py = self._px(x_mm, y_mm)
        if not (0 <= px < self.n and 0 <= py < self.n):
            return None
        g = np.array([self.gx[py, px], self.gy[py, px]])
        nrm = np.linalg.norm(g)
        return None if nrm < 1e-6 else -g / nrm      # hướng ra ngoài


def _shaded(mask: np.ndarray, color: Sequence[int]) -> np.ndarray:
    n = mask.shape[0]
    img = np.zeros((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    shade = 1.0 + 0.10 * (xx - n / 2) / n - 0.08 * (yy - n / 2) / n
    for c in range(3):
        img[..., c] = color[c] * shade
    img = np.clip(img, 0, 255).astype(np.uint8)
    img[mask == 0] = 0
    return img


def _canvas(extent_mm: float) -> Tuple[np.ndarray, int]:
    n = int(extent_mm / OBJ_RES) | 1
    return np.zeros((n, n), np.uint8), n // 2


def disc(d: float, color=(40, 150, 235), name: str = "", height: float = 25.0) -> SimObject:
    m, c = _canvas(d + 8)
    cv2.circle(m, (c, c), int(round(d / 2 / OBJ_RES)), 255, -1)
    return SimObject(name or f"disc{int(d)}", m, _shaded(m, color), height)


def box(l: float, w: float, color=(60, 200, 90), name: str = "", height: float = 30.0) -> SimObject:
    """Hộp: dài l theo trục x của vật, rộng w theo trục y."""
    m, c = _canvas(max(l, w) * 1.5 + 8)
    cv2.rectangle(m, (c - int(l / 2 / OBJ_RES), c - int(w / 2 / OBJ_RES)), (c + int(l / 2 / OBJ_RES), c + int(w / 2 / OBJ_RES)), 255, -1)
    return SimObject(name or f"box{int(l)}x{int(w)}", m, _shaded(m, color), height)


def ellipse(l: float, w: float, color=(200, 90, 60), name: str = "", height: float = 28.0) -> SimObject:
    m, c = _canvas(max(l, w) + 8)
    cv2.ellipse(m, (c, c), (int(l / 2 / OBJ_RES), int(w / 2 / OBJ_RES)), 0, 0, 360, 255, -1)
    return SimObject(name or f"ell{int(l)}x{int(w)}", m, _shaded(m, color), height)


def l_shape(l: float, t: float, color=(80, 90, 230), name: str = "", height: float = 30.0) -> SimObject:
    m, c = _canvas(l * 1.6 + 8)
    h = int(l / 2 / OBJ_RES)
    tt = int(t / OBJ_RES)
    cv2.rectangle(m, (c - h, c - h), (c - h + tt, c + h), 255, -1)
    cv2.rectangle(m, (c - h, c + h - tt), (c + h, c + h), 255, -1)
    return SimObject(name or f"L{int(l)}", m, _shaded(m, color), height)


def ring(d_out: float, d_in: float, color=(220, 190, 70), name: str = "", height: float = 22.0) -> SimObject:
    m, c = _canvas(d_out + 8)
    cv2.circle(m, (c, c), int(round(d_out / 2 / OBJ_RES)), 255, -1)
    cv2.circle(m, (c, c), int(round(d_in / 2 / OBJ_RES)), 0, -1)
    return SimObject(name or f"ring{int(d_out)}", m, _shaded(m, color), height)


def mug(d_out: float, d_in: float, color=(170, 120, 230), name: str = "", height: float = 40.0) -> SimObject:
    """Cốc có quai: vòng + quai hình tai bên +x."""
    m, c = _canvas(d_out * 2.0 + 8)
    r = int(round(d_out / 2 / OBJ_RES))
    cv2.circle(m, (c, c), r, 255, -1)
    cv2.circle(m, (c, c), int(round(d_in / 2 / OBJ_RES)), 0, -1)
    hand = np.zeros_like(m)
    cv2.ellipse(hand, (c + r, c), (int(0.45 * d_out / OBJ_RES), int(0.32 * d_out / OBJ_RES)), 0, 0, 360, 255, int(4 / OBJ_RES))
    hole = np.zeros_like(m)
    cv2.circle(hole, (c, c), r - 2, 255, -1)
    hand[hole > 0] = 0
    m = np.maximum(m, hand)
    return SimObject(name or f"mug{int(d_out)}", m, _shaded(m, color), height)


def plate(l: float, w: float, color=(190, 190, 200), name: str = "", height: float = 3.0) -> SimObject:
    return box(l, w, color, name or f"plate{int(l)}x{int(w)}", height)


def lowcon(d: float, name: str = "", height: float = 25.0) -> SimObject:
    return disc(d, (int(BELT_BGR[0] + 28), int(BELT_BGR[1] + 26), int(BELT_BGR[2] + 24)), name or f"lowcon{int(d)}", height)


def default_library() -> dict:
    return {
        "disc30": disc(30), "box25x50": box(50, 25), "ellipse28x48": ellipse(48, 28), "L40": l_shape(40, 14),
        "ring34": ring(34, 22), "mug30": mug(30, 20), "plate20x45": plate(45, 20), "lowcon30": lowcon(30),
        "disc22": disc(22, (230, 230, 60)), "box60x60": box(60, 60, (200, 60, 200), "box60x60"),
        "bar18x60": box(60, 18, (60, 220, 220), "bar18x60"),
    }


@dataclass
class Placed:
    obj: SimObject
    a_b: float            # vị trí trong hệ băng (vật liệu): a_b = a - s
    b: float
    theta_deg: float      # góc của trục x vật trong (a, b), từ +a sang +b
    attached: bool = False   # đang trong kẹp
    world_a: float = 0.0     # khi attached: vị trí thế giới (a, b) đi theo TCP
    world_b: float = 0.0

    def center_ab(self, s_mm: float) -> Tuple[float, float]:
        return (self.world_a, self.world_b) if self.attached else (self.a_b + s_mm, self.b)

    def to_local(self, a: float, b: float, s_mm: float) -> Tuple[float, float]:
        ca, cb = self.center_ab(s_mm)
        th = math.radians(self.theta_deg)
        dx, dy = a - ca, b - cb
        return math.cos(th) * dx + math.sin(th) * dy, -math.sin(th) * dx + math.cos(th) * dy

    def contains(self, a: float, b: float, s_mm: float) -> bool:
        return self.obj.contains_local(*self.to_local(a, b, s_mm))


# ----------------------------------------------------------------------------------------------- camera
def look_at_homography(cam_pos: Sequence[float], target: Sequence[float], f_px: float, size=(640, 480),
                       z_plane: float = 0.0, up_hint=(1.0, 0.0, 0.0), flip: bool = False) -> np.ndarray:
    """Homography W(x,y) -> pixel cho mặt phẳng z = z_plane, camera pinhole đặt tại cam_pos nhìn về target."""
    C = np.asarray(cam_pos, float)
    T = np.asarray(target, float)
    zc = (T - C) / np.linalg.norm(T - C)
    xc = np.cross(zc, np.asarray(up_hint, float))
    xc /= np.linalg.norm(xc)
    yc = np.cross(zc, xc)
    R = np.stack([xc, yc, zc])                # p_cam = R (p - C)
    K = np.array([[f_px, 0, size[0] / 2.0], [0, f_px, size[1] / 2.0], [0, 0, 1.0]])
    Hm = K @ np.stack([R[:, 0], R[:, 1], R[:, 2] * z_plane - R @ C], axis=1)
    if flip:
        F = np.array([[-1.0, 0, size[0] - 1], [0, 1.0, 0], [0, 0, 1.0]])
        Hm = F @ Hm
    return Hm / Hm[2, 2]


@dataclass
class SimCameraCfg:
    size: Tuple[int, int] = (640, 480)
    fps: float = 15.0
    latency_s: float = 0.10
    noise_sigma: float = 2.0
    blur_px: float = 0.8
    vignette: float = 0.12
    gain_jitter: float = 0.01
    canvas_res_mm: float = 1.0


class SceneRenderer:
    """Dựng khung camera giả từ trạng thái thế giới."""

    def __init__(self, H_wp: np.ndarray, belt_dir_deg: float, cam: SimCameraCfg, belt_texture: Optional[np.ndarray] = None,
                 texture_period_mm: float = 0.0, seed: int = 0):
        self.H_wp, self.phi, self.cam = H_wp, belt_dir_deg, cam
        self.rng = np.random.default_rng(seed)
        self.texture, self.period = belt_texture, texture_period_mm
        w, h = cam.size
        Hi = np.linalg.inv(H_wp)
        corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], float) @ Hi.T
        xy = corners[:, :2] / corners[:, 2:3]
        c, s = math.cos(math.radians(belt_dir_deg)), math.sin(math.radians(belt_dir_deg))
        a = xy @ np.array([c, s])
        b = xy @ np.array([-s, c])
        m = 40.0
        self.a0, self.a1, self.b0, self.b1 = a.min() - m, a.max() + m, b.min() - m, b.max() + m
        r = cam.canvas_res_mm
        self.r = r
        self.cols = int(math.ceil((self.a1 - self.a0) / r))
        self.rows = int(math.ceil((self.b1 - self.b0) / r))
        # canvas px -> W -> camera pixel
        u, v = np.array([c, s]), np.array([-s, c])
        A = np.array([[r * u[0], r * v[0], self.a0 * u[0] + self.b0 * v[0]],
                      [r * u[1], r * v[1], self.a0 * u[1] + self.b0 * v[1]],
                      [0, 0, 1.0]])
        self.M = H_wp @ A
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(xx - w / 2, yy - h / 2) / np.hypot(w / 2, h / 2)
        self.vig = (1.0 - cam.vignette * d ** 2).astype(np.float32)[..., None]
        self.gain = 1.0
        self._base = np.empty((self.rows, self.cols, 3), np.uint8)
        self._base[:] = BELT_BGR

    def _belt_canvas(self, s_mm: float) -> np.ndarray:
        if self.texture is None:
            return self._base.copy()
        # texture: (rows_t, Wc, 3) tuần hoàn theo toạ độ vật liệu; canvas cột c <-> a = a0 + c*r, a_b = a - s
        Wc = self.texture.shape[1]
        idx = (np.floor((self.a0 + np.arange(self.cols) * self.r - s_mm) / self.r).astype(int)) % Wc
        rows_t = self.texture.shape[0]
        out = np.empty((self.rows, self.cols, 3), np.uint8)
        out[:] = BELT_BGR
        # căn theo b: texture phủ b từ b0 trở đi
        n = min(rows_t, self.rows)
        out[:n] = self.texture[:n][:, idx]
        return out

    def render(self, s_mm: float, objects: Sequence[Placed], marks: Sequence[tuple] = (),
               gain: Optional[float] = None) -> np.ndarray:
        canvas = self._belt_canvas(s_mm)
        r = self.r
        for po in objects:
            ca, cb = po.center_ab(s_mm)
            self._blit(canvas, po, ca, cb)
        for m in marks:                          # đầu kẹp / liên kết cánh tay vẽ đơn giản
            if m[0] == "circle":
                _, a, b, rad, col = m
                cv2.circle(canvas, (int(round((a - self.a0) / r)), int(round((b - self.b0) / r))), int(rad / r), col, -1)
            elif m[0] == "checker":
                self._draw_checker(canvas, *m[1:])
            elif m[0] == "line":
                _, a1, b1, a2, b2, thick, col = m
                cv2.line(canvas, (int(round((a1 - self.a0) / r)), int(round((b1 - self.b0) / r))),
                         (int(round((a2 - self.a0) / r)), int(round((b2 - self.b0) / r))), col, max(1, int(thick / r)))
        img = cv2.warpPerspective(canvas, self.M, self.cam.size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        if self.cam.blur_px > 0:
            img = cv2.GaussianBlur(img, (0, 0), self.cam.blur_px)
        g = self.gain if gain is None else gain
        img = img.astype(np.float32) * self.vig * g
        img += self.rng.normal(0, self.cam.noise_sigma, img.shape).astype(np.float32)
        return np.clip(img, 0, 255).astype(np.uint8)

    def _draw_checker(self, canvas: np.ndarray, a0: float, b0: float, theta_deg: float, nx: int, ny: int, sq: float) -> None:
        """Bàn cờ nx × ny ô (vuông, cạnh sq mm), gốc (a0, b0) trong hệ băng, góc theta (trục x của bàn cờ trong (a, b)); viền trắng 1 ô."""
        r = self.r
        c, s = math.cos(math.radians(theta_deg)), math.sin(math.radians(theta_deg))

        def P(x, y):                                          # toạ độ bàn cờ [mm] -> canvas, đơn vị 1/16 px (sub-pixel)
            a, b = a0 + c * x - s * y, b0 + s * x + c * y
            return [int(round((a - self.a0) / r * 16)), int(round((b - self.b0) / r * 16))]

        quiet = np.array([P(-sq, -sq), P(nx * sq + sq, -sq), P(nx * sq + sq, ny * sq + sq), P(-sq, ny * sq + sq)], np.int32)
        cv2.fillPoly(canvas, [quiet], (235, 235, 235), lineType=cv2.LINE_AA, shift=4)
        for i in range(nx):
            for j in range(ny):
                if (i + j) % 2 == 0:
                    q = np.array([P(i * sq, j * sq), P((i + 1) * sq, j * sq), P((i + 1) * sq, (j + 1) * sq), P(i * sq, (j + 1) * sq)], np.int32)
                    cv2.fillPoly(canvas, [q], (25, 25, 25), lineType=cv2.LINE_AA, shift=4)

    def _blit(self, canvas: np.ndarray, po: Placed, ca: float, cb: float) -> None:
        obj = po.obj
        r = self.r
        th = math.radians(po.theta_deg)
        sc = OBJ_RES / r
        c, s = math.cos(th) * sc, math.sin(th) * sc
        n = obj.n
        cx = (ca - self.a0) / r
        cy = (cb - self.b0) / r
        half = n / 2.0 * sc * 1.5
        x0, x1 = int(max(0, math.floor(cx - half))), int(min(self.cols, math.ceil(cx + half)))
        y0, y1 = int(max(0, math.floor(cy - half))), int(min(self.rows, math.ceil(cy + half)))
        if x1 <= x0 or y1 <= y0:
            return
        # bitmap px (i,j) -> canvas px:  [c -s; s c] (p - n/2) + (cx, cy)
        M = np.array([[c, -s, cx - (c * (n // 2) - s * (n // 2)) - x0],
                      [s, c, cy - (s * (n // 2) + c * (n // 2)) - y0]], np.float64)
        sz = (x1 - x0, y1 - y0)
        col = cv2.warpAffine(obj.color, M, sz, flags=cv2.INTER_LINEAR, borderValue=0)
        al = cv2.warpAffine(obj.mask, M, sz, flags=cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255.0
        roi = canvas[y0:y1, x0:x1].astype(np.float32)
        # bóng đổ nhẹ
        sh = np.roll(al, (2, 2), axis=(0, 1))
        sh = cv2.GaussianBlur(sh, (0, 0), 2.0)
        roi *= (1 - 0.25 * sh)[..., None]
        roi = roi * (1 - al[..., None]) + col.astype(np.float32) * al[..., None]
        canvas[y0:y1, x0:x1] = np.clip(roi, 0, 255).astype(np.uint8)


def make_belt_texture(rows: int, period_mm: float, res_mm: float, seed: int = 3, contrast: float = 14.0) -> np.ndarray:
    """Texture tuần hoàn theo hướng băng (cột), dùng để thử bù độ dịch."""
    rng = np.random.default_rng(seed)
    Wc = int(round(period_mm / res_mm))
    base = rng.normal(0, 1, (rows // 8 + 1, Wc // 8 + 1)).astype(np.float32)
    base[:, -1] = base[:, 0]
    big = cv2.resize(base, (Wc, rows), interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), 3)
    big = big / (np.abs(big).max() + 1e-6)
    tex = np.empty((rows, Wc, 3), np.float32)
    for k in range(3):
        tex[..., k] = BELT_BGR[k] + contrast * big
    return np.clip(tex, 0, 255).astype(np.uint8)
