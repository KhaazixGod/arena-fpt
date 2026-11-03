"""Băng chuyền: s(t) (mm) và tốc độ, cùng lệnh chạy/dừng.

Hai cách biết s(t) (``belt.kind``):
  * ``model``   : không có phản hồi. s(t) = tích phân vận tốc theo lệnh với dốc gia tốc ``accel_mm_s2`` và trễ ``cmd_delay_s``.
                  Với băng trơn chạy ổn định chỉ cần HIỆU s(t_now) − s(t_img) = v·Δt nên mô hình này đủ (mốc tuyệt đối triệt tiêu);
                  với băng có texture cần bộ đếm (vì nền phụ thuộc s tuyệt đối).
  * ``counter`` : vi điều khiển gửi số xung tích luỹ qua serial; s = (xung − xung gốc)·mm_per_step.
Lệnh tốc độ gửi qua cùng cổng serial (``serial_port``) theo mẫu ``cmd_speed``; nếu firmware của bạn khác, sửa 3 chuỗi
``cmd_speed``, ``cmd_stop``, ``line_regex`` trong cấu hình (không cần sửa mã).
Không thử trên băng thật trong môi trường dựng mã này: [chưa kiểm trên phần cứng]; có test với serial giả.
"""
from __future__ import annotations

import bisect
import re
import threading
import time
from typing import Callable, List, Optional, Tuple

import numpy as np

from ..config import BeltCfg


