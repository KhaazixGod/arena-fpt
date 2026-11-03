"""``Platform`` cho phần cứng thật: camera thread + LeRobot + băng, nhịp điều khiển theo ``time.monotonic()``."""
from __future__ import annotations

import time
from typing import Callable, Optional

from ..config import Config
from ..types import Command, Frame, LinkLost, RobotState


class BeltCommError(LinkLost):
    """Băng đang chạy (đã ra lệnh v > 0) mà không có dòng bộ đếm mới: dữ liệu s(t) không còn đáng tin."""


class CameraCommError(LinkLost):
    """Camera không trả khung mới trong thời gian dài giữa lượt."""


class HardwarePlatform:
    """Thêm hai kiểm tra liên kết MỖI nhịp (nếu không, mất dữ liệu giữa lượt sẽ bị đọc nhầm thành thất bại của CL-0):
    camera im lặng quá ``cam_timeout_s``; băng ``kind = counter`` đang chạy mà không có dòng đếm mới quá ``belt_timeout_s``
    (sau thời gian chờ ``belt_grace_s`` + dốc tăng tốc kể từ lúc ra lệnh chạy; đủ dài cho Arduino/ESP vừa reset)."""

    def __init__(self, cfg: Config, camera, arm, belt, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, cam_timeout_s: float = 1.0, belt_timeout_s: float = 0.5,
                 belt_grace_s: float = 1.5):
        self.cfg, self.camera, self.arm, self.belt = cfg, camera, arm, belt
        self.clock, self._sleep = clock, sleep
        self.period = 1.0 / cfg.executor.control_hz
        self._next: Optional[float] = None
        self.n_ticks = 0
        self.n_late = 0
        self.max_late_s = 0.0
        self.cam_timeout_s, self.belt_timeout_s, self.belt_grace_s = cam_timeout_s, belt_timeout_s, belt_grace_s
        self._t_frame: Optional[float] = None         # lúc nhận khung mới gần nhất (đồng hồ chủ)
        self._belt_v = 0.0                            # tốc độ đã ra lệnh (mm/s); 0 = băng không được kỳ vọng đang chạy
        self._belt_t0 = 0.0

    def reset_run(self) -> None:
        """Gọi trước MỖI lượt: xoá bộ đếm nhịp và mốc thời gian của các kiểm tra liên kết (giữa hai lượt có thể cách nhau nhiều phút)."""
        self.n_ticks = self.n_late = 0
        self.max_late_s = 0.0
        self._next = None
        self._t_frame = None
        self._belt_v = 0.0

    def now(self) -> float:
        return self.clock()

    def poll_frame(self) -> Optional[Frame]:
        f = self.camera.poll()
        if f is not None:
            self._t_frame = self.clock()
        return f

    def robot_state(self) -> RobotState:
        return self.arm.state()

    def send(self, cmd: Command) -> None:
        self.arm.send(cmd.q_deg, cmd.gripper)

    def check_links(self, now: float) -> None:
        if self.camera is None:
            pass
        elif self._t_frame is None:
            self._t_frame = now                        # nhịp đầu tiên: bắt đầu tính thời gian im lặng từ đây
        elif now - self._t_frame > self.cam_timeout_s:
            raise CameraCommError(f"camera không trả khung mới trong {now - self._t_frame:.1f} s giữa lượt "
                                  f"(lỗi cuối: {getattr(self.camera, 'error', None)}); kiểm tra cáp USB / nguồn")
        if self._belt_v > 0 and getattr(self.cfg.belt, "kind", "") == "counter" and hasattr(self.belt, "healthy"):
            ramp = self._belt_v / max(self.cfg.belt.accel_mm_s2, 1.0)
            if now - self._belt_t0 > self.belt_grace_s + ramp and not self.belt.healthy(self.belt_timeout_s):
                n_ok, n_bad = getattr(self.belt, "n_lines", "?"), getattr(self.belt, "n_bad_lines", "?")
                raise BeltCommError(
                    f"băng đã ra lệnh chạy {self._belt_v:.0f} mm/s nhưng không có dòng bộ đếm mới trong {self.belt_timeout_s} s "
                    f"(dòng khớp line_regex: {n_ok}, không khớp: {n_bad}, dòng cuối: {getattr(self.belt, 'last_line', '')!r}). "
                    "Nếu chưa từng có dòng khớp: sai cổng/baud/line_regex hoặc firmware không gửi; nếu đang có rồi thì mất liên lạc serial.")

    def wait_tick(self) -> float:
        now = self.clock()
        self.check_links(now)
        if self._next is None:
            self._next = now
        self._next += self.period
        late = now - self._next
        self.n_ticks += 1
        if late > 0.5 * self.period:
            self.n_late += 1
            self.max_late_s = max(self.max_late_s, late)
        if late > 5 * self.period:                      # tụt quá xa: đồng bộ lại thay vì chạy bù
            self._next = now
        else:
            dt = self._next - now
            if dt > 0:
                self._sleep(dt)
        return self.clock()

    def start_belt(self, v_mm_s: float) -> None:
        self.belt.start(v_mm_s)
        self._belt_v, self._belt_t0 = float(v_mm_s), self.clock()

    def stop_belt(self) -> None:
        self._belt_v = 0.0
        self.belt.stop()
