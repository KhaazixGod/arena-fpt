"""Thế giới mô phỏng động học: băng, cánh tay SO-101 (FK thật từ URDF, trễ servo), kẹp, vật. Dùng để thử logic CL-0.

KHÔNG phải mô phỏng vật lý: không có ma sát, trượt, va chạm đẩy vật. "Kẹp thành công" = tại thời điểm khép, TCP nằm trong thân vật,
đoạn cắt dọc trục khép vừa độ mở, hai đầu đoạn có pháp tuyến nằm trong nón ma sát (đối cực), má kẹp không chạm vật khác, và độ cao đủ.
Nhấc >= 25 mm so với mặt băng liên tục >= 2 s thì tính là "thành công" (giống §4.3).
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Sequence, Tuple

import numpy as np

from ..geometry import perp, unit
from ..kinematics import SO101Kinematics
from ..types import Command, RobotState
from .scene import Placed, SceneRenderer


@dataclass
class WorldParams:
    servo_tau_s: float = 0.10
    servo_vmax_deg_s: float = 250.0
    cmd_delay_s: float = 0.02
    gripper_speed: float = 150.0            # đơn vị gripper/giây
    ap_max_mm: float = 60.0                 # độ mở ở gripper = 100
    mu: float = 0.5                         # ma sát cho kiểm tra đối cực
    finger_w_mm: float = 14.0               # bề rộng má kẹp (vuông góc trục khép)
    finger_t_mm: float = 5.0
    lift_threshold_mm: float = 25.0
    hold_s: float = 2.0
    belt_time_error_s: float = 0.0          # sai lệch thời gian giữa đọc s và ảnh (thử độ nhạy)
    belt_scale_error: float = 1.0           # sai hệ số mm/xung (thử độ nhạy)
    joint_offsets_deg: Tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0)   # FK thật lệch FK danh nghĩa


@dataclass
class GraspResult:
    success: bool
    reason: str
    obj: str = ""
    chord_mm: float = 0.0
    off_mm: float = 0.0          # TCP lệch gốc vật (tâm) lúc chạm


class SimWorld:
    def __init__(self, phi_deg: float, z_belt: float, renderer: SceneRenderer, objects: List[Placed], kin_true: SO101Kinematics,
                 home_q: Sequence[float], g_open: float, params: Optional[WorldParams] = None, accel: float = 200.0):
        self.phi, self.zb = phi_deg, z_belt
        self.u, self.v = unit(phi_deg), perp(phi_deg)
        self.R, self.objects, self.kin = renderer, objects, kin_true
        self.p = params or WorldParams()
        self.accel = accel
        self.t = 0.0
        self.s, self.sv, self.v_cmd = 0.0, 0.0, 0.0
        self._ht, self._hs = [0.0], [0.0]
        self.q = np.asarray(home_q, float).copy()
        self.q_goal = self.q.copy()
        self.g, self.g_goal, self.g_open = g_open, g_open, g_open
        self._cmdq: Deque = deque()
        self._off = np.asarray(self.p.joint_offsets_deg, float)
        self.holding: Optional[Placed] = None
        self.hold_off = (0.0, 0.0)
        self.stall = 0.0
        self.close_t: Optional[float] = None
        self.open_at_close = 0.0
        self.eval_done = False
        self.lift_acc = 0.0
        self.success = False
        self.grasp_log: List[Tuple[float, GraspResult]] = []
        self.events: List[Tuple[float, str]] = []
        self.extra_marks: List[tuple] = []          # vật vẽ tĩnh trong hệ thế giới (bàn cờ hiệu chuẩn...)
        self.show_arm = True

    # ------------------------------------------------------------------ BeltLike
    def start_belt(self, v: float) -> None:
        self.v_cmd = v

    def s_at(self, t: float) -> float:
        t = t + self.p.belt_time_error_s
        if t >= self._ht[-1]:
            s = self._hs[-1] + self.sv * (t - self._ht[-1])
        else:
            s = float(np.interp(t, self._ht, self._hs))
        return s * self.p.belt_scale_error

    def speed_at(self, t: float) -> float:
        return self.sv * self.p.belt_scale_error

    # ------------------------------------------------------------------ robot
    def send(self, t: float, cmd: Command) -> None:
        if cmd.q_deg is not None or cmd.gripper is not None:
            self._cmdq.append((t + self.p.cmd_delay_s, None if cmd.q_deg is None else np.asarray(cmd.q_deg, float),
                               cmd.gripper))

    def robot_state(self, t: float) -> RobotState:
        return RobotState(self.q.copy(), float(self.g), t)

    def tcp_true(self):
        p, a, c, pitch, yaw = self.kin.tool_axes(self.q + self._off)
        return p, yaw

    def tcp_ab(self):
        p, yaw = self.tcp_true()
        return float(p[0] * self.u[0] + p[1] * self.u[1]), float(p[0] * self.v[0] + p[1] * self.v[1]), float(p[2]), yaw

    # ------------------------------------------------------------------ vật
    def on_belt(self) -> List[Placed]:
        return [o for o in self.objects if not o.attached]

    def _target_chord(self):
        """Vật chứa TCP và đoạn cắt của nó dọc trục khép: (po, d, ends, chord) hoặc None."""
        a, b, z, yaw_w = self.tcp_ab()
        th = math.radians(yaw_w - self.phi)
        d = np.array([math.cos(th), math.sin(th)])        # trục khép trong (a, b)
        target = None
        for po in self.objects:
            if po.attached:
                continue
            if po.contains(a, b, self.s):
                target = po
                break
        if target is None:
            return None
        ends, lens = [], []
        for sgn in (+1.0, -1.0):
            t = 0.0
            while t < 120.0 and target.contains(a + sgn * d[0] * (t + 0.25), b + sgn * d[1] * (t + 0.25), self.s):
                t += 0.25
            ends.append(np.array([a, b]) + sgn * d * t)
            lens.append(t)
        return target, d, ends, lens[0] + lens[1]

    def evaluate_grasp(self, opening: float) -> GraspResult:
        """Chấm tại thời điểm má kẹp chạm vật. ``opening`` = độ mở (mm) lúc BẮT ĐẦU khép."""
        a, b, z, yaw_w = self.tcp_ab()
        hit = self._target_chord()
        if hit is None:
            return GraspResult(False, "miss")
        target, d, ends, chord = hit
        nm = target.obj.name
        off = float(math.hypot(a - (target.a_b + self.s), b - target.b))

        def R(ok, reason, ch=0.0):
            return GraspResult(ok, reason, nm, ch, off)

        if z > self.zb + target.obj.height_mm:
            return R(False, "too_high")
        if chord > opening - 1.5:
            return R(False, "too_wide", chord)
        # đối cực: pháp tuyến ngoài tại hai đầu chống lại hướng khép
        cos_min = math.cos(math.atan(self.p.mu))
        th_o = math.radians(target.theta_deg)
        for sgn, e in zip((+1.0, -1.0), ends):
            bpt = e + sgn * d * 0.12                                 # biên nằm giữa mẫu trong cuối và mẫu ngoài đầu tiên
            lx, ly = target.to_local(bpt[0], bpt[1], self.s)
            n = target.obj.normal_local(lx, ly)
            if n is None:
                return R(False, "slip", chord)
            nw = np.array([math.cos(th_o) * n[0] - math.sin(th_o) * n[1], math.sin(th_o) * n[0] + math.cos(th_o) * n[1]])
            if float(nw @ (sgn * d)) < cos_min:
                return R(False, "slip", chord)
        # má kẹp chạm vật khác?
        half = opening / 2.0 + self.p.finger_t_mm / 2.0
        for sgn in (+1.0, -1.0):
            c = np.array([a, b]) + sgn * d * half
            perp_d = np.array([-d[1], d[0]])
            for k in np.linspace(-self.p.finger_w_mm / 2, self.p.finger_w_mm / 2, 5):
                for j in np.linspace(-self.p.finger_t_mm / 2, self.p.finger_t_mm / 2, 3):
                    pt = c + perp_d * k + d * sgn * j
                    for po in self.objects:
                        if po is not target and not po.attached and po.contains(pt[0], pt[1], self.s):
                            return R(False, "collision", chord)
        return R(True, "ok", chord)

    # ------------------------------------------------------------------ vật lý
    def step(self, t: float, dt: float) -> None:
        self.t = t
        dv = float(np.clip(self.v_cmd - self.sv, -self.accel * dt, self.accel * dt))
        self.sv += dv
        self.s += self.sv * dt
        self._ht.append(t + dt)
        self._hs.append(self.s)
        while self._cmdq and self._cmdq[0][0] <= t:
            _, qg, gg = self._cmdq.popleft()
            if qg is not None:
                self.q_goal = qg
            if gg is not None:
                self.g_goal = float(gg)
        dq = (self.q_goal - self.q) / self.p.servo_tau_s
        vm = self.p.servo_vmax_deg_s
        dq = np.clip(dq, -vm, vm)
        self.q = self.q + dq * dt
        # kẹp
        dg = float(np.clip(self.g_goal - self.g, -self.p.gripper_speed * dt, self.p.gripper_speed * dt))
        g_new = self.g + dg
        if self.holding is not None and g_new < self.stall:
            g_new = self.stall
        self.g = g_new
        # logic khép / thả
        closing = self.g_goal < 0.5 * self.g_open
        if closing and self.close_t is None:
            self.close_t = t
            self.open_at_close = self.p.ap_max_mm * self.g / 100.0
            self.eval_done = False
        if closing and self.close_t is not None and not self.eval_done and self.holding is None:
            opening_now = self.p.ap_max_mm * self.g / 100.0
            hit = self._target_chord() if opening_now < self.open_at_close else None
            if (hit is not None and opening_now <= hit[3]) or self.g <= 0.5:      # má kẹp chạm vật, hoặc khép kín không chạm gì
                self.eval_done = True
                res = self.evaluate_grasp(self.open_at_close)
                self.grasp_log.append((t, res))
                self.events.append((t, "grasp_eval:" + res.reason))
            else:
                res = None
            if res is not None and res.success:
                a, b, z, _ = self.tcp_ab()
                for po in self.objects:
                    if po.obj.name == res.obj and not po.attached and po.contains(a, b, self.s):
                        po.attached = True
                        ca, cb = po.a_b + self.s, po.b
                        self.hold_off = (ca - a, cb - b)
                        self.holding = po
                        self.stall = res.chord_mm / self.p.ap_max_mm * 100.0
                        break
        if self.g_goal > self.g_open - 5.0:
            self.close_t = None
            if self.holding is not None:
                po = self.holding
                po.attached = False
                po.a_b, po.b = po.world_a - self.s, po.world_b
                self.holding = None
                self.lift_acc = 0.0
        if self.holding is not None:
            a, b, z, _ = self.tcp_ab()
            self.holding.world_a, self.holding.world_b = a + self.hold_off[0], b + self.hold_off[1]
            if z >= self.zb + self.p.lift_threshold_mm:
                self.lift_acc += dt
                if self.lift_acc >= self.p.hold_s:
                    self.success = True
            else:
                self.lift_acc = 0.0

    # ------------------------------------------------------------------ ảnh
    def marks(self):
        if not self.show_arm:
            return list(self.extra_marks)
        a, b, z, _ = self.tcp_ab()
        base = np.array([38.8, 0.0])                       # trục pan trong W
        ba, bb = float(base @ self.u), float(base @ self.v)
        dirv = np.array([ba - a, bb - b])
        n = np.linalg.norm(dirv)
        dirv = dirv / n if n > 1e-6 else np.array([1.0, 0.0])
        end = np.array([a, b]) + dirv * 170.0              # liên kết tay vẽ từ TCP về phía đế
        return list(self.extra_marks) + [("line", a, b, float(end[0]), float(end[1]), 28.0, (120, 120, 120)),
                                         ("circle", a, b, 13.0, (150, 150, 150))]

    def render(self, t: float) -> np.ndarray:
        return self.R.render(self.s, self.objects, self.marks())
