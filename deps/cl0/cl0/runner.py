"""Vòng điều khiển một lượt CL-0 trên một ``Platform`` (phần cứng thật hoặc mô phỏng).

``Platform`` che phần việc phụ thuộc môi trường: đồng hồ, khung ảnh mới, trạng thái robot, gửi lệnh, nhịp điều khiển.
Mô phỏng chạy theo thời gian ẢO (nhanh hơn thời gian thật); phần cứng chạy theo ``time.monotonic()``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Protocol, Tuple

from .controller import CL0Controller
from .types import BeltLike, Command, Frame, RobotState


class Platform(Protocol):
    belt: BeltLike

    def now(self) -> float: ...
    def poll_frame(self) -> Optional[Frame]: ...          # khung MỚI kể từ lần gọi trước (hoặc None)
    def robot_state(self) -> RobotState: ...
    def send(self, cmd: Command) -> None: ...
    def wait_tick(self) -> float: ...                     # chờ (thật) hoặc chạy mô phỏng (ảo) tới nhịp kế; trả thời gian mới
    def start_belt(self, v_mm_s: float) -> None: ...
    def stop_belt(self) -> None: ...


@dataclass
class RunResult:
    outcome: str                          # theo bộ điều khiển (xem controller.py)
    t_end: float
    phases: List[Tuple[float, str]]
    events: list
    log: List[dict]
    diag: dict
    finished: bool                        # False nếu vòng bị cắt bởi t_limit_s
    t_start: float = 0.0


def run_controller(ctrl: CL0Controller, platform: Platform, t_limit_s: float = 120.0,
                   on_tick: Optional[Callable[[float, Optional[Frame], RobotState, Command], None]] = None) -> RunResult:
    t = platform.now()
    t0 = t
    ctrl.reset(t, platform.robot_state())
    while True:
        frame = platform.poll_frame()
        state = platform.robot_state()
        cmd = ctrl.step(t, frame, platform.belt, state)
        platform.send(cmd)
        if on_tick is not None:
            on_tick(t, frame, state, cmd)
        if ctrl.finished or (t - t0) > t_limit_s:
            break
        t = platform.wait_tick()
    phases = [(e.t, e.name[6:]) for e in ctrl.events if e.name.startswith("phase:")]
    return RunResult(ctrl.outcome or ("" if ctrl.finished else "running"), t, phases, ctrl.events, ctrl.log, dict(ctrl.diag),
                     ctrl.finished, t0)
