"""One trial on the Isaac platform for ANY method (arena/methods): reset, run the method in lockstep, record ground truth and (optionally) videos.

Ground truth per control tick (GTRecorder): virtual time, true belt travel, the grasp centre (gripper_frame_link + R @ tcp_offset, i.e. the point CL-0 steers),
the closing-axis azimuth, gripper position, and every placed object's (a, b, z, yaw).  The labeler (arena/labeler.py) turns this into success / clean / cause.
The success rule itself lives in the labeler; GTRecorder keeps a running copy only so a trial can report it immediately.
"""
from __future__ import annotations

import os
import time
from typing import List, Optional, Sequence

import cv2
import numpy as np

from cl0.runner import run_controller

from .world import IsaacWorld, SimFault

LIFT_MM, HOLD_S = 25.0, 2.0          # plan §6.1 M1 / KE_HOACH_HUONG_1 §4.3 (same rule as cl0.sim.world)


class GTRecorder:
    """Per-tick ground truth; attach with ``platform.tick_hooks.append(rec)`` (and call ``rec(platform)`` once at t = 0)."""

    def __init__(self, world: IsaacWorld, names: List[str], tcp_offset_mm: Sequence[float] = (0.0, 0.0, 0.0)):
        self.world, self.names = world, names
        self.off = np.asarray(tcp_offset_mm, float)
        self.rows: List[list] = []
        self._run = {n: 0.0 for n in names}
        self.success_t: Optional[float] = None
        self.success_obj: Optional[str] = None
        self._last_t: Optional[float] = None

    def __call__(self, plat) -> None:
        w = self.world
        t = plat.now()
        gt = w.gt_objects()
        dt = 0.0 if self._last_t is None else t - self._last_t
        self._last_t = t
        p, R = w.gt_tcp_pose()
        tcp = p + R @ self.off
        c = R[:, 0]
        row = [t, plat.belt_s_true(t), *tcp, float(np.degrees(np.arctan2(c[1], c[0]))), w.grip_deg_to_pos(w.joint_deg()[5])]
        for n in self.names:
            o = gt[n]
            lift = o["pos_mm"][2] - w.spec_by_name[n].height_mm / 2.0 - w.belt_top_mm
            if lift >= LIFT_MM:
                self._run[n] += dt
                if self.success_t is None and self._run[n] >= HOLD_S:
                    self.success_t, self.success_obj = t, n
            else:
                self._run[n] = 0.0
            row += [o["a_mm"], o["b_mm"], o["pos_mm"][2], o["yaw_deg"], o.get("tilt_deg", 0.0)]
        self.rows.append(row)

    def columns(self) -> List[str]:
        c = ["t", "belt_s_gt", "tcp_x", "tcp_y", "tcp_z", "jaw_yaw", "grip_pos"]
        for n in self.names:
            c += [f"{n}.a", f"{n}.b", f"{n}.z", f"{n}.yaw", f"{n}.tilt"]          # .tilt added for E18 (11/11); every reader indexes columns by name
        return c

    def array(self) -> np.ndarray:
        return np.asarray(self.rows, float)


class TimedMethod:
    """Wraps a method: measures the WALL time of every ``step`` (metric M6), and turns an exception raised INSIDE the method into that method's
    failure (outcome "method_exception:<type>", the trial ends) instead of crashing the run.  Everything else is delegated."""

    def __init__(self, inner):
        self.inner = inner
        self.step_ms: List[float] = []
        self.exc: Optional[str] = None

    def reset(self, t0, state):
        self.step_ms, self.exc, self.last_cmd = [], None, None
        return self.inner.reset(t0, state)

    def step(self, t, frame, belt, state):
        from cl0.types import Command
        a = time.perf_counter()
        try:
            cmd = self.inner.step(t, frame, belt, state)
        except Exception as e:                      # noqa: BLE001  (third-party methods: their bug is their failure)
            import traceback
            self.exc = f"method_exception:{type(e).__name__}"
            self.exc_trace = traceback.format_exc()
            cmd = Command(None, None, "ERROR", str(e)[:200])
        self.step_ms.append((time.perf_counter() - a) * 1e3)
        self.last_cmd = cmd
        return cmd

    @property
    def finished(self) -> bool:
        return self.exc is not None or bool(self.inner.finished)

    @property
    def outcome(self) -> str:
        return self.exc if self.exc is not None else self.inner.outcome

    def __getattr__(self, name):                 # events, log, diag, phase, close ...
        return getattr(self.inner, name)


