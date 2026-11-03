"""Tầng phần cứng với THIẾT BỊ GIẢ (serial giả, robot LeRobot giả, cv2.VideoCapture giả). Chỉ kiểm logic của adapter:
KHÔNG chứng minh chạy được trên băng/robot/camera thật (tên phương thức LeRobot, firmware băng, V4L2 là giả định - xem README)."""
import threading
import time
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from cl0.config import BeltCfg, CameraCfg, Config, RobotCfg
from cl0.hw.arm import JOINTS, ArmCommError, LeRobotArm, SafetyError, go_to, make_so101
from cl0.hw.belt import Belt
from cl0.hw.camera import CameraThread, ReplayCamera, Undistorter
from cl0.hw.platform import BeltCommError, CameraCommError, HardwarePlatform
from cl0.types import LinkLost
from cl0.types import Command


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def sleep(self, dt):
        self.t += max(dt, 0.0)


def wait_until(pred, timeout=3.0):
    t0 = time.time()
    while not pred():
        if time.time() - t0 > timeout:
            raise AssertionError("hết thời gian chờ điều kiện")
        time.sleep(0.002)


# ================================================================================================================ BĂNG
class FakeSerial:
    def __init__(self):
        self._buf = bytearray()
        self._lock = threading.Lock()
        self.written = []
        self.closed = False

    def feed(self, data):
        with self._lock:
            self._buf += data if isinstance(data, bytes) else data.encode()

    def read(self, n=256):
        with self._lock:
            out, self._buf = bytes(self._buf[:n]), self._buf[n:]
        if not out:
            time.sleep(0.002)
        return out

    def write(self, b):
        self.written.append(b.decode())

    def flush(self):
        pass

    def close(self):
        self.closed = True


def _counter_belt(**kw):
    cfg = BeltCfg(kind="counter", serial_port="/dev/fake", mm_per_step=0.05, serial_latency_s=0.003, **kw)
    ser, clk = FakeSerial(), FakeClock()
    belt = Belt(cfg, clock=clk, serial=ser)
    belt.open()
    return belt, ser, clk


def _feed(belt, ser, clk, t, count):
    n = belt.n_lines
    clk.t = t
    ser.feed(f"S {count}\n")
    wait_until(lambda: belt.n_lines == n + 1)


def test_counter_belt_builds_history_from_serial_lines():
    belt, ser, clk = _counter_belt()
    try:
        for k in range(10):
            _feed(belt, ser, clk, 1.0 + 0.1 * k, 1000 + 50 * k)                     # 500 xung/s = 25 mm/s
        t, s = belt.history()
        assert len(t) == 10 and s[0] == 0.0 and s[-1] == pytest.approx(9 * 50 * 0.05)
        assert t[0] == pytest.approx(1.0 - 0.003)                                  # trừ trễ serial
        assert belt.speed_at(1.9) == pytest.approx(25.0, rel=0.02)
        assert belt.s_at(t[4]) == pytest.approx(s[4])
        assert belt.s_at(t[-1] + 0.05) == pytest.approx(s[-1] + 25.0 * 0.05, rel=0.02)   # ngoại suy theo độ dốc cuối
        assert belt.s_at(t[0] - 1.0) == pytest.approx(0.0)
    finally:
        belt.close()
    assert ser.closed


def test_counter_belt_handles_split_lines_and_garbage():
    belt, ser, clk = _counter_belt()
    try:
        clk.t = 5.0
        ser.feed("hello\n")
        wait_until(lambda: belt.n_bad_lines == 1)
        ser.feed("S 20")
        time.sleep(0.05)
        assert belt.n_lines == 0                                                    # dòng chưa đủ: chưa phân tích
        clk.t = 5.1
        ser.feed("00\n")
        wait_until(lambda: belt.n_lines == 1)
        clk.t = 5.2
        ser.feed("S,2040\n")
        wait_until(lambda: belt.n_lines == 2)
        _, s = belt.history()
        assert s[0] == 0.0 and s[1] == pytest.approx(40 * 0.05)
        assert belt.last_line == "S,2040"
    finally:
        belt.close()


