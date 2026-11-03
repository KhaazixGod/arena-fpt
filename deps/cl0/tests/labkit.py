"""Tiện ích cho test 'phòng thí nghiệm ảo': chạy CHÍNH các lệnh `cl0.calibrate` (board → belt → background → lag) với một
người thử ảo trên thế giới mô phỏng theo thời gian ảo, rồi dựng chồng CL-0 TỪ CÁC FILE vừa sinh ra và chạy lượt thử."""
import contextlib
import io
import os
import re
import shutil
from typing import List, Optional, Sequence, Tuple

import numpy as np

from cl0 import calibrate as C
from cl0.config import Config, load_config
from cl0.geometry import PlaneCalib
from cl0.runner import run_controller
from cl0.sim.harness import SimSetup, arrangement_to_placed, build_system
from cl0.sim.lab import LabSession, Operator, SimLab
from cl0.sim.platform import SimPlatform
from cl0.system import build_stack


def write_cfg(D: str, mm_per_step: float = 0.0, latency: float = 0.0, lead: float = 0.0, speed: float = 50.0, extra: str = "") -> str:
    p = os.path.join(D, "cfg.toml")
    with open(p, "w", encoding="utf-8") as f:
        f.write(f'''calib_path = "{D}/calib.json"
background_path = "{D}/background.npz"
[camera]
width = 640
height = 480
fps = 15
latency_s = {latency}
[belt]
kind = "counter"
mm_per_step = {mm_per_step}
speed_mm_s = {speed}
width_mm = 120.0
[executor]
lead_s = {lead}
{extra}
''')
    return p


class Pipeline:
    def __init__(self, D, setup, sim, lab, cfg_path, calib, lead, log):
        self.D, self.setup, self.sys, self.lab, self.cfg_path, self.calib, self.lead, self.log = D, setup, sim, lab, cfg_path, calib, lead, log


def run_pipeline(D: str, setup: SimSetup, op_kw: Optional[dict] = None, verbose: bool = False, board=("7", "4", "15"),
                 b_range: Optional[str] = None, a_range: Optional[str] = None) -> Pipeline:
    shutil.rmtree(D, ignore_errors=True)
    os.makedirs(D)
    cfgp = write_cfg(D)
    sim = build_system(setup, Config())
    lab = SimLab(sim)
    op = Operator(lab, **(op_kw or {}))
    out = io.StringIO()
    ctx = contextlib.nullcontext() if verbose else contextlib.redirect_stdout(out)
    with LabSession(lab, op), ctx:
        assert C.main(["board", "--config", cfgp, "--cols", board[0], "--rows", board[1], "--square-mm", board[2], "--frames", "10"]) == 0
        assert C.main(["belt", "--config", cfgp, "--speed", str(1.0 / setup.mm_per_step * 60), "--runs", "3"]) == 0
        cal = PlaneCalib.load(f"{D}/calib.json")
        write_cfg(D, cal.mm_per_step, cal.latency_s)
        args = ["background", "--config", cfgp, "--frames", "30"]
        if b_range:
            args += ["--b-range", b_range]
        if a_range:
            args += ["--a-range", a_range]
        assert C.main(args) == 0
        assert C.main(["lag", "--config", cfgp, "--speed", "40", "--duration", "3"]) == 0
    log = out.getvalue()
    m = re.search(r"lead_s = ([0-9.]+)", log)
    lead = float(m.group(1)) if m else 0.0
    cfgp = write_cfg(D, cal.mm_per_step, cal.latency_s, lead=lead)
    return Pipeline(D, setup, sim, lab, cfgp, cal, lead, log)


def trials(pl: Pipeline, items_list: Sequence[Sequence[Tuple[str, float, float, float]]], v: float = 50.0, cache_dir: Optional[str] = None
           ) -> List[Tuple[bool, str, str, float]]:
    """Chạy từng danh sách vật bằng chồng dựng TỪ FILE (calib.json, background.npz, cfg.toml). Trả [(thành công, outcome, lý do, lệch tâm)]."""
    cfg = load_config(pl.cfg_path)
    cfg.belt.speed_mm_s = v
    out = []
    for items in items_list:
        stack = build_stack(cfg, cache_dir=cache_dir)
        objs = arrangement_to_placed(pl.sys, items, a_start=-420.0)
        world = pl.sys.make_world(objs)
        world.p.belt_scale_error = pl.calib.mm_per_step / pl.setup.mm_per_step      # băng thật chạy theo mm/xung thật; phần mềm dùng giá trị đo
        plat = SimPlatform(world, cfg.executor.control_hz, pl.setup.cam.fps, pl.lab.lat, cfg.camera.latency_s)
        plat.start_belt(v)
        rr = run_controller(stack.ctrl, plat, t_limit_s=cfg.executor.hard_timeout_s + 10.0)
        last = world.grasp_log[-1][1] if world.grasp_log else None
        out.append((bool(world.success), rr.outcome, last.reason if last else "", last.off_mm if last else float("nan")))
    return out
