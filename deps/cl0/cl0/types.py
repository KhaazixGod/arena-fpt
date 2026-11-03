"""Kiểu dữ liệu dùng chung giữa bộ điều khiển và các adapter (phần cứng thật hay mô phỏng)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Tuple

import numpy as np


@dataclass
class Frame:
    img: np.ndarray            # BGR uint8
    t_capture: float           # thời điểm chụp ƯỚC LƯỢNG theo đồng hồ chủ (= lúc nhận - độ trễ camera đã đo)


@dataclass
class RobotState:
    q_deg: np.ndarray          # 5 khớp tay (độ), thứ tự shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll
    gripper: float             # gripper.pos (0–100)
    t: float


@dataclass
class Command:
    q_deg: Optional[np.ndarray]   # None = giữ nguyên lệnh trước
    gripper: Optional[float]
    phase: str
    note: str = ""


class BeltLike(Protocol):
    def s_at(self, t: float) -> float: ...         # độ dịch băng (mm) tại thời điểm t (đồng hồ chủ)
    def speed_at(self, t: float) -> float: ...     # mm/s


@dataclass
class TrialEvent:
    t: float
    name: str
    data: dict = field(default_factory=dict)


class LinkLost(RuntimeError):
    """Mất liên lạc với một thiết bị (camera, bộ đếm băng...) giữa lượt. Theo §4.3 của kế hoạch, lỗi phần cứng/mất giao tiếp là lượt
    KHÔNG hợp lệ (phải chạy lại); ``run_g0`` mặc định gợi ý phân loại đó cho loại lỗi này (người thử vẫn là người quyết định)."""
