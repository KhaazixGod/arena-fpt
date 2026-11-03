"""``Platform`` mô phỏng: bọc SimWorld, camera ảo có độ trễ, nhịp điều khiển; chạy theo thời gian ảo."""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..types import Command, Frame, RobotState
from .world import SimWorld


class SimPlatform:
    def __init__(self, world: SimWorld, control_hz: float, cam_fps: float, cam_latency_s: float, latency_est_s: float,
                 physics_hz: float = 200.0):
        self.world, self.belt = world, world
        self.dt = 1.0 / physics_hz
        self.ctrl_dt = 1.0 / control_hz
        self.cam_dt = 1.0 / cam_fps
        self.lat, self.lat_est = cam_latency_s, latency_est_s
        self.t = 0.0
        self._next_cam = 0.0
        self._next_ctrl = 0.0
        self._q: deque = deque()
        self._frames_ready: Optional[Frame] = None

    # ---- Platform
    def now(self) -> float:
        return self.t

    def _advance_one(self) -> None:
        self.world.step(self.t, self.dt)
        if self.t >= self._next_cam:
            self._q.append((self.t + self.lat, self.world.render(self.t)))
            self._next_cam += self.cam_dt
        self.t += self.dt

    def poll_frame(self) -> Optional[Frame]:
        fr = None
        while self._q and self._q[0][0] <= self.t:
            td, img = self._q.popleft()
            fr = Frame(img, td - self.lat_est)
        return fr

    def robot_state(self) -> RobotState:
        return self.world.robot_state(self.t)

    def send(self, cmd: Command) -> None:
        self.world.send(self.t, cmd)

    def wait_tick(self) -> float:
        self._next_ctrl += self.ctrl_dt
        while self.t < self._next_ctrl - 1e-9:
            self._advance_one()
        return self.t

    def start_belt(self, v_mm_s: float) -> None:
        self.world.start_belt(v_mm_s)

    def stop_belt(self) -> None:
        self.world.start_belt(0.0)
