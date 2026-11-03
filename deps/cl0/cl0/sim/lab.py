"""Phòng thí nghiệm ảo theo THỜI GIAN ẢO: camera + băng + tay có cùng giao diện như phần cứng thật.

Dùng để chạy thử các lệnh ``python -m cl0.calibrate {board,belt,background,lag}`` (đường dẫn I/O, thứ tự, đơn vị, hiệu chuẩn tính ra có đúng
với thế giới ảo hay không) mà không cần thiết bị: ``LabSession`` thay ``time``, ``input`` và ``open_camera/open_belt/open_arm`` của
``cl0.calibrate`` bằng bản ảo, còn một "người vận hành" ảo (``Operator``) làm các việc tay chân mà lời nhắc yêu cầu (đặt bàn cờ, đặt vạch,
chạm góc bằng TCP...).

KHÔNG chứng minh gì về phần cứng thật (serial, V4L2, LeRobot); chỉ chứng minh logic hiệu chuẩn + khung toạ độ + đơn vị khớp nhau.
"""
from __future__ import annotations

import builtins
import math
import types
from collections import deque
from typing import Callable, List, Optional

import numpy as np

from ..types import Command, Frame, RobotState
from .harness import System
from .scene import Placed


class SimCamera:
    def __init__(self, lab: "SimLab", assumed_latency_s: float):
        self.lab = lab
        self.assumed = assumed_latency_s
        self._latest: Optional[Frame] = None
        self._seq = 0
        self._seen = 0

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def _deliver(self, t_deliver: float, img: np.ndarray) -> None:
        self._latest = Frame(img, t_deliver - self.assumed)          # như CameraThread: t_nhận − camera.latency_s (giá trị ĐÃ cấu hình)
        self._seq += 1

    def poll(self) -> Optional[Frame]:
        if self._seq == self._seen:
            return None
        self._seen = self._seq
        return self._latest

    def latest(self) -> Optional[Frame]:
        return self._latest

    def fps_measured(self) -> float:
        return self.lab.sys.setup.cam.fps

    def jitter_ms(self) -> float:
        return 0.0


class SimBelt:
    """Bộ đếm xung ảo. Lệnh tốc độ v [mm/s] được đổi thành xung/s bằng mm/xung ĐANG DÙNG; băng thật quay với mm/xung THẬT."""

    def __init__(self, lab: "SimLab", used_mm_per_step: float):
        self.lab, self.used = lab, used_mm_per_step
        self.true = lab.sys.setup.mm_per_step
        self.cfg = lab.sys.cfg.belt
        self.is_open = False

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def start(self, v_mm_s: float) -> None:
        steps_per_s = v_mm_s / self.used if self.used > 0 else 0.0
        self.lab.world.start_belt(steps_per_s * self.true)

    def stop(self) -> None:
        self.lab.world.start_belt(0.0)

    def history(self):
        t, c = self.lab.belt_log()
        return t, c * self.used

    def s_at(self, t: float) -> float:
        th, sh = self.history()
        return float(np.interp(t, th, sh)) if len(th) else 0.0

    def speed_at(self, t: float) -> float:
        th, sh = self.history()
        if len(th) < 3:
            return 0.0
        j1 = min(max(int(np.searchsorted(th, t)), 2), len(th) - 1)
        j0 = max(j1 - 50, 0)
        return float((sh[j1] - sh[j0]) / max(th[j1] - th[j0], 1e-6))


class SimArm:
    def __init__(self, lab: "SimLab"):
        self.lab = lab
        self.torque_on = True
        self.connected = False

    def connect(self) -> None:
        self.connected = True
        self.torque_on = True                               # LeRobot bật torque khi kết nối

    def disconnect(self) -> None:
        self.connected = False

    def torque(self, on: bool) -> None:
        self.torque_on = on

    def state(self) -> RobotState:
        return self.lab.world.robot_state(self.lab.t)

    def send(self, q_deg, gripper) -> None:
        if self.torque_on:
            self.lab.world.send(self.lab.t, Command(None if q_deg is None else np.asarray(q_deg, float), gripper, "lab"))

    def set_q_direct(self, q_deg) -> None:
        """Mô phỏng người kéo tay (torque tắt): đặt thẳng góc khớp ĐỌC VỀ."""
        w = self.lab.world
        w.q = np.asarray(q_deg, float).copy()
        w.q_goal = w.q.copy()


