"""Adapter LeRobot cho SO-101 follower. Chỉ phần này (và camera/băng) chạm phần cứng; bộ điều khiển không biết gì về LeRobot.

Đã ĐỐI CHIẾU VỚI MÃ NGUỒN lerobot 0.6.1 (đọc ``robots/so_follower/{so_follower,config_so_follower}.py`` và ``motors/motors_bus.py``;
KHÔNG chạy với robot thật, [chưa kiểm trên máy bạn]):
  * ``from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig``; ``SO101FollowerConfig(port, id, use_degrees=True,
    max_relative_target=...)``. Bản cũ hơn dùng ``lerobot.robots.so101_follower`` - ``make_so101`` thử cả hai;
  * ``robot.connect()`` (nếu hiệu chuẩn trong động cơ lệch file hiệu chuẩn của ``id`` thì LeRobot HỎI bằng ``input()``: Enter = dùng file;
    nếu KHÔNG có file thì nó tự hiệu chuẩn mới và ghi đè động cơ => ``check_calibration_file`` chặn trước; file nằm ở
    ``<HF_LEROBOT_CALIBRATION>/robots/so_follower/<id>.json`` (0.6.1; bản cũ: ``.../robots/so101_follower/``)),
    ``robot.get_observation()`` -> {"shoulder_pan.pos": ..., ..., "gripper.pos": ...},
    ``robot.send_action({"<khớp>.pos": ...})``, ``robot.disconnect()``, ``robot.bus.enable_torque()/disable_torque()``;
  * ``use_degrees=True`` (mặc định của 0.6.1): các khớp tay tính bằng ĐỘ (0° = giữa tầm chuyển động đã hiệu chuẩn), gripper trong [0, 100].
Có thể thay hoàn toàn bằng lớp của bạn: ``--arm-adapter mô_đun:Lớp`` (cần ``connect/state/send/torque/disconnect``).
"""
from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np

from ..config import RobotCfg
from ..types import LinkLost, RobotState

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")


class SafetyError(RuntimeError):
    pass


class ArmCommError(LinkLost):
    """Mất liên lạc với servo (serial/bus lỗi, rút cáp, hết nguồn): theo §4.3 là lỗi phần cứng, lượt KHÔNG hợp lệ."""


def make_so101(cfg: RobotCfg):
    """Tạo đối tượng robot LeRobot SO-101 follower, thử nhiều đường import."""
    errs = []
    candidates = [
        ("lerobot.robots.so101_follower", "SO101Follower", "SO101FollowerConfig"),
        ("lerobot.robots.so_follower", "SO101Follower", "SO101FollowerConfig"),
        ("lerobot.robots.so_follower", "SOFollower", "SO101FollowerConfig"),
        ("lerobot.common.robots.so101_follower", "SO101Follower", "SO101FollowerConfig"),
    ]
    kw = dict(port=cfg.port, id=cfg.robot_id, use_degrees=True)
    if cfg.max_relative_target and cfg.max_relative_target > 0:
        kw["max_relative_target"] = cfg.max_relative_target
    for mod, cls, ccls in candidates:
        try:
            m = importlib.import_module(mod)
            return getattr(m, cls)(getattr(m, ccls)(**kw))
        except Exception as e:                       # noqa: BLE001
            errs.append(f"{mod}.{cls}: {type(e).__name__}: {e}")
    try:                                              # đường chung qua registry cấu hình
        from lerobot.robots import RobotConfig, make_robot_from_config
        return make_robot_from_config(RobotConfig.get_choice_class("so101_follower")(**kw))
    except Exception as e:                           # noqa: BLE001
        errs.append(f"registry so101_follower: {type(e).__name__}: {e}")
    raise RuntimeError("không tạo được robot LeRobot SO-101:\n  " + "\n  ".join(errs) +
                       "\nKiểm tra `pip show lerobot`, phiên bản, và truyền adapter riêng bằng --arm-adapter.")