def test_counter_belt_keeps_the_newest_count_when_several_lines_arrive_together():
    """Nhiều dòng trong một lần đọc có cùng dấu thời gian: giữ số đếm MỚI nhất (trước đây dòng cũ chiếm chỗ và mất dòng mới)."""
    belt, ser, clk = _counter_belt()
    try:
        _feed(belt, ser, clk, 3.0, 100)
        clk.t = 3.5
        ser.feed("S 150\nS 200\nS 250\n")
        wait_until(lambda: belt.n_lines == 4)
        t, s = belt.history()
        assert len(t) == 2 and s[-1] == pytest.approx(150 * 0.05)
    finally:
        belt.close()


def test_counter_belt_commands_follow_the_configured_templates():
    belt, ser, clk = _counter_belt()
    try:
        belt.start(50.0)
        belt.stop()
        assert ser.written == ["V 1000.00\n", "V 0\n"]
    finally:
        belt.close()


def test_custom_firmware_strings_come_from_config_without_code_changes():
    cfg = BeltCfg(kind="counter", serial_port="x", mm_per_step=0.1, cmd_speed="SPD {v_mm_s:.1f} {steps_per_s:.0f}\r\n", cmd_stop="HALT\r\n",
                  line_regex=r"^POS=(-?\d+)")
    ser = FakeSerial()
    clk = FakeClock(2.0)
    belt = Belt(cfg, clock=clk, serial=ser)
    belt.open()
    try:
        belt.start(30.0)
        belt.stop()
        assert ser.written == ["SPD 30.0 300\r\n", "HALT\r\n"]
        ser.feed("POS=7\n")
        wait_until(lambda: belt.n_lines == 1)
        clk.t = 2.1
        ser.feed("POS=107\n")
        wait_until(lambda: belt.n_lines == 2)
        assert belt.history()[1][-1] == pytest.approx(10.0)
    finally:
        belt.close()


def test_counter_belt_health_requires_recent_lines():
    belt, ser, clk = _counter_belt()
    try:
        assert not belt.healthy()
        _feed(belt, ser, clk, 10.0, 0)
        clk.t = 10.2
        assert belt.healthy(0.5)
        clk.t = 11.0
        assert not belt.healthy(0.5)
    finally:
        belt.close()


def test_counter_belt_open_validates_configuration():
    with pytest.raises(RuntimeError, match="serial_port"):
        Belt(BeltCfg(kind="counter", serial_port="", mm_per_step=0.05)).open()
    with pytest.raises(RuntimeError, match="mm_per_step"):
        Belt(BeltCfg(kind="counter", serial_port="x", mm_per_step=0.0), serial=FakeSerial()).open()


def test_opening_a_real_port_waits_for_board_reset_and_drops_boot_noise(monkeypatch):
    """Arduino/ESP tự reset khi mở cổng serial: lệnh gửi ngay sau khi mở bị mất. Belt.open() phải chờ rồi bỏ rác khởi động."""
    import sys
    import types as _types
    import cl0.hw.belt as belt_mod
    events = []

    class PortSerial(FakeSerial):
        def reset_input_buffer(self):
            events.append("reset_input")

    fake_mod = _types.SimpleNamespace(Serial=lambda port, baud, timeout=None: (events.append(f"open {port} {baud}"), PortSerial())[1])
    monkeypatch.setitem(sys.modules, "serial", fake_mod)
    monkeypatch.setattr(belt_mod.time, "sleep", lambda dt: events.append(f"sleep {dt}"))
    belt = Belt(BeltCfg(kind="model", serial_port="/dev/ttyUSB7", serial_baud=57600, serial_open_delay_s=2.0))
    belt.open()
    assert events == ["open /dev/ttyUSB7 57600", "sleep 2.0", "reset_input"]
    events.clear()
    Belt(BeltCfg(kind="model", serial_port="/dev/ttyUSB7", serial_open_delay_s=0.0)).open()
    assert "sleep 0.0" not in events and events[-1] == "reset_input"