class SimLab:
    def __init__(self, system: System, objects: Optional[List[Placed]] = None, cam_latency_true_s: Optional[float] = None,
                 physics_dt: float = 0.005):
        self.sys = system
        self.world = system.make_world(list(objects or []))
        self.t = 0.0
        self.dt = physics_dt
        self.cam_dt = 1.0 / system.setup.cam.fps
        self.lat = system.setup.cam.latency_s if cam_latency_true_s is None else cam_latency_true_s
        self._next_cam = 0.0
        self._pending: deque = deque()
        self._bt: List[float] = [0.0]
        self._bc: List[float] = [0.0]
        self.camera: Optional[SimCamera] = None
        self.arm = SimArm(self)
        self._cams: List[SimCamera] = []

    # ------------------------------------------------------------------ thiết bị (như open_* của calibrate)
    def camera_for(self, cfg) -> SimCamera:
        cam = SimCamera(self, cfg.camera.latency_s)
        self.camera = cam
        self._cams.append(cam)
        return cam

    def belt_for(self, cfg, counts_only: bool = False) -> SimBelt:
        used = cfg.belt.mm_per_step
        if counts_only and cfg.belt.kind == "counter" and used <= 0:
            used = 1.0                                      # đúng như open_belt thật: đếm xung thô
        return SimBelt(self, used)

    def arm_for(self, cfg) -> SimArm:
        self.arm.connect()
        return self.arm

    def belt_log(self):
        return np.asarray(self._bt), np.asarray(self._bc)

    # ------------------------------------------------------------------ thời gian ảo
    def advance(self, dt: float) -> None:
        t_end = self.t + dt
        while self.t < t_end - 1e-12:
            h = min(self.dt, t_end - self.t)
            self.world.step(self.t, h)
            self.t += h
            self._bt.append(self.t)
            self._bc.append(float(np.floor(self.world.s / self.sys.setup.mm_per_step)))
            if self.t >= self._next_cam:
                self._pending.append((self.t + self.lat, self.world.render(self.t)))
                self._next_cam += self.cam_dt
            while self._pending and self._pending[0][0] <= self.t:
                td, img = self._pending.popleft()
                for cam in self._cams:
                    cam._deliver(td, img)

    def monotonic(self) -> float:
        return self.t

    def sleep(self, dt: float) -> None:
        self.advance(max(dt, 0.0))

    def time_module(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(monotonic=self.monotonic, sleep=self.sleep, time=self.monotonic)

    # ------------------------------------------------------------------ dựng cảnh / hình học thật
    def place(self, obj_name: str, a_world: float, b_world: float, theta_deg: float = 0.0) -> Placed:
        po = Placed(self.sys.lib[obj_name], a_world - self.world.s, b_world, theta_deg)
        self.world.objects.append(po)
        return po

    def clear(self) -> None:
        self.world.objects.clear()
        self.world.extra_marks.clear()

    def px_to_w(self, uv) -> np.ndarray:
        """Điểm ảnh -> W (mm) THEO HÌNH HỌC THẬT của thế giới ảo (không phải hiệu chuẩn)."""
        uv = np.atleast_2d(np.asarray(uv, float))
        p = np.c_[uv, np.ones(len(uv))] @ np.linalg.inv(self.sys.H_wp).T
        return p[:, :2] / p[:, 2:3]

    def w_to_px(self, xy) -> np.ndarray:
        xy = np.atleast_2d(np.asarray(xy, float))
        p = np.c_[xy, np.ones(len(xy))] @ self.sys.H_wp.T
        return p[:, :2] / p[:, 2:3]

    def set_tcp_true(self, xy, z: float, rng: Optional[np.random.Generator] = None, noise_mm: float = 0.0, yaw_deg: Optional[float] = None) -> bool:
        """Người vận hành đưa TCP THẬT tới (xy, z) (kèm sai số đặt tay noise_mm). Phần mềm chỉ thấy FK danh nghĩa của góc đọc về."""
        xy = np.asarray(xy, float)
        if rng is not None and noise_mm > 0:
            xy = xy + rng.normal(0, noise_mm, 2)
        st = self.sys
        r = st.kin.ik([float(xy[0]), float(xy[1]), float(z)], st.setup.phi_deg if yaw_deg is None else yaw_deg,
                      tilt_deg=st.cfg.robot.tilt_deg, q0_deg=self.world.q)
        if not r.ok:
            return False
        off = np.asarray(st.setup.world.joint_offsets_deg, float)
        self.arm.set_q_direct(r.q_deg - off)
        return True


class LabSession:
    """``with LabSession(lab, operator): calibrate.main([...])`` — vá cl0.calibrate để chạy trên phòng thí nghiệm ảo."""

    def __init__(self, lab: SimLab, operator: Callable[[str], str]):
        self.lab, self.operator = lab, operator
        self.prompts: List[str] = []

    def _input(self, prompt: str = "") -> str:
        self.prompts.append(prompt)
        out = self.operator(prompt)
        return "" if out is None else out

    def __enter__(self):
        from .. import calibrate as C
        self._C = C
        self._saved = (C.time, builtins.input, C.open_camera, C.open_belt, C.open_arm)
        C.time = self.lab.time_module()
        builtins.input = self._input
        C.open_camera = lambda cfg, calib_path: self.lab.camera_for(cfg)
        C.open_belt = lambda cfg, counts_only=False: self.lab.belt_for(cfg, counts_only)
        C.open_arm = lambda cfg, kin: self.lab.arm_for(cfg)
        return self

    def __exit__(self, *exc):
        C = self._C
        C.time, builtins.input, C.open_camera, C.open_belt, C.open_arm = self._saved
        return False


class Operator:
    """Người vận hành ảo: đọc lời nhắc của calibrate rồi làm đúng việc được yêu cầu trong thế giới ảo."""

    def __init__(self, lab: SimLab, board_cols: int = 7, board_rows: int = 4, square_mm: float = 15.0, board_theta_deg: float = 12.0,
                 board_center_ab=None, touch_noise_mm: float = 1.0, marker: str = "plate20x45", marker_b_offsets=(-25.0, 0.0, 25.0),
                 marker_a_start_rel: float = -170.0, seed: int = 0, show_arm_in_board: bool = True):
        self.lab, self.cols, self.rows, self.sq = lab, board_cols, board_rows, square_mm
        self.theta = board_theta_deg
        sys_ = lab.sys
        self.center_ab = board_center_ab if board_center_ab is not None else (sys_.ca, sys_.cb)
        self.noise = touch_noise_mm
        self.marker, self.mb, self.ma = marker, list(marker_b_offsets), marker_a_start_rel
        self.rng = np.random.default_rng(seed)
        self.n_marker = 0
        self.touch_log: List[tuple] = []
        self._corners_px: Optional[np.ndarray] = None
        self.show_arm_in_board = show_arm_in_board

    # --- bàn cờ
    def _board_origin_ab(self):
        c, s = math.cos(math.radians(self.theta)), math.sin(math.radians(self.theta))
        hx, hy = (self.cols + 1) * self.sq / 2.0, (self.rows + 1) * self.sq / 2.0
        ca, cb = self.center_ab
        return ca - (c * hx - s * hy), cb - (s * hx + c * hy)

    def put_board(self) -> None:
        a0, b0 = self._board_origin_ab()
        self.lab.world.extra_marks = [("checker", a0, b0, self.theta, self.cols + 1, self.rows + 1, self.sq)]
        self.lab.world.show_arm = self.show_arm_in_board

    def __call__(self, prompt: str) -> str:
        lab = self.lab
        sys_ = lab.sys
        if "Đặt bàn cờ" in prompt:
            self.put_board()
            lab.sleep(0.5)
            return ""
        if "Chạm góc #" in prompt:
            k = int(prompt.split("#")[1].split()[0])
            if self._corners_px is None:                                   # người vận hành nhìn ảnh xem góc k nằm ở đâu
                from .. import calib_tools as ct
                self._corners_px = ct.detect_board(lab.camera.latest().img, self.cols, self.rows)
                assert self._corners_px is not None, "operator: không thấy bàn cờ"
            xy = lab.px_to_w(self._corners_px[k])[0]
            ok = lab.set_tcp_true(xy, sys_.setup.z_belt, self.rng, self.noise)
            self.touch_log.append((k, xy.copy(), ok))
            assert ok, f"operator: không đưa được TCP tới góc #{k} ({xy.round(0)})"
            lab.sleep(0.3)
            return ""
        if "Dọn băng TRỐNG" in prompt:
            lab.clear()
            lab.world.show_arm = True
            lab.arm.set_q_direct(np.asarray(sys_.cfg.robot.home_q_deg, float))      # tay về nhà (tay thật cũng phải ra khỏi băng)
            lab.sleep(0.5)
            return ""
        if "Đặt VẠCH PHẲNG" in prompt or "Đưa vạch về vị trí thượng nguồn" in prompt:
            lab.clear()
            b = sys_.cb + self.mb[self.n_marker % len(self.mb)]
            self.n_marker += 1
            lab.place(self.marker, sys_.ca + self.ma, b, 0.0)
            lab.sleep(0.5)
            return ""
        return ""
