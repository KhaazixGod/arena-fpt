"""Camera USB (OpenCV) chạy ở luồng riêng, gắn dấu thời gian lúc NHẬN khung rồi trừ độ trễ camera đã đo.

``Frame.t_capture = t_nhận − camera.latency_s``. Độ trễ đúng là lượng căn thời gian giữa ảnh và s(t) của băng; đo bằng
``python -m cl0.calibrate belt`` (cách chính xác nhất vì nó đo thẳng độ lệch ảnh↔băng) hoặc bằng bài thử chớp LED (§3.1 dòng 2).
Không kiểm thử trên camera thật trong môi trường dựng mã này: [chưa kiểm trên phần cứng].
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import numpy as np

from ..config import CameraCfg
from ..types import Frame


class Undistorter:
    """Gỡ méo ống kính từ file npz (K, dist) do ``calibrate intrinsics`` sinh ra. Không bắt buộc."""

    def __init__(self, path: str, size):
        import cv2
        d = np.load(path)
        K, dist = d["K"], d["dist"]
        w, h = size
        newK, _ = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 0)
        self.m1, self.m2 = cv2.initUndistortRectifyMap(K, dist, None, newK, (w, h), cv2.CV_16SC2)
        self.newK = newK
        self._cv2 = cv2

    def __call__(self, img: np.ndarray) -> np.ndarray:
        return self._cv2.remap(img, self.m1, self.m2, self._cv2.INTER_LINEAR)


class CameraThread:
    def __init__(self, cfg: CameraCfg, clock: Callable[[], float] = time.monotonic, undistort: Optional[Undistorter] = None):
        self.cfg, self.clock, self.undistort = cfg, clock, undistort
        self._cap = None
        self._th: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._frame: Optional[Frame] = None
        self._seq = 0
        self._seen = 0
        self._t_recv: list = []
        self.error: Optional[str] = None

    # ----------------------------------------------------------------------------------------------- vòng đời
    def start(self) -> None:
        import cv2
        dev = self.cfg.device
        cap = cv2.VideoCapture(dev, cv2.CAP_V4L2) if isinstance(dev, int) or str(dev).startswith("/dev/") else cv2.VideoCapture(dev)
        if not cap.isOpened():
            raise RuntimeError(f"không mở được camera {dev!r}; kiểm tra chỉ số /dev/video* và quyền (nhóm video)")
        if self.cfg.fourcc:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.cfg.fourcc))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.height)
        cap.set(cv2.CAP_PROP_FPS, self.cfg.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap = cap
        ok, img = cap.read()
        if not ok:
            raise RuntimeError("camera mở được nhưng không đọc được khung")
        h, w = img.shape[:2]
        if (w, h) != (self.cfg.width, self.cfg.height):
            print(f"[camera] CẢNH BÁO: yêu cầu {self.cfg.width}x{self.cfg.height} nhưng camera trả {w}x{h}; "
                  "hiệu chuẩn phải làm đúng ở độ phân giải này")
        self._stop.clear()
        self._th = threading.Thread(target=self._run, name="cl0-camera", daemon=True)
        self._th.start()

    def stop(self) -> None:
        self._stop.set()
        if self._th is not None:
            self._th.join(timeout=2.0)
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _run(self) -> None:
        while not self._stop.is_set():
            ok, img = self._cap.read()
            t = self.clock()
            if not ok:
                self.error = "đọc khung thất bại"
                time.sleep(0.01)
                continue
            if self.undistort is not None:
                img = self.undistort(img)
            with self._lock:
                self._seq += 1
                self._frame = Frame(img, t - self.cfg.latency_s)
                self._t_recv.append(t)
                if len(self._t_recv) > 120:
                    self._t_recv = self._t_recv[-120:]

    # ----------------------------------------------------------------------------------------------- truy cập
    def poll(self) -> Optional[Frame]:
        """Khung MỚI kể từ lần gọi trước (hoặc None)."""
        with self._lock:
            if self._seq == self._seen:
                return None
            self._seen = self._seq
            return self._frame

    def latest(self) -> Optional[Frame]:
        with self._lock:
            return self._frame

    def fps_measured(self) -> float:
        with self._lock:
            ts = list(self._t_recv)
        if len(ts) < 3:
            return 0.0
        return (len(ts) - 1) / (ts[-1] - ts[0])

    def jitter_ms(self) -> float:
        """Độ lệch chuẩn của khoảng cách giữa các khung (ms): lớn bất thường => camera/USB có vấn đề."""
        with self._lock:
            ts = np.asarray(self._t_recv, float)
        if len(ts) < 5:
            return 0.0
        return float(np.std(np.diff(ts)) * 1e3)


class ReplayCamera:
    """Phát lại danh sách (ảnh, t_capture) — để thử bộ nhận thức/offline hoặc test."""

    def __init__(self, frames):
        self._frames = list(frames)
        self._i = 0

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def poll(self) -> Optional[Frame]:
        if self._i >= len(self._frames):
            return None
        img, t = self._frames[self._i]
        self._i += 1
        return Frame(img, t)

    def latest(self) -> Optional[Frame]:
        if not self._frames:
            return None
        img, t = self._frames[min(self._i, len(self._frames) - 1)]
        return Frame(img, t)