class LeRobotArm:
    def __init__(self, cfg: RobotCfg, clock: Callable[[], float] = time.monotonic, robot=None,
                 limits_deg: Optional[np.ndarray] = None, max_jump_deg: float = 30.0):
        self.cfg, self.clock = cfg, clock
        self._robot = robot
        self.limits = None if limits_deg is None else np.asarray(limits_deg, float)       # (5, 2) [min, max]
        self.max_jump = max_jump_deg
        self._q_goal: Optional[np.ndarray] = None
        self._g_goal: Optional[float] = None
        self._last_q_meas: Optional[np.ndarray] = None

    # ----------------------------------------------------------------------------------------------- vòng đời
    def check_calibration_file(self) -> None:
        """Chốt chặn TRƯỚC ``robot.connect()``: LeRobot thiếu file hiệu chuẩn của ``id`` thì tự chạy hiệu chuẩn MỚI (hỏi bằng ``input()``,
        rồi GHI lại thanh ghi lệch-gốc của động cơ). Điều đó đổi "0°" của tay so với tay leader và dữ liệu cũ, nên không bao giờ để nó xảy ra ngầm.
        Bản LeRobot 0.6.1 tìm ở ``<HF_LEROBOT_CALIBRATION>/robots/so_follower/<id>.json``; bản cũ lưu ở ``.../robots/so101_follower/<id>.json``.
        Đối tượng robot giả/không có ``calibration_fpath`` thì bỏ qua."""
        fp = getattr(self._robot, "calibration_fpath", None)
        if fp is None:
            return
        fp = Path(fp)
        if fp.is_file():
            return
        root = fp.parent.parent
        others = sorted(q for q in root.glob(f"*/{fp.name}") if q != fp) if root.is_dir() else []
        hint = (f"Có file cùng tên ở: {', '.join(str(q) for q in others)}. Nếu đó là hiệu chuẩn của CHÍNH tay follower này (bản LeRobot cũ lưu ở thư mục khác), "
                f"chép (cp, không mv) sang {fp} rồi chạy lại." if others else
                "Không thấy file cùng tên ở thư mục robot nào khác. Kiểm tra lại `robot.robot_id` trong cấu hình; nếu tay chưa từng hiệu chuẩn thì chạy "
                "`lerobot-calibrate` riêng cho follower (và leader), rồi chạy lại.")
        raise RuntimeError(f"Không thấy file hiệu chuẩn LeRobot của robot_id={self.cfg.robot_id!r}: {fp}\n"
                           "Thiếu file thì LeRobot tự chạy hiệu chuẩn MỚI và ghi đè thanh ghi lệch-gốc của động cơ (làm lệch '0°' so với tay leader và dữ liệu cũ) "
                           "nên mình dừng ở đây, chưa kết nối.\n" + hint)

    def connect(self) -> None:
        if self._robot is None:
            self._robot = make_so101(self.cfg)
        if not getattr(self._robot, "is_connected", False):
            self.check_calibration_file()
            self._robot.connect()
        use_deg = getattr(getattr(self._robot, "config", None), "use_degrees", None)
        if use_deg is False:
            raise RuntimeError("robot đang ở chế độ chuẩn hoá -100..100; cần use_degrees=True để FK đúng")
        st = self.state()
        self._q_goal, self._g_goal = st.q_deg.copy(), st.gripper
        if np.any(np.abs(st.q_deg) > 200):
            raise RuntimeError(f"góc khớp đọc về bất thường {st.q_deg.round(1)}: có thể đang ở chế độ -100..100 hoặc hiệu chuẩn hỏng")

    def disconnect(self) -> None:
        if self._robot is not None:
            try:
                self._robot.disconnect()
            finally:
                self._robot = None

    def torque(self, on: bool) -> None:
        bus = getattr(self._robot, "bus", None)
        if bus is None:
            raise RuntimeError("robot không có bus để bật/tắt torque")
        if on:
            self._q_goal = None
            bus.enable_torque()
        else:
            bus.disable_torque()

    # ----------------------------------------------------------------------------------------------- đọc / ghi
    def state(self) -> RobotState:
        try:
            obs = self._robot.get_observation()
        except (ConnectionError, TimeoutError, OSError) as e:        # gồm serial.SerialException và DeviceNotConnectedError của LeRobot
            raise ArmCommError(f"mất liên lạc với servo khi đọc trạng thái: {type(e).__name__}: {e}") from e
        t = self.clock()
        q = np.array([float(obs[f"{j}.pos"]) for j in JOINTS])
        self._last_q_meas = q
        return RobotState(q, float(obs["gripper.pos"]), t)

    def send(self, q_deg: Optional[Sequence[float]], gripper: Optional[float]) -> None:
        if q_deg is not None:
            q = np.asarray(q_deg, float)
            if q.shape != (5,) or not np.all(np.isfinite(q)):
                raise SafetyError(f"lệnh khớp không hợp lệ: {q}")
            if self.limits is not None:
                q = np.clip(q, self.limits[:, 0], self.limits[:, 1])
            ref = self._last_q_meas if self._last_q_meas is not None else self._q_goal
            if ref is not None and np.max(np.abs(q - ref)) > self.max_jump:
                raise SafetyError(f"lệnh nhảy {np.max(np.abs(q - ref)):.1f}° so với vị trí đo > {self.max_jump}°: dừng (nghi lỗi dấu/IK)")
            self._q_goal = q
        if gripper is not None:
            if not np.isfinite(gripper):
                raise SafetyError("lệnh kẹp không hợp lệ")
            self._g_goal = float(np.clip(gripper, 0.0, 100.0))
        if self._q_goal is None or self._g_goal is None:
            return
        act = {f"{j}.pos": float(v) for j, v in zip(JOINTS, self._q_goal)}
        act["gripper.pos"] = self._g_goal
        try:
            self._robot.send_action(act)
        except (ConnectionError, TimeoutError, OSError) as e:
            raise ArmCommError(f"mất liên lạc với servo khi gửi lệnh: {type(e).__name__}: {e}") from e


def go_to(arm, platform_clock: Callable[[], float], q_target: np.ndarray, gripper: float, duration_s: float, hz: float = 50.0,
          sleep: Callable[[float], None] = time.sleep) -> None:
    """Đưa tay tới q_target bằng nội suy min-jerk trong không gian khớp (dùng khi bắt đầu / kết thúc phiên).

    Đọc lại trạng thái MỖI nhịp: kiểm tra 'nhảy' của ``LeRobotArm.send`` so lệnh với vị trí đo gần nhất; nếu chỉ đọc một lần ở đầu thì
    chuyển động dài hơn ``max_jump_deg`` (vd. từ tư thế gập về nhà) sẽ bị chặn nhầm giữa chừng."""
    st = arm.state()
    q0 = st.q_deg.copy()
    dq = float(np.max(np.abs(np.asarray(q_target, float) - q0)))
    T = max(duration_s, 1.875 * dq / 100.0)           # đỉnh <= 100°/s
    t0 = platform_clock()
    while True:
        arm.state()
        tau = (platform_clock() - t0) / T
        tt = min(max(tau, 0.0), 1.0)
        f = 10 * tt ** 3 - 15 * tt ** 4 + 6 * tt ** 5
        arm.send(q0 + (np.asarray(q_target, float) - q0) * f, gripper)
        if tau >= 1.0:
            break
        sleep(1.0 / hz)