def test_model_belt_matches_closed_form_ramp_and_plateau():
    cfg = BeltCfg(kind="model", accel_mm_s2=200.0, cmd_delay_s=0.05)
    clk = FakeClock(0.0)
    belt = Belt(cfg, clock=clk)
    belt.start(50.0)
    assert belt.s_at(0.0) == 0.0 and belt.speed_at(0.04) == 0.0                    # trễ lệnh 50 ms
    assert belt.speed_at(0.2) == pytest.approx(30.0)                               # 200·(0,2−0,05)
    assert belt.s_at(0.30) == pytest.approx(6.25)
    assert belt.s_at(1.0) == pytest.approx(6.25 + 50.0 * 0.70)
    assert belt.speed_at(1.0) == pytest.approx(50.0)
    clk.t = 2.0
    belt.stop()
    assert belt.s_at(2.05) == pytest.approx(6.25 + 50.0 * 1.75)
    assert belt.s_at(2.30) == pytest.approx(100.0)
    assert belt.speed_at(3.0) == 0.0 and belt.s_at(9.0) == pytest.approx(100.0)
    assert belt.healthy()


def test_model_belt_difference_is_what_matters():
    """Với băng trơn chỉ cần HIỆU s(t_now) − s(t_img) = v·Δt: mô hình phải cho đúng v·Δt khi đã ổn định."""
    belt = Belt(BeltCfg(kind="model", accel_mm_s2=200.0, cmd_delay_s=0.05), clock=FakeClock(0.0))
    belt.start(60.0)
    assert belt.s_at(5.0) - belt.s_at(4.88) == pytest.approx(60.0 * 0.12)


# ================================================================================================================ TAY
class FakeBus:
    def __init__(self):
        self.calls = []

    def enable_torque(self):
        self.calls.append("on")

    def disable_torque(self):
        self.calls.append("off")


class FakeRobot:
    def __init__(self, q=(0.0, -49.0, 48.0, 91.0, 0.0), grip=60.0, use_degrees=True):
        self.config = SimpleNamespace(use_degrees=use_degrees)
        self.is_connected = False
        self.q, self.grip = list(q), grip
        self.sent = []
        self.bus = FakeBus()

    def connect(self):
        self.is_connected = True

    def disconnect(self):
        self.is_connected = False

    def get_observation(self):
        obs = {f"{j}.pos": v for j, v in zip(JOINTS, self.q)}
        obs["gripper.pos"] = self.grip
        return obs

    def send_action(self, act):
        self.sent.append(dict(act))
        self.q = [act[f"{j}.pos"] for j in JOINTS]
        self.grip = act["gripper.pos"]


def _arm(robot=None, **kw):
    robot = robot or FakeRobot()
    arm = LeRobotArm(RobotCfg(), clock=FakeClock(1.0), robot=robot, **kw)
    arm.connect()
    return arm, robot


def test_arm_connect_reads_state_in_joint_order():
    arm, robot = _arm()
    st = arm.state()
    assert robot.is_connected and np.allclose(st.q_deg, [0, -49, 48, 91, 0]) and st.gripper == 60.0 and st.t == 1.0


def test_arm_rejects_normalized_mode_and_absurd_angles():
    with pytest.raises(RuntimeError, match="use_degrees"):
        LeRobotArm(RobotCfg(), robot=FakeRobot(use_degrees=False)).connect()
    with pytest.raises(RuntimeError, match="bất thường"):
        LeRobotArm(RobotCfg(), robot=FakeRobot(q=(0, -100, 100, 99, 250))).connect()


def test_arm_send_clips_to_limits_and_converts_names():
    lim = np.array([[-110, 110], [-100, 100], [-97, 97], [-95, 95], [-157, 163]], float)
    arm, robot = _arm(limits_deg=lim, max_jump_deg=200.0)
    arm.send([150, -49, 48, 91, 0], 40.0)
    act = robot.sent[-1]
    assert act["shoulder_pan.pos"] == 110 and act["gripper.pos"] == 40.0 and set(act) == {f"{j}.pos" for j in JOINTS} | {"gripper.pos"}


def test_arm_blocks_large_jumps_and_bad_commands_without_sending():
    arm, robot = _arm()
    n = len(robot.sent)
    for bad in ([40, -49, 48, 91, 0], [np.nan, 0, 0, 0, 0], [0, 0, 0]):
        with pytest.raises(SafetyError):
            arm.send(bad, None)
    with pytest.raises(SafetyError):
        arm.send(None, float("nan"))
    assert len(robot.sent) == n


