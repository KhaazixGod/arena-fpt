"""Ghép hệ thống mô phỏng đầy đủ: hiệu chuẩn giả (có nhiễu), nền, bộ phát hiện, bản đồ tầm với, bộ điều khiển, thế giới.
``run_trial`` chạy một lượt thử theo thời gian ảo và trả kết quả. Dùng cho test và cho ``cl0.run_g0 --sim``.
"""
from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..config import Config
from ..controller import CL0Controller
from ..geometry import PlaneCalib, Rectifier, Window, calib_from_board, fit_belt_motion, fit_plane_homography, perp, unit
from ..kinematics import SO101Kinematics
from ..perception import Detector, build_background
from ..reach import TopDownReach
from ..runner import run_controller
from ..types import Frame
from .scene import (Placed, SceneRenderer, SimCameraCfg, default_library, look_at_homography, make_belt_texture)
from .platform import SimPlatform
from .world import SimWorld, WorldParams

_REACH_CACHE: Dict[tuple, TopDownReach] = {}


def get_reach(kin: SO101Kinematics, tilt: float, margin: float, step: float = 5.0) -> TopDownReach:
    key = (round(tilt, 3), round(margin, 3), step, tuple(np.round(kin.tcp_offset_mm, 3)))
    if key not in _REACH_CACHE:
        _REACH_CACHE[key] = TopDownReach(kin, tilt_deg=tilt, step_mm=step, margin_deg=margin).build()
    return _REACH_CACHE[key]


@dataclass
class SimSetup:
    phi_deg: float = 90.0
    z_belt: float = -40.0               # mặt băng THẤP hơn mặt đế robot 40 mm (xem README: để có khoảng nâng với kẹp thẳng đứng)
    belt_center_w: Tuple[float, float] = (200.0, 0.0)
    belt_width: float = 120.0
    flip: bool = False
    textured: bool = False
    texture_period_mm: float = 1200.0
    calib_mode: str = "board"           # "board" (bàn cờ + vài điểm chạm) | "touch" (mọi điểm đều chạm)
    calib_n: int = 12
    calib_noise_px: float = 0.5
    calib_noise_mm: float = 1.5
    belt_dir_err_deg: float = 0.0
    mm_per_step: float = 0.05
    latency_est_error_s: float = 0.0
    seed: int = 0
    world: WorldParams = field(default_factory=WorldParams)
    cam: SimCameraCfg = field(default_factory=SimCameraCfg)
    window_half_a: float = 220.0


@dataclass
class System:
    setup: SimSetup
    cfg: Config
    kin: SO101Kinematics
    calib: PlaneCalib
    rect: Rectifier
    detector: Detector
    reach: TopDownReach
    controller: CL0Controller
    renderer: SceneRenderer
    H_wp: np.ndarray
    lib: dict
    ca: float
    cb: float
    marks_home: list = field(default_factory=list)      # vẽ cánh tay ở tư thế nhà (đã nằm trong nền): dùng khi tự dựng ảnh cảnh trong test

    def make_world(self, objects: List[Placed]) -> SimWorld:
        st = self.setup
        return SimWorld(st.phi_deg, st.z_belt, self.renderer, objects, self.kin, self.cfg.robot.home_q_deg,
                        self.cfg.robot.gripper_open, st.world, accel=self.cfg.belt.accel_mm_s2)