class VideoTap:
    """Writes the camera frames of a trial (downscaled) with a t / phase caption."""

    def __init__(self, path: str, method, size=(640, 360), fps: float = 30.0):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
        self.size, self.method, self.path = size, method, path

    def _caption(self, f, t):
        cv2.putText(f, f"t={t:5.2f}s {getattr(self.method, 'phase', '')}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        return f

    def __call__(self, t: float, img: np.ndarray) -> None:
        self.w.write(self._caption(cv2.resize(img, self.size, interpolation=cv2.INTER_AREA), t))

    def close(self) -> None:
        self.w.release()


class DebugVideoTap(VideoTap):
    """Same, from the oblique debug camera (IsaacWorld(debug_cam=True)); one extra render per captured frame."""

    def __init__(self, path: str, method, world, size=(960, 540), fps: float = 30.0):
        super().__init__(path, method, size, fps)
        self.world = world

    def __call__(self, t: float, img: np.ndarray) -> None:
        super().__call__(t, self.world.render_debug_bgr())


def run_trial(plat, method, cfg, placements: List[dict], speed_mm_s: float, video_path: Optional[str] = None,
              debug_video_path: Optional[str] = None, t_limit_s: Optional[float] = None, extra_taps: Sequence = (), hard_reset: bool = False) -> dict:
    """Reset the world, run ``method`` to completion; returns outcome, events, GT, timings.  Raises SimFault on a simulation fault (valid = 0)."""
    names = [p["name"] for p in placements]
    wall0 = time.perf_counter()
    plat.reset_trial(placements, hard=hard_reset)
    rec = GTRecorder(plat.world, names, cfg.robot.tcp_offset_mm)
    rec(plat)
    plat.tick_hooks.append(rec)
    taps = []
    if video_path:
        taps.append(VideoTap(video_path, method))
    if debug_video_path:
        taps.append(DebugVideoTap(debug_video_path, method, plat.world))
    plat.frame_hooks.extend(taps)
    plat.frame_hooks.extend(extra_taps)
    tm = method if isinstance(method, TimedMethod) else TimedMethod(method)
    st0 = dict(plat.stats)
    try:
        if speed_mm_s > 0:
            plat.start_belt(speed_mm_s)
        limit = t_limit_s if t_limit_s is not None else cfg.executor.hard_timeout_s + 10.0
        rr = run_controller(tm, plat, t_limit_s=limit)
        plat.stop_belt()
    finally:
        plat.tick_hooks.remove(rec)
        for tp in taps:
            plat.frame_hooks.remove(tp)
            tp.close()
        for tp in extra_taps:
            plat.frame_hooks.remove(tp)
    ms = np.asarray(tm.step_ms, float)
    return {"outcome": rr.outcome, "finished": rr.finished, "t_end_s": rr.t_end, "phases": [(round(t, 3), n) for t, n in rr.phases],
            "events": [{"t": round(e.t, 3), "name": e.name, "data": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in e.data.items()}}
                       for e in rr.events],
            "diag": {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v)) for k, v in rr.diag.items()},
            "log": rr.log,
            "gt_success": rec.success_t is not None, "gt_success_t": rec.success_t, "gt_success_obj": rec.success_obj,
            "gt_columns": rec.columns(), "gt_array": rec.array(),
            "ms_step_p50": float(np.percentile(ms, 50)) if ms.size else float("nan"), "ms_step_p95": float(np.percentile(ms, 95)) if ms.size else float("nan"),
            "n_steps": int(ms.size), "wall_s": round(time.perf_counter() - wall0, 2),
            "method_exception": getattr(tm, "exc_trace", None) if tm.exc else None,
            "renders": plat.stats["renders"] - st0["renders"], "render_wall_s": round(plat.stats["render_wall_s"] - st0["render_wall_s"], 2)}


def run_cl0_trial(plat, ctrl, cfg, placements, speed_mm_s, video_path=None, debug_video_path=None) -> dict:
    """E2 compatibility (scripts/e2_run_cl0.py): the old result layout."""
    r = run_trial(plat, ctrl, cfg, placements, speed_mm_s, video_path, debug_video_path)
    r["gt"] = {"success": r["gt_success"], "success_t": r["gt_success_t"], "success_obj": r["gt_success_obj"], "max_lift_mm": {}}
    r.pop("log", None)
    return r