def test_arm_gripper_is_clipped_and_none_repeats_last_goal():
    arm, robot = _arm()
    arm.send([2, -49, 48, 91, 0], 150.0)
    assert robot.sent[-1]["gripper.pos"] == 100.0
    arm.send(None, None)
    assert robot.sent[-1] == robot.sent[-2]
    arm.send(None, -5.0)
    assert robot.sent[-1]["gripper.pos"] == 0.0 and robot.sent[-1]["shoulder_pan.pos"] == 2.0


def test_arm_jump_check_uses_measured_state_after_state_call():
    arm, robot = _arm()
    arm.send([20, -49, 48, 91, 0], None)                      # 20° < 30° so với đo
    robot.q = [100, -49, 48, 91, 0]                           # tay bị đẩy đi (vd. tắt torque)
    arm.state()
    with pytest.raises(SafetyError):
        arm.send([20, -49, 48, 91, 0], None)                  # cách vị trí đo 80°


def test_servo_communication_errors_become_link_lost_but_logic_errors_do_not():
    """Lỗi bus/serial từ LeRobot (ConnectionError, OSError, TimeoutError) = mất giao tiếp servo (lượt không hợp lệ theo §4.3);
    SafetyError (lệnh nhảy) KHÔNG phải mất liên lạc: nó có thể là lỗi phần mềm nên không được tự "hợp lệ hoá"."""
    for exc in (ConnectionError("Incorrect status packet"), OSError("device disconnected"), TimeoutError("sync_read")):
        arm, robot = _arm()

        def boom(*a, _e=exc, **k):
            raise _e
        robot.get_observation = boom
        with pytest.raises(ArmCommError, match="đọc trạng thái") as ei:
            arm.state()
        assert isinstance(ei.value, LinkLost) and ei.value.__cause__ is exc
    arm, robot = _arm()
    robot.send_action = lambda act: (_ for _ in ()).throw(ConnectionError("rút cáp"))
    with pytest.raises(ArmCommError, match="gửi lệnh"):
        arm.send(np.array([0.0, -49.0, 48.0, 91.0, 0.0]), 10.0)
    assert not issubclass(SafetyError, LinkLost)


class FakeCalibratedRobot(FakeRobot):
    """Như robot LeRobot thật: có ``calibration_fpath``; ``connect()`` mà thiếu file thì LeRobot sẽ tự hiệu chuẩn mới (ở đây: ghi lại vết)."""

    def __init__(self, fpath, **kw):
        super().__init__(**kw)
        self.calibration_fpath = fpath
        self.connect_calls = 0

    def connect(self):
        self.connect_calls += 1
        super().connect()


def test_arm_refuses_to_connect_when_lerobot_calibration_file_is_missing(tmp_path):
    """LeRobot không thấy file hiệu chuẩn của id thì tự hiệu chuẩn lại và ghi đè động cơ: phải chặn TRƯỚC khi gọi connect()."""
    fp = tmp_path / "robots" / "so_follower" / "my_follower.json"
    fp.parent.mkdir(parents=True)
    robot = FakeCalibratedRobot(fp)
    with pytest.raises(RuntimeError, match="hiệu chuẩn MỚI") as e:
        LeRobotArm(RobotCfg(robot_id="my_follower"), robot=robot).connect()
    assert robot.connect_calls == 0 and not robot.is_connected
    assert "my_follower" in str(e.value) and str(fp) in str(e.value) and "lerobot-calibrate" in str(e.value)


def test_missing_calibration_file_hint_points_at_the_old_lerobot_directory(tmp_path):
    old = tmp_path / "robots" / "so101_follower" / "my_follower.json"
    old.parent.mkdir(parents=True)
    old.write_text("{}")
    new = tmp_path / "robots" / "so_follower" / "my_follower.json"
    new.parent.mkdir(parents=True)
    robot = FakeCalibratedRobot(new)
    with pytest.raises(RuntimeError) as e:
        LeRobotArm(RobotCfg(robot_id="my_follower"), robot=robot).connect()
    msg = str(e.value)
    assert str(old) in msg and "cp" in msg and robot.connect_calls == 0
    old.replace(new)                                                  # người dùng chép/chuyển file sang đúng chỗ
    arm = LeRobotArm(RobotCfg(robot_id="my_follower"), robot=robot)
    arm.connect()
    assert robot.connect_calls == 1 and robot.is_connected


