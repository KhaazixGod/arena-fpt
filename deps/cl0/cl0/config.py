"""Cấu hình CL-0. Mọi đơn vị: mm, giây, độ (trừ ghi chú khác). Đọc từ TOML; khoá lạ báo lỗi (tránh gõ sai tên mà không hay).

Các tham số tinh chỉnh trong "2 ngày" của §3.4 nằm ở các mục [perception], [perception.grasp], [executor], [track].
Sau khi đóng băng, lưu bản sao file này cùng ``sha256sum`` (xem README_CL0.md).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Tuple

from .grasp import GraspParams
from .perception import PerceptionParams


@dataclass
class CameraCfg:
    device: Any = 0                   # chỉ số /dev/videoN hoặc đường dẫn
    width: int = 640
    height: int = 480
    fps: int = 30
    fourcc: str = "MJPG"
    latency_s: float = 0.10           # độ trễ camera -> PC đã đo (§3.1 dòng 2); dùng để quy dấu thời gian khung về lúc chụp


@dataclass
class BeltCfg:
    speed_mm_s: float = 50.0          # tốc độ chạy trong lượt thử (chọn theo L = v·tau/w, §3.1)
    mm_per_step: float = 0.0          # điền sau khi hiệu chuẩn (cl0.calibrate belt)
    textured: bool = False
    period_mm: float = 0.0            # chu vi băng, cần khi textured = true
    accel_mm_s2: float = 200.0        # dốc tăng/giảm tốc của băng (firmware); dùng cho mô hình s(t) khi không có bộ đếm
    width_mm: float = 150.0           # bề rộng băng (cho cửa sổ nhìn / sinh sắp xếp)
    # --- cách biết s(t) ---
    kind: str = "model"               # "model": s(t) tính từ lệnh (vận tốc + dốc gia tốc); "counter": đọc bộ đếm xung qua serial
    serial_port: str = ""             # cổng serial của vi điều khiển băng ("" = không gửi lệnh / không đọc)
    serial_baud: int = 115200
    serial_open_delay_s: float = 2.0  # chờ sau khi mở cổng: Arduino/ESP tự reset khi mở cổng serial (DTR) và bỏ qua lệnh trong lúc khởi động
    cmd_speed: str = "V {steps_per_s:.2f}\n"      # dòng lệnh đặt tốc độ; trường: steps_per_s, v_mm_s
    cmd_stop: str = "V 0\n"
    line_regex: str = "^S[ ,:]+(-?\\d+)"          # nhóm 1 = số xung tích luỹ (kind = counter)
    serial_latency_s: float = 0.003   # trễ từ lúc vi điều khiển đếm tới lúc PC nhận dòng
    cmd_delay_s: float = 0.05         # trễ từ lúc PC gửi lệnh tới lúc băng bắt đầu đổi tốc độ (kind = model)


@dataclass
class RobotCfg:
    port: str = "/dev/ttyACM0"
    robot_id: str = "my_follower"
    urdf: str = ""                    # rỗng = dùng số liệu URDF chính thức nhúng sẵn
    tcp_offset_mm: Tuple[float, float, float] = (0.0, 0.0, 0.0)   # trong khung gripper_frame_link
    tilt_deg: float = 90.0            # góc chúc cố định của trục tiến vào (90 = thẳng xuống)
    joint_margin_deg: float = 3.0
    q_dot_max_deg_s: float = 150.0    # chặn tốc độ khớp ở lệnh gửi đi (an toàn)
    home_q_deg: Tuple[float, ...] = (0.0, -49.0, 48.0, 91.0, 0.0)      # ví dụ; đặt lại theo thiết lập của bạn
    hold_q_deg: Tuple[float, ...] = (0.0, -37.0, 41.0, 86.0, 0.0)    # tư thế giữ vật 2 s sau khi nhấc (cố định trong W)
    gripper_open: float = 60.0        # giá trị gripper.pos (0–100) khi mở để kẹp; độ mở hữu dụng w (mm) tương ứng điền ở perception.grasp.gripper_w_mm
    gripper_closed: float = 0.0
    gripper_held_margin: float = 6.0  # kẹp dừng cao hơn closed + margin => có vật
    max_relative_target: float = 0.0  # 0 = không dùng của LeRobot (bộ thực thi tự chặn tốc độ)


@dataclass
class ExecCfg:
    control_hz: float = 50.0
    z_grasp_above_belt_mm: float = 10.0   # độ cao TCP khi kẹp so với mặt băng (cố định, CL-0 không biết chiều cao vật)
    pre_height_mm: float = 40.0
    lift_height_mm: float = 60.0
    min_z_above_belt_mm: float = 3.0      # chặn cứng: không bao giờ ra lệnh thấp hơn
    omega_xy: float = 7.0                 # rad/s, bộ lọc tới hạn trong hệ băng
    vmax_xy: float = 300.0                # mm/s trong hệ băng
    omega_z: float = 9.0
    vmax_z: float = 150.0
    omega_yaw: float = 9.0
    vmax_yaw: float = 360.0               # độ/s
    tol_xy_mm: float = 4.0
    tol_meas_xy_mm: float = 6.0           # sai lệch đo được (FK của khớp đọc về) cho phép trước khi hạ
    tol_z_mm: float = 2.5
    tol_yaw_deg: float = 6.0
    settle_s: float = 0.20
    lead_s: float = 0.0                   # dẫn trước bù độ trễ cánh tay: dùng s(t + lead)  [đo bằng cl0.calibrate lag]
    lag_ki: float = 2.5                   # 1/s; tích phân bù (lệnh gốc − đo được) cho trễ servo / võng trọng lực; 0 = tắt
    lag_int_max_mm: float = 25.0
    lag_int_window_mm: float = 30.0       # chỉ tích phân khi sai lệch nhỏ hơn mức này
    lag_int_vmax_mm_s: float = 40.0       # và khi bộ lọc gần tĩnh (tốc độ hệ băng nhỏ hơn mức này)
    freeze_radius_mm: float = 45.0        # ngừng cập nhật mục tiêu khi TCP vào gần (đầu kẹp che vật)
    arm_exclusion_mm: float = 55.0        # bỏ phát hiện có tâm trong bán kính này quanh TCP
    close_wait_s: float = 0.7
    lift_wait_s: float = 0.6
    hold_s: float = 2.0
    move_hold_s: float = 1.0
    trial_timeout_s: float = 20.0
    t_to_grasp_s: float = 1.8             # ước lượng thời gian từ lúc chọn tới lúc kẹp; vật phải nằm trong vùng với tới ngay lúc chọn, giữa chừng, lúc kẹp và lúc nhấc
    follow_margin_s: float = 1.0          # vật còn phải ở trong vùng với tới thêm chừng này sau khi kẹp (tới hết lúc nhấc)
    ik_fail_abort_s: float = 0.6
    t_after_settle_s: float = 2.1         # từ lúc ổn định ở độ cao chờ tới lúc nhấc xong (hạ + khép + nhấc); dùng kiểm khả thi trước khi hạ
    lift_timeout_s: float = 2.0           # quá hạn (hoặc IK hỏng khi nhấc) thì vẫn chuyển sang tư thế giữ
    hard_timeout_s: float = 45.0          # chốt cứng cho cả lượt: sau mức này mở kẹp và về nhà
    move_peak_deg_s: float = 150.0        # đỉnh tốc độ khớp khi di chuyển trong không gian khớp (kéo dài thời gian nếu cần)
    a_pick_min: float = -1e9              # cửa sổ nhặt bổ sung theo a (W-căn-theo-băng); mặc định không giới hạn
    a_pick_max: float = 1e9


@dataclass
class TrackCfg:
    gate_mm: float = 12.0
    n_confirm: int = 3
    window: int = 6
    max_std_mm: float = 5.0               # độ lệch chuẩn lớn hơn => chưa ổn định (vật đang trượt / mặt nạ nhảy)
    lost_s: float = 1.5


@dataclass
class Config:
    camera: CameraCfg = field(default_factory=CameraCfg)
    belt: BeltCfg = field(default_factory=BeltCfg)
    robot: RobotCfg = field(default_factory=RobotCfg)
    executor: ExecCfg = field(default_factory=ExecCfg)
    track: TrackCfg = field(default_factory=TrackCfg)
    perception: PerceptionParams = field(default_factory=PerceptionParams)
    calib_path: str = "calib.json"
    background_path: str = "background.npz"


def _build(cls, d: dict, path: str = ""):
    fields = {f.name: f for f in dataclasses.fields(cls)}
    bad = set(d) - set(fields)
    if bad:
        raise KeyError(f"khoá lạ trong cấu hình {path or '(gốc)'}: {sorted(bad)}; hợp lệ: {sorted(fields)}")
    kw = {}
    for name, v in d.items():
        f = fields[name]
        default = f.default_factory() if f.default_factory is not dataclasses.MISSING else f.default
        if dataclasses.is_dataclass(default) and isinstance(v, dict):
            kw[name] = _build(type(default), v, f"{path}.{name}" if path else name)
        elif isinstance(default, tuple):
            kw[name] = tuple(v)
        else:
            kw[name] = v
    return cls(**kw)


def config_from_dict(d: dict) -> Config:
    return _build(Config, dict(d))


def load_config(path: str) -> Config:
    try:
        import tomllib
    except ModuleNotFoundError:          # Python < 3.11
        import tomli as tomllib          # type: ignore
    with open(path, "rb") as f:
        return config_from_dict(tomllib.load(f))


def dump_config(cfg: Config) -> dict:
    return dataclasses.asdict(cfg)


# ------------------------------------------------------------------------------------------------------------ mẫu cấu hình
_TEMPLATE_HEAD = """# Cấu hình CL-0 — SINH TỰ ĐỘNG từ giá trị mặc định trong cl0/config.py (python -m cl0.config > configs/config_template.toml).
# Đơn vị: mm, giây, độ (trừ ghi chú). Khoá lạ => báo lỗi. Chỉ cần ghi những khoá bạn muốn đổi; khoá vắng mặt lấy mặc định.
#
# PHẢI chỉnh cho máy của bạn (mặc định chỉ là ví dụ):
#   [camera]   device, width/height/fps (đúng độ phân giải đã hiệu chuẩn), latency_s (đo bằng `calibrate belt`)
#   [belt]     kind + serial_port + cmd_speed/cmd_stop/line_regex (khớp firmware của bạn), mm_per_step (đo bằng `calibrate belt`), speed_mm_s, width_mm
#   [robot]    port, robot_id (đúng tên đã hiệu chuẩn bằng lerobot-calibrate), tcp_offset_mm (điểm bạn coi là tâm kẹp), home_q_deg/hold_q_deg
#   [perception.grasp] gripper_w_mm (độ mở hữu dụng đo bằng thước ở giá trị robot.gripper_open)
#   [executor] a_pick_min/a_pick_max (từ `python -m cl0.tune reach`), lead_s (từ `calibrate lag`)
# Sau khi tinh chỉnh xong: `python -m cl0.freeze --config <file>` rồi KHÔNG đổi nữa (xem README_CL0.md).
"""


def _toml_val(v) -> str:
    import json
    import math
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        if math.isinf(v):
            return "inf" if v > 0 else "-inf"
        if abs(v) >= 1e6 and v == round(v):
            return f"{v:.0e}"
        return repr(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (tuple, list)):
        return "[" + ", ".join(_toml_val(x) for x in v) + "]"
    raise TypeError(f"không biểu diễn được {type(v)} trong TOML")


def template_toml(cfg: "Config | None" = None) -> str:
    """Bản TOML đầy đủ (mọi khoá, kèm chú thích lấy từ mã nguồn) của cấu hình mặc định — luôn khớp với mã."""
    import inspect
    import re
    cfg = cfg or Config()
    out = [_TEMPLATE_HEAD]

    def comments(cls) -> dict:
        cm = {}
        for ln in inspect.getsource(cls).splitlines():
            m = re.match(r"^\s{4}(\w+)\s*:\s*[^#=]+=[^#]*#\s?(.*)$", ln)
            if m:
                cm[m.group(1)] = m.group(2).strip()
        return cm

    def emit(obj, path: str, top: bool = False) -> None:
        cm = comments(type(obj))
        scal, subs = [], []
        for f in dataclasses.fields(obj):
            v = getattr(obj, f.name)
            (subs if dataclasses.is_dataclass(v) else scal).append((f.name, v))
        if not top:
            out.append(f"\n[{path}]")
        for name, v in scal:
            c = cm.get(name, "")
            out.append(f"{name} = {_toml_val(v)}" + (f"    # {c}" if c else ""))
        for name, v in subs:
            emit(v, f"{path}.{name}" if path else name)

    emit(cfg, "", top=True)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys
    sys.stdout.write(template_toml())
