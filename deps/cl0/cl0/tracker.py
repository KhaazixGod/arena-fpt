"""Theo dõi trong hệ băng (bước 5 của §3.3 CL-0): vị trí vật trong hệ băng p_b = p_w - s·u_hat là HẰNG SỐ khi vật không trượt,
nên chỉ cần gộp nhiều quan sát (trung vị) thay vì lọc động học. Liên kết giữa các khung bằng khoảng cách trong hệ băng."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .config import TrackCfg
from .perception import Detection


def circ_mean_axis_deg(thetas_deg: Sequence[float]) -> float:
    """Trung bình vòng của các góc *trục* (mod 180)."""
    t = np.radians(np.asarray(thetas_deg, float) * 2.0)
    return float((math.degrees(math.atan2(np.sin(t).mean(), np.cos(t).mean())) / 2.0) % 180.0)


@dataclass
class Track:
    tid: int
    obs: List[Tuple[float, float, float, float, float]] = field(default_factory=list)  # (t_img, a_b, b, theta, width)
    first_t: float = 0.0
    last_t: float = 0.0
    n_total: int = 0

    def add(self, t, a_b, b, th, w, window):
        self.obs.append((t, a_b, b, th, w))
        self.obs = self.obs[-window:]
        self.last_t = t
        self.n_total += 1

    def estimate(self):
        o = np.asarray(self.obs, float)
        a, b = float(np.median(o[:, 1])), float(np.median(o[:, 2]))
        th = circ_mean_axis_deg(o[:, 3])
        w = float(np.median(o[:, 4]))
        std = float(np.hypot(o[:, 1].std(), o[:, 2].std())) if len(o) > 1 else 0.0
        return a, b, th, w, std


class Tracker:
    def __init__(self, cfg: TrackCfg):
        self.cfg = cfg
        self.tracks: List[Track] = []
        self._next = 1

    def update(self, dets: Sequence[Detection], s_img: float, t_img: float) -> None:
        """Chỉ nhận phát hiện hợp lệ (reject == '')."""
        used = set()
        for d in dets:
            if not d.ok:
                continue
            a_b, b = d.a_mm - s_img, d.b_mm
            best, bd = None, self.cfg.gate_mm
            for tr in self.tracks:
                if tr.tid in used:
                    continue
                ea, eb, _, _, _ = tr.estimate()
                dist = math.hypot(ea - a_b, eb - b)
                if dist < bd:
                    best, bd = tr, dist
            if best is None:
                best = Track(self._next, first_t=t_img)
                self._next += 1
                self.tracks.append(best)
            used.add(best.tid)
            best.add(t_img, a_b, b, d.theta_deg, d.width_mm, self.cfg.window)

    def confirmed(self) -> List[Track]:
        out = []
        for tr in self.tracks:
            if tr.n_total >= self.cfg.n_confirm and len(tr.obs) >= self.cfg.n_confirm:
                if tr.estimate()[4] <= self.cfg.max_std_mm:
                    out.append(tr)
        return out

    def prune(self, t_now: float, keep: Optional[int] = None) -> None:
        self.tracks = [tr for tr in self.tracks if (t_now - tr.last_t) <= self.cfg.lost_s or tr.tid == keep]

    def get(self, tid: int) -> Optional[Track]:
        for tr in self.tracks:
            if tr.tid == tid:
                return tr
        return None

    def match(self, a_b: float, b: float) -> Optional[Track]:
        best, bd = None, self.cfg.gate_mm
        for tr in self.tracks:
            ea, eb, _, _, _ = tr.estimate()
            d = math.hypot(ea - a_b, eb - b)
            if d < bd:
                best, bd = tr, d
        return best