def test_calibration_check_is_skipped_for_robots_without_a_calibration_path_and_when_already_connected(tmp_path):
    _arm()                                                            # FakeRobot không có calibration_fpath: vẫn kết nối bình thường
    robot = FakeCalibratedRobot(tmp_path / "missing.json")
    robot.is_connected = True                                         # đã kết nối từ trước (vd. do người dùng mở): không kiểm, không connect lại
    LeRobotArm(RobotCfg(), robot=robot).connect()
    assert robot.connect_calls == 0


def test_arm_torque_switch_and_disconnect():
    arm, robot = _arm()
    arm.torque(False)
    arm.torque(True)
    assert robot.bus.calls == ["off", "on"]
    arm.disconnect()
    assert not robot.is_connected
    with pytest.raises(RuntimeError):
        LeRobotArm(RobotCfg(), robot=SimpleNamespace(bus=None)).torque(True)


def test_go_to_reaches_target_smoothly_and_without_tripping_safety():
    arm, robot = _arm(max_jump_deg=15.0)
    clk = arm.clock
    target = np.array([30.0, -20.0, 20.0, 80.0, 10.0])
    go_to(arm, clk, target, 30.0, duration_s=1.0, hz=50.0, sleep=clk.sleep)
    assert np.allclose(robot.q, target, atol=1e-6) and robot.grip == 30.0
    qs = np.array([[a[f"{j}.pos"] for j in JOINTS] for a in robot.sent])
    speed = np.abs(np.diff(qs, axis=0)).max(axis=1) * 50.0
    assert speed.max() <= 105.0                                # đỉnh <= 100°/s
    T = max(1.0, 1.875 * 49.0 / 100.0)
    assert abs(len(robot.sent) - T * 50) <= 3


def test_make_so101_reports_all_attempts_when_lerobot_is_missing(monkeypatch):
    import importlib
    import sys

    def boom(name, *a, **k):
        raise ModuleNotFoundError(f"No module named '{name.split('.')[0]}'")

    monkeypatch.setattr(importlib, "import_module", boom)
    # đường cuối của make_so101 dùng `from lerobot.robots import ...` (không qua import_module): chặn bằng sys.modules để test cũng
    # đúng khi lerobot ĐÃ được cài trong môi trường chạy test (trên máy có robot thật)
    monkeypatch.setitem(sys.modules, "lerobot", None)
    with pytest.raises(RuntimeError) as e:
        make_so101(RobotCfg(port="/dev/ttyACM9", robot_id="abc", max_relative_target=10.0))
    msg = str(e.value)
    assert "lerobot.robots.so101_follower" in msg and "--arm-adapter" in msg and "registry" in msg


# ================================================================================================================ CAMERA
class FakeCap:
    opened = True
    shape = (240, 320)
    instances = []

    def __init__(self, dev, *a):
        self.dev, self.props, self.n = dev, {}, 0
        FakeCap.instances.append(self)

    def isOpened(self):
        return FakeCap.opened

    def set(self, prop, val):
        self.props[prop] = val
        return True

    def read(self):
        time.sleep(0.003)
        self.n += 1
        img = np.full(FakeCap.shape + (3,), self.n % 250, np.uint8)
        return True, img

    def release(self):
        self.released = True


@pytest.fixture()
def fake_cv2_capture(monkeypatch):
    FakeCap.opened, FakeCap.shape, FakeCap.instances = True, (240, 320), []
    monkeypatch.setattr(cv2, "VideoCapture", FakeCap)
    return FakeCap


class TickClock:
    def __init__(self):
        self.n = 0
        self._lock = threading.Lock()

    def __call__(self):
        with self._lock:
            self.n += 1
            return 100.0 + 0.01 * self.n


def test_camera_timestamps_frames_at_receive_time_minus_latency(fake_cv2_capture):
    cam = CameraThread(CameraCfg(device=0, width=320, height=240, fps=30, latency_s=0.1), clock=TickClock())
    cam.start()
    wait_until(lambda: cam._seq >= 6)
    cam.stop()
    f = cam.poll()
    assert f is not None and f.img.shape == (240, 320, 3)
    n = round((f.t_capture + 0.1 - 100.0) / 0.01)
    assert abs((f.t_capture + 0.1) - (100.0 + 0.01 * n)) < 1e-9                    # đúng t_nhận − latency, không thêm lệch nào khác
    assert cam.poll() is None                                                      # khung chỉ giao một lần
    assert cam.latest() is not None and cam.fps_measured() > 0.0
    assert fake_cv2_capture.instances[0].released


