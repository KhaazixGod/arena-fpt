"""IsaacPlatform: the ``cl0.runner.Platform`` implemented on the Isaac world, in LOCKSTEP (virtual time = physics steps; no wall clock anywhere).

* ``wait_tick`` advances a whole number of physics steps (hz / control_hz); the camera captures every hz / fps steps and delivers ``latency_true_s`` later;
  ``Frame.t_capture`` = delivery time - ``cfg.camera.latency_s`` (what CL-0 believes), exactly like ``CameraThread``.
* The belt is the REAL ``cl0.hw.belt.Belt`` in ``kind = "counter"`` with its serial port replaced by this class: the physical belt profile is that class's own model
  (command delay ``cmd_delay_s``, ramp ``accel_mm_s2``), the PhysX surface velocity follows it, and a virtual microcontroller reports an integer pulse count
  (``counter_mm_per_step_true``, ``counter_rate_hz``, ``serial_latency_s``).  CL-0 reads ``s_at / speed_at`` from the pulses with its own estimate of mm/step.
* Nothing here exposes ground truth to CL-0; GT is read from ``platform.world.gt_*`` by the runner.
"""
from __future__ import annotations

import math
import time
from collections import deque
from typing import Callable, Deque, List, Optional, Tuple

import numpy as np

from cl0.config import Config
from cl0.hw.belt import Belt
from cl0.types import Command, Frame, RobotState

from .world import IsaacWorld, SimFault


class _StepClock:
    """Virtual time for the belt model.  Holds integers only: the objects CL-0 (or any method) receives must not lead back to the world (GT leak test)."""
    __slots__ = ("k", "k0", "hz")

    def __init__(self, hz: float):
        self.k, self.k0, self.hz = 0, 0, hz

    def now(self) -> float:
        return (self.k - self.k0) / self.hz


def _whole(x: float, what: str) -> int:
    n = int(round(x))
    if abs(x - n) > 1e-6 or n < 1:
        raise ValueError(f"{what} = {x} is not a whole number of physics steps; choose scene [physics] hz as a multiple of control_hz, camera fps and counter_rate_hz")
    return n


