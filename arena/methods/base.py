"""Method contract of the arena (KE_HOACH_DAU_TRUONG.md §2) and the registry.

A METHOD is anything with the interface ``cl0.runner.run_controller`` drives (the same one CL-0 has):

    reset(t0: float, state: RobotState) -> None
    step(t: float, frame: Optional[Frame], belt: BeltLike, state: RobotState) -> Command      # called at control_hz (50 Hz), virtual time
    finished: bool        outcome: str        events: list[TrialEvent]        log: list[dict]        diag: dict
    close() -> None       (optional)          phase: str (optional, shown in videos)

Observations (all a real robot would have, nothing else):
  * ``frame``: the newest camera image since the previous step or None.  ``frame.img`` BGR uint8 (1280x720 here), ``frame.t_capture`` (virtual s, already
    corrected by the believed camera latency).  With ``--depth``: ``frame.depth_mm`` float32 HxW, ideal depth along the optical axis (no sensor noise).
  * ``belt.s_at(t)``, ``belt.speed_at(t)``: belt travel (mm) / speed from the pulse counter.
  * ``state.q_deg`` (5 arm joints, deg, LeRobot order), ``state.gripper`` (0-100), ``state.t``.
Action: ``Command(q_deg=5 joint targets in deg or None, gripper=0-100 or None, phase=str)``.  The platform applies it as servo targets.
Shared, calibrated knowledge every method may use (MethodContext): CL-0 config, kinematics (FK/IK with the tcp offset), calib.json (pixel -> belt plane,
belt direction), background.npz.  A method must not touch the Isaac world; only PRIVILEGED methods (ORACLE) get ``ctx.gt``.

Plug-in of your own code (no edit of the arena needed):  ``--methods mypkg.mymodule:make_method`` where ``make_method(ctx) -> method``.
"""
from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from cl0.config import Config
from cl0.geometry import PlaneCalib
from cl0.kinematics import SO101Kinematics


@dataclass
class MethodContext:
    cfg: Config                          # arena.toml as loaded (each method gets its own copy)
    kin: SO101Kinematics                 # official SO-101 chain + cfg.robot.tcp_offset_mm
    calib: PlaneCalib                    # calib.json: H (pixel -> W on the belt plane), z_plane_mm, belt_dir_deg, mm_per_step, latency_s
    calib_path: str
    background_path: str
    image_size: Tuple[int, int]
    control_hz: float
    cache_dir: str = os.path.expanduser("~/.cache/cl0")
    gt: Optional[object] = None          # ground-truth tap: ONLY for privileged methods (ORACLE); None for every other method
    extra: Dict[str, str] = field(default_factory=dict)     # --method-arg key=value pairs


@dataclass
class MethodSpec:
    name: str
    factory: Callable[[MethodContext], object]
    privileged: bool = False
    doc: str = ""
    uses_pixels: bool = True             # False: the platform skips the RTX render for this method (frames still arrive, with a 1x1 placeholder image)


REGISTRY: Dict[str, MethodSpec] = {}


def register(name: str, privileged: bool = False, doc: str = "", uses_pixels: bool = True):
    def deco(fn):
        REGISTRY[name] = MethodSpec(name, fn, privileged, doc or (fn.__doc__ or "").strip().splitlines()[0] if (doc or fn.__doc__) else "", uses_pixels)
        return fn
    return deco


def resolve(spec: str) -> MethodSpec:
    """'CL0' (registered) or 'package.module:factory' (your own code, privileged = False)."""
    if spec in REGISTRY:
        return REGISTRY[spec]
    if ":" in spec:
        mod, fn = spec.split(":", 1)
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        f = getattr(importlib.import_module(mod), fn)
        return MethodSpec(spec, f, False, (f.__doc__ or "").strip().splitlines()[0] if f.__doc__ else "")
    raise KeyError(f"unknown method {spec!r}; registered: {sorted(REGISTRY)}; or give module.path:factory")


def check_contract(m) -> list:
    """Names of missing parts of the method contract (empty list = OK)."""
    miss = [n for n in ("reset", "step") if not callable(getattr(m, n, None))]
    miss += [n for n in ("finished", "outcome", "events", "log", "diag") if not hasattr(m, n)]
    return miss