def test_camera_requests_format_size_and_fps(fake_cv2_capture):
    cam = CameraThread(CameraCfg(device=2, width=320, height=240, fps=25, fourcc="MJPG"))
    cam.start()
    cam.stop()
    props = fake_cv2_capture.instances[0].props
    assert props[cv2.CAP_PROP_FRAME_WIDTH] == 320 and props[cv2.CAP_PROP_FRAME_HEIGHT] == 240 and props[cv2.CAP_PROP_FPS] == 25
    assert props[cv2.CAP_PROP_BUFFERSIZE] == 1 and cv2.CAP_PROP_FOURCC in props


def test_camera_open_failure_is_a_clear_error(fake_cv2_capture):
    fake_cv2_capture.opened = False
    with pytest.raises(RuntimeError, match="không mở được camera"):
        CameraThread(CameraCfg(device=7)).start()


def test_camera_warns_about_resolution_mismatch(fake_cv2_capture, capsys):
    cam = CameraThread(CameraCfg(device=0, width=640, height=480))
    cam.start()
    cam.stop()
    assert "CẢNH BÁO" in capsys.readouterr().out


def test_undistorter_is_identity_without_distortion(tmp_path):
    K = np.array([[500.0, 0, 160], [0, 500.0, 120], [0, 0, 1]])
    np.savez(tmp_path / "i.npz", K=K, dist=np.zeros(5))
    img = (np.random.default_rng(0).random((240, 320, 3)) * 255).astype(np.uint8)
    out = Undistorter(str(tmp_path / "i.npz"), (320, 240))(img)
    assert out.shape == img.shape and np.abs(out.astype(int) - img.astype(int)).max() <= 1


def test_replay_camera_plays_frames_once_in_order():
    frames = [(np.full((4, 4, 3), i, np.uint8), 0.1 * i) for i in range(3)]
    cam = ReplayCamera(frames)
    assert cam.latest().t_capture == 0.0
    got = []
    while (f := cam.poll()) is not None:
        got.append(f.t_capture)
    assert got == [0.0, 0.1, 0.2] and cam.poll() is None and cam.latest().t_capture == 0.2


# ================================================================================================================ NỀN TẢNG
def test_platform_paces_ticks_and_counts_overruns():
    clk = FakeClock(10.0)
    slept = []

    def sleep(dt):
        slept.append(dt)
        clk.t += dt

    plat = HardwarePlatform(Config(), None, None, None, clock=clk, sleep=sleep)
    period = plat.period
    assert period == pytest.approx(1.0 / Config().executor.control_hz)
    for _ in range(10):
        plat.wait_tick()
    assert clk.t == pytest.approx(10.0 + 10 * period) and plat.n_late == 0
    clk.t += 0.6 * period                                       # thân vòng lặp tốn 0,6 chu kỳ: phải ngủ phần còn lại
    t0 = clk.t
    plat.wait_tick()
    assert clk.t - t0 == pytest.approx(0.4 * period, abs=1e-9)
    clk.t += 1.8 * period                                       # trễ nhẹ: không ngủ nhưng không bỏ nhịp
    plat.wait_tick()
    assert plat.n_late >= 1 and plat.max_late_s > 0.4 * period
    clk.t += 40 * period                                        # đứng hình lâu: đồng bộ lại, không chạy bù hàng loạt
    n_sleep = len(slept)
    plat.wait_tick()
    assert len(slept) == n_sleep
    plat.wait_tick()
    assert slept[-1] == pytest.approx(period, rel=0.05)


def test_platform_delegates_to_devices():
    calls = []
    arm = SimpleNamespace(state=lambda: "S", send=lambda q, g: calls.append(("send", q, g)))
    cam = SimpleNamespace(poll=lambda: "F")
    belt = SimpleNamespace(start=lambda v: calls.append(("start", v)), stop=lambda: calls.append(("stop",)))
    plat = HardwarePlatform(Config(), cam, arm, belt, clock=FakeClock())
    assert plat.poll_frame() == "F" and plat.robot_state() == "S" and plat.now() == 0.0
    plat.send(Command(np.zeros(5), 12.0, "X"))
    plat.start_belt(40.0)
    plat.stop_belt()
    assert calls[0][0] == "send" and calls[0][2] == 12.0 and calls[1:] == [("start", 40.0), ("stop",)]


