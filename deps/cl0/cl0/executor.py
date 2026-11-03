"""Bộ thực thi bám băng DÙNG CHUNG (dạng I2 của §3.2) cho CL-0 và cho chính sách học ở các giai đoạn sau.

Đầu vào mỗi bước: mục tiêu trong HỆ BĂNG (a_b, b, góc khép θ so với û) + độ cao tham chiếu; đầu ra: góc khớp lệnh.
    p_w,lệnh(t_x) = p_b,mục tiêu + s(t_x)·û          (đúng p_w,EE(t_img) + a + (s(t_x) − s(t_img))·û khi a = p_b,mục tiêu − p_b,EE(t_img))
Các thành phần:
  * bộ lọc tới hạn bậc hai TRONG HỆ BĂNG (mục tiêu đổi liên tục mà không giật), có chặn tốc độ;
  * ``lead_s``: dẫn trước bù trễ cánh tay (đo bằng ``python -m cl0.calibrate lag``);
  * tích phân bù ``lag_ki``: cộng thêm vào lệnh phần chênh giữa lệnh-gốc và vị trí ĐO ĐƯỢC (FK của khớp đọc về) khi bộ lọc đã gần tĩnh.
    Nó bù trễ servo còn sót, võng trọng lực của vai/khuỷu và tự theo đổi tốc độ băng. Tắt bằng ``lag_ki = 0``;
  * IK số (LM) khởi động nóng từ lệnh trước, chặn tốc độ khớp ở đầu ra.
Nếu dùng cho chính sách học (I2), phải dùng ĐÚNG module này với cùng tham số để so công bằng (xem README_CL0.md).
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .config import Config
from .geometry import perp, unit
from .kinematics import SO101Kinematics


class _Filt:
    """Bộ lọc tới hạn bậc hai x'' = w²(ref − x) − 2w x' có chặn |x'| <= vmax (vô hướng hoặc vector)."""

    def __init__(self, x, v, omega: float, vmax: float):
        self.x = np.array(x, float)
        self.v = np.array(v, float)
        self.w, self.vmax = omega, vmax

    def step(self, ref, dt: float):
        ref = np.asarray(ref, float)
        a = self.w ** 2 * (ref - self.x) - 2 * self.w * self.v
        self.v = self.v + a * dt
        sp = float(np.linalg.norm(self.v))
        if sp > self.vmax:
            self.v *= self.vmax / sp
        self.x = self.x + self.v * dt
        return self.x


class BeltExecutor:
    def __init__(self, cfg: Config, kin: SO101Kinematics, phi_deg: float, z_belt_mm: float):
        self.cfg, self.kin = cfg, kin
        self.phi, self.zb = phi_deg, z_belt_mm
        self.u, self.v = unit(phi_deg), perp(phi_deg)
        self.q_last = np.asarray(cfg.robot.home_q_deg, float).copy()
        self.fxy: Optional[_Filt] = None
        self.fz: Optional[_Filt] = None
        self.fth: Optional[_Filt] = None
        self.int_xy = np.zeros(2)
        self.int_z = 0.0
        self.ik_fail_t = 0.0
        self._last_full_ik = -1e9

    # ------------------------------------------------------------------------------------------------ vòng đời
    def reset(self, q_deg: Optional[np.ndarray] = None) -> None:
        if q_deg is not None:
            self.q_last = np.asarray(q_deg, float).copy()
        self.fxy = self.fz = self.fth = None
        self.int_xy = np.zeros(2)
        self.int_z = 0.0
        self.ik_fail_t = 0.0
        self._last_full_ik = -1e9

    @property
    def started(self) -> bool:
        return self.fxy is not None

    def start(self, tcp: dict, s_now: float, sdot: float) -> None:
        """Khởi tạo các bộ lọc tại TCP đo được (đang đứng yên trong hệ thế giới => vận tốc hệ băng = −ṡ)."""
        ex = self.cfg.executor
        self.fxy = _Filt([tcp["a"] - s_now, tcp["b"]], [-sdot, 0.0], ex.omega_xy, ex.vmax_xy)
        self.fz = _Filt(tcp["z"], 0.0, ex.omega_z, ex.vmax_z)
        self.fth = _Filt(tcp["theta"], 0.0, ex.omega_yaw, ex.vmax_yaw)
        self.int_xy = np.zeros(2)
        self.int_z = 0.0
        self.ik_fail_t = 0.0

    def set_q_last(self, q: np.ndarray) -> None:
        self.q_last = np.asarray(q, float).copy()

    # ------------------------------------------------------------------------------------------------ IK
    def _rate_limit(self, q_new: np.ndarray, dt: float) -> np.ndarray:
        lim = self.cfg.robot.q_dot_max_deg_s * dt
        q = self.q_last + np.clip(q_new - self.q_last, -lim, lim)
        self.q_last = q
        return q.copy()

    def _ik_cmd(self, t: float, dt: float, xy_w, z: float, yaw_w: float) -> np.ndarray:
        ex, rb = self.cfg.executor, self.cfg.robot
        z = max(z, self.zb + ex.min_z_above_belt_mm)
        tgt = [float(xy_w[0]), float(xy_w[1]), float(z)]
        r = self.kin.ik(tgt, yaw_w, q0_deg=self.q_last, tilt_deg=rb.tilt_deg, max_seeds=1, max_iter=15)
        good = r.ok and self.kin.within_margin(r.q_deg, rb.joint_margin_deg)
        if not good and (t - self._last_full_ik) > 0.2:
            self._last_full_ik = t
            r = self.kin.ik(tgt, yaw_w, q0_deg=self.q_last, tilt_deg=rb.tilt_deg, max_seeds=4, max_iter=25)
            good = r.ok and self.kin.within_margin(r.q_deg, rb.joint_margin_deg)
        if not good:
            self.ik_fail_t += dt
            return self.q_last.copy()
        self.ik_fail_t = 0.0
        return self._rate_limit(r.q_deg, dt)

    # ------------------------------------------------------------------------------------------------ một bước bám
    def step(self, t: float, dt: float, s_now: float, sdot: float, tcp: dict, tgt_bf: np.ndarray, th_deg: float, z_ref: float,
             hold_z_if_far: bool = False) -> Tuple[np.ndarray, float, float]:
        """Trả (q_lệnh, sai lệch đo được xy trong hệ băng [mm], góc khép tham chiếu đã chọn nhánh gần nhất)."""
        ex = self.cfg.executor
        tgt_bf = np.asarray(tgt_bf, float)
        th_ref = th_deg + 180.0 * round((self.fth.x - th_deg) / 180.0)
        meas = np.array([tcp["a"] - s_now, tcp["b"]])
        err_meas = float(np.hypot(*(meas - tgt_bf)))
        if hold_z_if_far and err_meas > 1.5 * ex.tol_meas_xy_mm:
            z_ref = float(self.fz.x)
        # --- tích phân bù (lệnh gốc − đo được); chỉ cộng khi bộ lọc gần tĩnh để không học nhầm quá độ
        if ex.lag_ki > 0.0:
            quasi = float(np.linalg.norm(self.fxy.v)) < ex.lag_int_vmax_mm_s and abs(float(self.fz.v)) < ex.lag_int_vmax_mm_s
            e_xy = self.fxy.x - meas
            if quasi and float(np.linalg.norm(e_xy)) < ex.lag_int_window_mm:
                self.int_xy = np.clip(self.int_xy + ex.lag_ki * e_xy * dt, -ex.lag_int_max_mm, ex.lag_int_max_mm)
            e_z = float(self.fz.x) - tcp["z"]
            if quasi and abs(e_z) < ex.lag_int_window_mm:
                self.int_z = float(np.clip(self.int_z + ex.lag_ki * e_z * dt, -ex.lag_int_max_mm, ex.lag_int_max_mm))
        self.fxy.step(tgt_bf, dt)
        self.fz.step(z_ref, dt)
        self.fth.step(th_ref, dt)
        s_cmd = s_now + sdot * ex.lead_s
        a = self.fxy.x[0] + self.int_xy[0] + s_cmd
        b = self.fxy.x[1] + self.int_xy[1]
        xy = a * self.u + b * self.v
        q = self._ik_cmd(t, dt, xy, float(self.fz.x) + self.int_z, self.phi + float(self.fth.x))
        return q, err_meas, th_ref
