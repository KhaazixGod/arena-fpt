"""Dựng toàn bộ chồng CL-0 từ cấu hình + các file hiệu chuẩn (dùng cho run_g0, calibrate, test)."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Optional

from .config import Config
from .controller import CL0Controller
from .geometry import PlaneCalib, Rectifier, Window, auto_window
from .kinematics import SO101Kinematics
from .perception import BackgroundModel, Detector, window_of
from .reach import TopDownReach


@dataclass
class Stack:
    cfg: Config
    kin: SO101Kinematics
    calib: PlaneCalib
    rect: Rectifier
    bg: BackgroundModel
    det: Detector
    reach: TopDownReach
    ctrl: CL0Controller


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def code_sha256() -> str:
    """Băm toàn bộ mã *.py của gói cl0 (trừ sim/ và tests) — để chứng minh mã không đổi sau khi đóng băng."""
    root = os.path.dirname(os.path.abspath(__file__))
    h = hashlib.sha256()
    for dp, dn, fn in sorted(os.walk(root)):
        dn[:] = sorted(d for d in dn if d not in ("__pycache__", "sim", "tests"))
        for f in sorted(fn):
            if f.endswith(".py"):
                with open(os.path.join(dp, f), "rb") as fh:
                    h.update(os.path.relpath(os.path.join(dp, f), root).encode() + b"\0" + fh.read() + b"\0")
    return h.hexdigest()


def get_reach(kin: SO101Kinematics, cfg: Config, cache_dir: Optional[str] = None, step_mm: float = 5.0) -> TopDownReach:
    key = json.dumps([cfg.robot.tilt_deg, cfg.robot.joint_margin_deg, step_mm, list(kin.tcp_offset_mm), cfg.robot.urdf], sort_keys=True)
    tag = hashlib.sha256(key.encode()).hexdigest()[:12]
    reach = TopDownReach(kin, tilt_deg=cfg.robot.tilt_deg, step_mm=step_mm, margin_deg=cfg.robot.joint_margin_deg)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, f"reach_{tag}.npz")
        if os.path.exists(path):
            return reach.load_into(path)
        reach.build()
        reach.save(path)
        return reach
    return reach.build()


def build_stack(cfg: Config, calib_path: Optional[str] = None, bg_path: Optional[str] = None, async_perception: bool = False,
                cache_dir: Optional[str] = None) -> Stack:
    calib_path = calib_path or cfg.calib_path
    bg_path = bg_path or cfg.background_path
    calib = PlaneCalib.load(calib_path)
    if cfg.belt.mm_per_step <= 0 and calib.mm_per_step > 0:
        cfg.belt.mm_per_step = calib.mm_per_step
    kin = SO101Kinematics(urdf=cfg.robot.urdf or None, tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
    bg = BackgroundModel.load(bg_path)
    want = bg.meta.get("calib_sha")
    if want and want != file_sha256(calib_path):
        raise RuntimeError(f"{bg_path} được dựng với một calib.json khác; hiệu chuẩn đã đổi => dựng lại nền (cl0.calibrate background)")
    if bg.textured != cfg.belt.textured:
        raise RuntimeError(f"nền textured={bg.textured} nhưng cấu hình belt.textured={cfg.belt.textured}")
    win = window_of(bg)
    rect = Rectifier(calib, win)
    det = Detector(rect, bg, cfg.perception)
    reach = get_reach(kin, cfg, cache_dir)
    ctrl = CL0Controller(cfg, kin, det, reach, calib.belt_dir_deg, calib.z_plane_mm, async_perception=async_perception)
    return Stack(cfg, kin, calib, rect, bg, det, reach, ctrl)