# ================================================================================================================ KIỂM TRA LIÊN KẾT
class _FakeCam:
    def __init__(self):
        self.frames = 0
        self.error = None

    def poll(self):
        if self.frames > 0:
            self.frames -= 1
            return "F"
        return None


class _FakeBeltHealth:
    def __init__(self, healthy=True):
        self.ok, self.n_lines, self.n_bad_lines, self.last_line = healthy, 0, 7, "ready"
        self.started = []

    def healthy(self, max_age_s=0.5):
        return self.ok

    def start(self, v):
        self.started.append(v)

    def stop(self):
        self.started.append(0)


def _plat(kind="counter", healthy=True):
    cfg = Config()
    cfg.belt.kind = kind
    clk = FakeClock(100.0)
    cam, belt = _FakeCam(), _FakeBeltHealth(healthy)
    return HardwarePlatform(cfg, cam, None, belt, clock=clk, sleep=clk.sleep), cam, belt, clk


def test_link_errors_are_link_lost_so_run_g0_suggests_invalid():
    assert issubclass(BeltCommError, LinkLost) and issubclass(CameraCommError, LinkLost)


def test_silent_camera_raises_after_timeout_but_not_before():
    plat, cam, _, clk = _plat()
    cam.frames = 1
    plat.poll_frame()
    for _ in range(40):                                        # 40 nhịp ~0,8 s < 1 s im lặng: chưa báo
        plat.wait_tick()
    assert clk.t - 100.0 < 1.0
    with pytest.raises(CameraCommError, match="camera không trả khung"):
        for _ in range(40):
            plat.wait_tick()
    plat2, cam2, _, _ = _plat()                                # chưa từng có khung nào: tính từ nhịp đầu tiên
    with pytest.raises(CameraCommError):
        for _ in range(200):
            plat2.wait_tick()


def test_counter_belt_silence_raises_only_after_grace_and_only_while_running():
    plat, cam, belt, clk = _plat(healthy=False)
    cam.frames = 10 ** 6
    for _ in range(300):                                       # băng chưa được ra lệnh chạy: im lặng là bình thường (lượt tĩnh)
        plat.poll_frame()
        plat.wait_tick()
    plat.start_belt(50.0)
    t0 = clk.t
    with pytest.raises(BeltCommError, match="line_regex"):
        for _ in range(400):
            plat.poll_frame()
            plat.wait_tick()
    grace = plat.belt_grace_s + 50.0 / Config().belt.accel_mm_s2
    assert grace < clk.t - t0 < grace + 0.2                    # không báo sớm trong thời gian chờ (Arduino khởi động, dốc tăng tốc)
    plat.stop_belt()
    plat.reset_run()
    for _ in range(100):                                       # dừng băng: hết kiểm tra
        plat.poll_frame()
        plat.wait_tick()


def test_healthy_belt_never_trips_and_model_belt_is_not_checked():
    plat, cam, belt, clk = _plat(healthy=True)
    cam.frames = 10 ** 6
    plat.start_belt(50.0)
    for _ in range(500):
        plat.poll_frame()
        plat.wait_tick()
    plat3, cam3, belt3, _ = _plat(kind="model", healthy=False)
    cam3.frames = 10 ** 6
    plat3.start_belt(50.0)
    for _ in range(500):
        plat3.poll_frame()
        plat3.wait_tick()


def test_reset_run_forgets_the_previous_trials_link_state():
    plat, cam, belt, clk = _plat(healthy=True)
    cam.frames = 1
    plat.poll_frame()
    plat.wait_tick()
    clk.t += 120.0                                             # người thử đặt vật mất 2 phút giữa hai lượt
    plat.reset_run()
    cam.frames = 10 ** 6
    plat.poll_frame()
    plat.wait_tick()                                           # không được báo lỗi camera vì khoảng nghỉ giữa lượt
    assert plat.n_ticks == 1 and plat._belt_v == 0.0