class _History:
    def __init__(self, maxlen: int = 40000):
        self.t: List[float] = []
        self.s: List[float] = []
        self.maxlen = maxlen
        self._lock = threading.Lock()

    def add(self, t: float, s: float) -> None:
        with self._lock:
            if self.t and t <= self.t[-1]:
                return
            self.t.append(t)
            self.s.append(s)
            if len(self.t) > self.maxlen:
                del self.t[: len(self.t) // 4]
                del self.s[: len(self.s) // 4]

    def s_at(self, t: float, tail_s: float = 0.3) -> float:
        with self._lock:
            ts, ss = self.t, self.s
            if not ts:
                return 0.0
            if len(ts) == 1:
                return ss[0]
            if t >= ts[-1]:                                   # ngoại suy theo độ dốc của đoạn cuối
                j = bisect.bisect_left(ts, ts[-1] - tail_s)
                j = min(j, len(ts) - 2)
                v = (ss[-1] - ss[j]) / max(ts[-1] - ts[j], 1e-6)
                return ss[-1] + v * (t - ts[-1])
            if t <= ts[0]:
                return ss[0]
            return float(np.interp(t, ts, ss))

    def speed_at(self, t: float, win_s: float = 0.25) -> float:
        with self._lock:
            ts, ss = self.t, self.s
            if len(ts) < 2:
                return 0.0
            t_hi = min(t, ts[-1])
            j1 = bisect.bisect_right(ts, t_hi) - 1
            j0 = bisect.bisect_left(ts, t_hi - win_s)
            j0 = min(j0, max(j1 - 1, 0))
            j1 = max(j1, j0 + 1) if j0 + 1 < len(ts) else j1
            if j1 <= j0:
                return 0.0
            return (ss[j1] - ss[j0]) / max(ts[j1] - ts[j0], 1e-6)


class Belt:
    """Cài ``BeltLike`` (s_at, speed_at) + start/stop. ``serial`` có thể là đối tượng giống pyserial.Serial (để test)."""

    def __init__(self, cfg: BeltCfg, clock: Callable[[], float] = time.monotonic, serial=None):
        self.cfg, self.clock = cfg, clock
        self._ser = serial
        self._segs: List[Tuple[float, float, float, float]] = [(-1e18, 0.0, 0.0, 0.0)]   # (t0, s0, v0, v_target)
        self._seg_t: List[float] = [-1e18]
        self._hist = _History()
        self._count0: Optional[int] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._rx = re.compile(cfg.line_regex) if cfg.line_regex else None
        self.last_line = ""
        self.n_lines = 0
        self.n_bad_lines = 0

    # ----------------------------------------------------------------------------------------------- vòng đời
    def open(self) -> None:
        c = self.cfg
        if self._ser is None and c.serial_port:
            try:
                import serial  # pyserial
            except ImportError as e:
                raise RuntimeError("thiếu pyserial: pip install pyserial") from e
            self._ser = serial.Serial(c.serial_port, c.serial_baud, timeout=0.05)
            if c.serial_open_delay_s > 0:
                time.sleep(c.serial_open_delay_s)             # bo mạch Arduino/ESP reset khi mở cổng; chưa sẵn sàng ngay
            if hasattr(self._ser, "reset_input_buffer"):
                self._ser.reset_input_buffer()               # bỏ dòng khởi động / rác tích từ trước
        if c.kind == "counter":
            if self._ser is None:
                raise RuntimeError("belt.kind = counter cần belt.serial_port")
            if c.mm_per_step <= 0:
                raise RuntimeError("belt.kind = counter cần belt.mm_per_step > 0 (hiệu chuẩn bằng cl0.calibrate belt)")
            self._stop.clear()
            self._rx_thread = threading.Thread(target=self._rx_loop, name="cl0-belt-rx", daemon=True)
            self._rx_thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._rx_thread is not None:
            self._rx_thread.join(timeout=1.0)
        try:
            if self._ser is not None and hasattr(self._ser, "close"):
                self._ser.close()
        finally:
            self._ser = None

    def _rx_loop(self) -> None:
        buf = b""
        while not self._stop.is_set():
            try:
                chunk = self._ser.read(256) if hasattr(self._ser, "read") else b""
            except Exception:
                time.sleep(0.01)
                continue
            if not chunk:
                continue
            t = self.clock() - self.cfg.serial_latency_s
            buf += chunk
            last = None
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                c = self._parse_line(line.decode("ascii", "ignore").strip())
                if c is not None:
                    last = c
            if last is not None:                              # nhiều dòng trong MỘT lần đọc: không dán nhãn được từng dòng => chỉ giữ số đếm MỚI nhất
                self._add_count(last, t)

    def _parse_line(self, line: str) -> Optional[int]:
        self.last_line = line
        m = self._rx.match(line) if self._rx else None
        if not m:
            self.n_bad_lines += 1
            return None
        self.n_lines += 1
        return int(m.group(1))

    def _add_count(self, cnt: int, t: float) -> None:
        if self._count0 is None:
            self._count0 = cnt
        self._hist.add(t, (cnt - self._count0) * self.cfg.mm_per_step)

    # ----------------------------------------------------------------------------------------------- lệnh
    def _write(self, text: str) -> None:
        if self._ser is not None:
            self._ser.write(text.encode("ascii"))
            if hasattr(self._ser, "flush"):
                self._ser.flush()

    def start(self, v_mm_s: float) -> None:
        c = self.cfg
        now = self.clock()
        steps = v_mm_s / c.mm_per_step if c.mm_per_step > 0 else 0.0
        self._write(c.cmd_speed.format(steps_per_s=steps, v_mm_s=v_mm_s))
        self._model_cmd(now + c.cmd_delay_s, v_mm_s)

    def stop(self) -> None:
        now = self.clock()
        self._write(self.cfg.cmd_stop)
        self._model_cmd(now + self.cfg.cmd_delay_s, 0.0)

    def _model_cmd(self, t_eff: float, v_target: float) -> None:
        s0, v0 = self._model_state(t_eff)
        self._segs.append((t_eff, s0, v0, v_target))
        self._seg_t.append(t_eff)

    def _model_state(self, t: float) -> Tuple[float, float]:
        j = max(bisect.bisect_right(self._seg_t, t) - 1, 0)
        t0, s0, v0, vt = self._segs[j]
        a = max(self.cfg.accel_mm_s2, 1e-6)
        dt = max(t - t0, 0.0)
        dv = vt - v0
        t_ramp = abs(dv) / a
        sgn = 1.0 if dv >= 0 else -1.0
        if dt <= t_ramp:
            return s0 + v0 * dt + 0.5 * sgn * a * dt * dt, v0 + sgn * a * dt
        s_ramp = v0 * t_ramp + 0.5 * sgn * a * t_ramp ** 2
        return s0 + s_ramp + vt * (dt - t_ramp), vt

    # ----------------------------------------------------------------------------------------------- BeltLike
    def s_at(self, t: float) -> float:
        if self.cfg.kind == "counter":
            return self._hist.s_at(t)
        return self._model_state(t)[0]

    def speed_at(self, t: float) -> float:
        if self.cfg.kind == "counter":
            return self._hist.speed_at(t)
        return self._model_state(t)[1]

    def history(self):
        """(t, s) đã nhận từ bộ đếm (bản sao); s tính theo mm_per_step hiện tại."""
        with self._hist._lock:
            return np.asarray(self._hist.t, float), np.asarray(self._hist.s, float)

    def healthy(self, max_age_s: float = 0.5) -> bool:
        """kind = counter: có dòng mới trong ``max_age_s`` giây không."""
        if self.cfg.kind != "counter":
            return True
        with self._hist._lock:
            return bool(self._hist.t) and (self.clock() - self._hist.t[-1]) < max_age_s