class IsaacPlatform:
    def __init__(self, world: IsaacWorld, cfg: Config):
        self.world, self.cfg = world, cfg
        sc = world.cfg
        hz = world.hz
        self.steps_per_tick = _whole(hz / cfg.executor.control_hz, "hz/control_hz")
        self.cam_every = _whole(hz / cfg.camera.fps, "hz/camera.fps")
        self.cnt_every = _whole(hz / sc["belt"]["counter_rate_hz"], "hz/counter_rate_hz")
        self.lat_steps = int(round(sc["camera"]["latency_true_s"] * hz))
        self.cmd_delay_steps = int(round(sc["robot"].get("cmd_delay_s", 0.0) * hz))
        self.mm_per_step_true = float(sc["belt"]["counter_mm_per_step_true"])
        self._clock = _StepClock(hz)
        self._clock.k = self._clock.k0 = world.k
        self._tick = 0
        self._cmd_q: Deque[Tuple[int, Optional[np.ndarray], Optional[float]]] = deque()
        self._frames: Deque[Tuple[int, np.ndarray]] = deque()
        self._pending_counts: Deque[Tuple[float, int]] = deque()
        self.belt = Belt(cfg.belt, clock=self._clock.now)
        self.depth = bool(getattr(world, "depth_enabled", False))
        self.render_enabled = True             # False for methods that never look at pixels (NOOP, ORACLE): physics and timing are unchanged
        self.warm_renders = int(sc["camera"].get("warm_renders", 8))
        self.frame_hooks: List[Callable[[float, np.ndarray], None]] = []
        self.tick_hooks: List[Callable[["IsaacPlatform"], None]] = []
        self.stats = {"renders": 0, "render_wall_s": 0.0, "steps": 0, "step_wall_s": 0.0}
        self.home_q = np.asarray(cfg.robot.home_q_deg, float)

    # ------------------------------------------------------------------ trial reset (not part of the Platform protocol; called by the runner)
    def reset_trial(self, placements: List[dict], hard: bool = False) -> None:
        w, sc = self.world, self.world.cfg
        if hard:
            w.hard_reset()
        w.set_belt_speed(0.0)
        w.park_all()
        w.teleport_arm(self.home_q, self.cfg.robot.gripper_open)
        w.step_seconds(0.3)                                   # one step also makes the renderer/Fabric follow the teleport; 0.3 s lets contacts relax
        w.place(placements)
        w.step_seconds(sc["reset"]["settle_s"])
        if not w.finite():
            raise SimFault("non-finite state during reset")
        err = float(np.max(np.abs(w.joint_deg()[:5] - self.home_q)))
        if err > sc["reset"]["home_tol_deg"]:
            raise SimFault(f"arm not at home after reset (max joint error {err:.2f} deg)")
        gt = w.gt_objects()
        for p in placements:                                   # nothing was flung or sank while settling
            o = gt[p["name"]]
            top = w.belt_top_mm + w.spec_by_name[p["name"]].height_mm / 2.0
            if abs(o["a_mm"] - p["a_mm"]) > 3.0 or abs(o["b_mm"] - p["b_mm"]) > 3.0 or abs(o["pos_mm"][2] - top) > 4.0:
                raise SimFault(f"object {p['name']} moved while settling: a {o['a_mm']:.1f}/{p['a_mm']:.1f} b {o['b_mm']:.1f}/{p['b_mm']:.1f} z {o['pos_mm'][2]:.1f}/{top:.1f}")
        self._clock.k = self._clock.k0 = w.k
        self._tick = 0
        self._cmd_q.clear(); self._frames.clear(); self._pending_counts.clear()
        self.belt = Belt(self.cfg.belt, clock=self._clock.now)
        self.belt._add_count(0, 0.0)
        if self.render_enabled:            # flush the renderer's TEMPORAL history (AA / denoiser blend past frames): otherwise the first frames of a trial carry a
            for _ in range(self.warm_renders):   # trace of the PREVIOUS trial and pixel-based methods are not repeatable (E7 remote check, 30/10)
                self.world.render_bgr()
        self._capture()

    # ------------------------------------------------------------------ Platform protocol
    @property
    def k0(self) -> int:
        return self._clock.k0

    def now(self) -> float:
        return self._clock.now()

    def poll_frame(self) -> Optional[Frame]:
        k, fr = self.world.k, None
        while self._frames and self._frames[0][0] <= k:
            kd, img, depth = self._frames.popleft()
            fr = Frame(img, (kd - self.k0) / self.world.hz - self.cfg.camera.latency_s)
            if depth is not None:
                fr.depth_mm = depth                   # optional extra observation (ideal depth, mm, same pixels as img); CL-0 ignores it
        return fr

    def robot_state(self) -> RobotState:
        d = self.world.joint_deg()
        return RobotState(d[:5].copy(), self.world.grip_deg_to_pos(d[5]), self.now())

    def send(self, cmd: Command) -> None:
        if cmd.q_deg is None and cmd.gripper is None:
            return
        q = None if cmd.q_deg is None else np.asarray(cmd.q_deg, float).copy()
        if self.cmd_delay_steps <= 0:
            self.world.set_targets(q, cmd.gripper)
        else:
            self._cmd_q.append((self.world.k + self.cmd_delay_steps, q, cmd.gripper))

    def start_belt(self, v_mm_s: float) -> None:
        self.belt.start(float(v_mm_s))

    def stop_belt(self) -> None:
        self.belt.stop()

    def wait_tick(self) -> float:
        self._tick += 1
        target = self.k0 + self._tick * self.steps_per_tick
        while self.world.k < target:
            self._advance_one()
        if not self.world.finite():
            raise SimFault("non-finite physics state")
        for h in self.tick_hooks:
            h(self)
        return self.now()

    # ------------------------------------------------------------------ internals
    def belt_s_true(self, t: Optional[float] = None) -> float:
        """GROUND-TRUTH belt travel (mm) from the physical belt profile; for the runner/labeler, never given to CL-0."""
        return self.belt._model_state(self.now() if t is None else t)[0]

    def _advance_one(self) -> None:
        w = self.world
        t0 = self.now()
        w.set_belt_speed(self.belt._model_state(t0 + 0.5 * w.dt)[1])          # velocity at mid-step: the belt really ramps with accel_mm_s2 after the command delay
        a = time.perf_counter()
        w.step()
        self._clock.k = w.k
        self.stats["steps"] += 1; self.stats["step_wall_s"] += time.perf_counter() - a
        k, t = w.k, self.now()
        while self._cmd_q and self._cmd_q[0][0] <= k:
            _, q, g = self._cmd_q.popleft()
            w.set_targets(q, g)
        n = k - self.k0
        if n % self.cnt_every == 0:                                               # the virtual microcontroller prints "S <count>"; PC receives it serial_latency_s later
            count = int(math.floor(self.belt._model_state(t)[0] / self.mm_per_step_true + 1e-9))
            self._pending_counts.append((t + self.cfg.belt.serial_latency_s, count))
        while self._pending_counts and self._pending_counts[0][0] <= t + 1e-12:
            ts, cnt = self._pending_counts.popleft()
            self.belt._add_count(cnt, ts)
        if n % self.cam_every == 0:
            self._capture()

    def _capture(self) -> None:
        if self.render_enabled:
            a = time.perf_counter()
            img = self.world.render_bgr()
            depth = self.world.last_depth_mm() if self.depth else None
            self.stats["renders"] += 1; self.stats["render_wall_s"] += time.perf_counter() - a
        else:
            img, depth = np.zeros((1, 1, 3), np.uint8), None       # a NEW object per frame: the GT tap keys capture-time snapshots by id(img)
        self._frames.append((self.world.k + self.lat_steps, img, depth))
        for h in self.frame_hooks:
            h(self.now(), img)