def build_system(setup: Optional[SimSetup] = None, cfg: Optional[Config] = None, async_perception: bool = False) -> System:
    st = setup or SimSetup()
    cfg = cfg or Config()
    rng = np.random.default_rng(st.seed)
    kin = SO101Kinematics(urdf=cfg.robot.urdf or None, tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
    cx, cy = st.belt_center_w
    H_wp = look_at_homography((cx, cy, st.z_belt + 450.0), (cx, cy, st.z_belt), 520.0, st.cam.size, z_plane=st.z_belt, flip=st.flip)
    tex = None
    renderer = SceneRenderer(H_wp, st.phi_deg, st.cam, seed=st.seed + 1)
    if st.textured:
        tex = make_belt_texture(renderer.rows, st.texture_period_mm, renderer.r, seed=st.seed + 5)
        renderer = SceneRenderer(H_wp, st.phi_deg, st.cam, belt_texture=tex, texture_period_mm=st.texture_period_mm, seed=st.seed + 1)
    u, v = unit(st.phi_deg), perp(st.phi_deg)
    ca, cb = float(np.dot((cx, cy), u)), float(np.dot((cx, cy), v))

    # --- hiệu chuẩn giả
    off = np.asarray(st.world.joint_offsets_deg, float)

    def touch_xy(pt):
        """Đặt TCP thật vào pt: phần mềm chỉ thấy FK danh nghĩa của góc khớp đọc về (thật = FK(q + off))."""
        r = kin.ik([float(pt[0]), float(pt[1]), st.z_belt], st.phi_deg, tilt_deg=cfg.robot.tilt_deg)
        if r.ok and kin.within_margin(r.q_deg, cfg.robot.joint_margin_deg):
            pn, _ = kin.fk(r.q_deg - off)
            return pn
        return None

    if st.calib_mode == "board":
        A = np.linspace(-st.window_half_a * 0.9, st.window_half_a * 0.9, 10)
        B = np.linspace(-st.belt_width / 2 + 10, st.belt_width / 2 - 10, 4)
        AA, BB = np.meshgrid(A, B)
        P = (ca + AA.ravel())[:, None] * u + (cb + BB.ravel())[:, None] * v
        px = (np.c_[P, np.ones(len(P))] @ H_wp.T)
        px = px[:, :2] / px[:, 2:3] + rng.normal(0, st.calib_noise_px * 0.6, (len(P), 2))
        ang = math.radians(7.0)                                         # hệ bàn cờ quay/tịnh tiến tuỳ ý so với W
        Rb = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
        board_xy = (Rb @ P.T).T + np.array([31.0, -22.0]) + rng.normal(0, 0.15, P.shape)     # in chính xác ~0.15 mm
        tb, tw, zt = [], [], []
        for i in rng.permutation(len(P)):
            pn = touch_xy(P[i])
            if pn is not None:
                tb.append(board_xy[i]); tw.append(pn[:2] + rng.normal(0, st.calib_noise_mm, 2)); zt.append(float(pn[2]))
            if len(tb) >= 5:
                break
        if len(tb) < 3:
            raise RuntimeError("mô phỏng: không đủ điểm chạm trong vùng với tới")
        calib = calib_from_board(px, board_xy, np.array(tb), np.array(tw), float(np.mean(zt)), image_size=st.cam.size)
    else:
        A = rng.uniform(-st.window_half_a * 0.9, st.window_half_a * 0.9, st.calib_n)
        B = rng.uniform(-st.belt_width / 2, st.belt_width / 2, st.calib_n)
        P = (ca + A)[:, None] * u + (cb + B)[:, None] * v
        px = (np.c_[P, np.ones(len(P))] @ H_wp.T)
        px = px[:, :2] / px[:, 2:3] + rng.normal(0, st.calib_noise_px, (len(P), 2))
        xy_meas, z_touch = P.copy(), []
        for i, pt in enumerate(P):
            pn = touch_xy(pt)
            if pn is not None:
                xy_meas[i] = pn[:2]
                z_touch.append(float(pn[2]))
        xy_meas = xy_meas + rng.normal(0, st.calib_noise_mm, P.shape)
        calib = fit_plane_homography(px, xy_meas, z_plane_mm=float(np.mean(z_touch)) if z_touch else st.z_belt, image_size=st.cam.size)

    # --- hướng băng và mm/xung từ vạch đánh dấu
    tracks = []
    for k in range(3):
        steps = np.array([0, 2000, 4000, 6000]) + 100 * k
        a0 = ca + rng.uniform(-120, -60)
        b0 = cb + rng.uniform(-40, 40)
        pts = np.array([(a0 + st.mm_per_step * s) * u + b0 * v for s in steps])
        pxm = np.c_[pts, np.ones(len(pts))] @ H_wp.T
        pxm = pxm[:, :2] / pxm[:, 2:3] + rng.normal(0, st.calib_noise_px, (len(pts), 2))
        tracks.append((steps, calib.pix_to_world(pxm)))
    phi_hat, mps, lat = fit_belt_motion(tracks)
    calib.belt_dir_deg = phi_hat + st.belt_dir_err_deg
    calib.mm_per_step = mps

    # --- cửa sổ nhìn từ trên và nền băng trống
    win = Window(ca - st.window_half_a, ca + st.window_half_a, cb - st.belt_width / 2 - 15, cb + st.belt_width / 2 + 15,
                 cfg.perception.res_mm)
    rect = Rectifier(calib, win)
    period = st.texture_period_mm if st.textured else 0.0
    s_list = rng.uniform(0, st.texture_period_mm, 60) if st.textured else rng.uniform(0, 300, 12)
    # nền dựng với cánh tay ở tư thế NHÀ — đúng quy trình thật (`calibrate background`: tay ở home là một phần của nền)
    marks_home = SimWorld(st.phi_deg, st.z_belt, renderer, [], kin, cfg.robot.home_q_deg, cfg.robot.gripper_open, st.world).marks()
    bg = build_background(((renderer.render(float(s), [], marks_home), float(s)) for s in s_list), rect, cfg.perception,
                          textured=st.textured, period_mm=period)
    det = Detector(rect, bg, cfg.perception)
    reach = get_reach(kin, cfg.robot.tilt_deg, cfg.robot.joint_margin_deg)
    ctrl = CL0Controller(cfg, kin, det, reach, calib.belt_dir_deg, calib.z_plane_mm, async_perception=async_perception)
    return System(st, cfg, kin, calib, rect, det, reach, ctrl, renderer, H_wp, default_library(), ca, cb, marks_home)


def belt_center_for(phi_deg: float, d_mm: float = 170.0, base_xy: Tuple[float, float] = (38.8, 0.0)) -> Tuple[float, float]:
    """Tâm băng (W) cho băng chạy theo φ, đi cách trục pan của robot d_mm về phía trước (+x) — băng không bao giờ cắt qua đế robot.
    φ = 90° cho (208.8, 0) ≈ cấu hình mặc định (200, 0)."""
    ph = math.radians(phi_deg)
    n = np.array([math.sin(ph), -math.cos(ph)])
    if n[0] < -1e-9:
        n = -n
    return float(base_xy[0] + d_mm * n[0]), float(base_xy[1] + d_mm * n[1])


def arrangement_to_placed(sys_: System, items: Sequence[Tuple[str, float, float, float]], a_start: float = -420.0,
                          b_offset: float = 0.0) -> List[Placed]:
    """items: (tên vật, dx dọc băng so với vật đầu, y ngang băng tính từ mép TRÁI (nhìn theo chiều băng chạy), yaw độ CCW so với hướng băng).
    a_start = vị trí a_b của vật đầu."""
    out = []
    b_left = sys_.cb + sys_.setup.belt_width / 2          # mép TRÁI nhìn theo chiều băng chạy = phía b lớn (v_hat là bên trái của u_hat)
    for name, dx, y, th in items:
        out.append(Placed(sys_.lib[name], sys_.ca + a_start + dx, b_left - y + b_offset, th))
    return out


@dataclass
class TrialResult:
    success: bool                  # theo thế giới mô phỏng (nhấc >= 25 mm giữ >= 2 s)
    outcome: str                   # theo bộ điều khiển
    grasp: str                     # lý do đánh giá kẹp ("" nếu không kẹp lần nào)
    picked: str
    t_end: float
    phases: List[Tuple[float, str]]
    diag: dict
    log: List[dict]
    events: list
    off_mm: float = float("nan")     # TCP lệch tâm vật lúc má kẹp chạm


def run_trial(sys_: System, objects: List[Placed], v_mm_s: Optional[float] = None, t_max: Optional[float] = None,
              verbose: bool = False) -> TrialResult:
    cfg, st = sys_.cfg, sys_.setup
    world = sys_.make_world(objects)
    plat = SimPlatform(world, cfg.executor.control_hz, st.cam.fps, st.cam.latency_s, st.cam.latency_s + st.latency_est_error_s)
    plat.start_belt(cfg.belt.speed_mm_s if v_mm_s is None else v_mm_s)
    rr = run_controller(sys_.controller, plat, t_limit_s=t_max if t_max is not None else cfg.executor.hard_timeout_s + 10.0)
    last = world.grasp_log[-1][1] if world.grasp_log else None
    return TrialResult(world.success, rr.outcome, last.reason if last else "", last.obj if last else "", rr.t_end, rr.phases,
                       rr.diag, rr.log, rr.events, last.off_mm if last else float("nan"))
