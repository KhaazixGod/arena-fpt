"""P8 (paper-dev): paper front-ends re-implemented in this thesis and plugged into CL-0's tracker / target selection / BeltExecutor.

The benchmark (Benmark_Capstone, arena-fpt 4963d40) ran P05 CNS, P07 ViT-VS and P17 ODIL as "component_only" ports: the paper's perception front-end
gives a grasp in image pixels, CL-0's tracker / selection / executor do the rest (its groups rgb_perception / rgbd_perception, yaw-aware feasibility).
Its adapter code stayed on the benchmark machine, so ports/ re-implements the three front-ends from the papers (ports/README.md); this module is the
arena side, identical for the three:

    # the detector, in its own venv (ports/detector_server.py):
    env -u PYTHONPATH ~/venvs/ports/bin/python ports/detector_server.py --detector p05_cns --refs runs/p8_refs/train_dev --port 6305
    # the arena:
    ~/env_isaac/bin/python -m arena.run_arena --methods P05_CNS_W --method-arg detector=localhost:6305 ...

P05_CNS / P07_VITVS / P17_ODIL: CL-0's YawFeasibleController (as the benchmark's pixel_grasp ports) around the remote detector.
..._W: the same + W1 (arena/wrist_branch.py), the executor fix CL0_W and ORACLE_W have, so the comparison with CL0_W differs only in perception.
The detector gets exactly what a pixel method gets: the camera image and, with run_arena --depth, the ideal depth image.  Never ground truth.

REFCAP (privileged): writes the reference views of ports/ (one object alone on the stopped belt): image, depth and the grasp ORACLE would use (the
object's stored good grasp), in pixels.  Only the reference renderer uses it; the detectors read its files, never the simulator.
"""
from __future__ import annotations

import copy
import json
import math
import os
import time
from multiprocessing.connection import Client
from typing import List

import cv2
import numpy as np

from cl0.types import Command, TrialEvent

from .base import MethodContext, register
from .oracle_w import W1Mixin
from .pixel_grasp import PixelGrasp, PixelGraspDetector
from .yawfeasible import YawFeasibleController, yaw_reach


def _pack(a):
    if a is None:
        return None
    a = np.ascontiguousarray(np.asarray(a))
    return {"data": a.tobytes(), "dtype": str(a.dtype), "shape": list(a.shape)}


class RemoteDetector:
    """detect_fn for PixelGraspDetector: sends the frame (and depth) to ports/detector_server.py, returns its PixelGrasps."""

    def __init__(self, addr: str, expect: str, info: dict, authkey: str = "arena"):
        host, port = addr.rsplit(":", 1)
        self.conn = Client((host, int(port)), authkey=authkey.encode())
        self.conn.send(info)                       # calib + CL-0 window: the detector looks only at the belt, as CL-0 does
        hello = self.conn.recv()
        self.name = hello.get("name", "")
        if not self.name.startswith(expect):
            raise RuntimeError(f"detector server at {addr} is {self.name!r}, this method expects {expect}*")
        self.info = hello
        self.n_calls, self.ms = 0, []

    def __call__(self, img_bgr, depth_mm) -> List[PixelGrasp]:
        t = time.perf_counter()
        self.conn.send({"img": _pack(img_bgr), "depth": _pack(depth_mm)})
        r = self.conn.recv()
        if "error" in r:
            raise RuntimeError(f"detector {self.name}: {r['error']}")
        self.n_calls += 1
        self.ms.append(1000.0 * (time.perf_counter() - t))
        return [PixelGrasp(float(g["u"]), float(g["v"]), float(g["angle_deg"]), float(g["width_mm"]), float(g.get("score", 1.0))) for g in r["grasps"]]


class PortW(W1Mixin, YawFeasibleController):
    def __init__(self, *a, extra=None, **k):
        super().__init__(*a, **k)
        self._w1_init(extra)


def _make_port(ctx: MethodContext, expect: str, w1: bool):
    addr = ctx.extra.get("detector")
    if not addr:
        raise RuntimeError(f"{expect}: give the detector server with --method-arg detector=host:port (ports/detector_server.py)")
    from cl0.perception import BackgroundModel, window_of
    cfg = copy.deepcopy(ctx.cfg)
    w = window_of(BackgroundModel.load(ctx.background_path))
    info = {"calib": json.loads(ctx.calib.to_json()), "window": [w.a_min, w.a_max, w.b_min, w.b_max], "image_size": list(ctx.image_size),
            "gripper_w_mm": float(cfg.perception.grasp.gripper_w_mm)}
    det = PixelGraspDetector(ctx, RemoteDetector(addr, expect, info), float(ctx.extra.get("min_score", 0.0)))
    args = (cfg, ctx.kin, det, yaw_reach(ctx), ctx.calib.belt_dir_deg, ctx.calib.z_plane_mm)
    return PortW(*args, extra=ctx.extra) if w1 else YawFeasibleController(*args)


for _name, _expect, _doc in (("P05_CNS", "P05", "P05 CNS classic front-end (SIFT matches to reference views, re-implemented)"),
                             ("P07_VITVS", "P07", "P07 ViT-VS front-end (DINOv2 ViT-S/14 best-buddy correspondences, re-implemented)"),
                             ("P17_ODIL", "P17", "P17 ODIL stage 1 (FPFH + FGR + ICP registration to reference clouds, needs --depth, re-implemented)")):
    for _w1 in (False, True):
        register(_name + ("_W" if _w1 else ""), doc=_doc + " + CL-0 tracker/executor" + (" + W1" if _w1 else ""))(
            (lambda e, w: (lambda ctx: _make_port(ctx, e, w)))(_expect, _w1))


# ------------------------------------------------------------------ reference views
class RefCapture:
    """Waits until the object has rested a few frames on the stopped belt, then writes <out>/<object>.{png,npy,json} and ends."""
    phase = "REFCAP"

    def __init__(self, ctx: MethodContext, out: str, settle_s: float = 0.5):
        from .oracle import OracleDetector
        self.ctx, self.out, self.settle_s = ctx, out, settle_s
        self.det = OracleDetector(ctx)
        os.makedirs(out, exist_ok=True)
        self.reset(0.0, None)

    def reset(self, t0, state) -> None:
        self.t0, self.finished, self.outcome = t0, False, ""
        self.events = [TrialEvent(t0, "phase:REFCAP", {})]
        self.log, self.diag = [], {}

    def _to_pixel(self, a: float, b: float, theta_deg: float):
        cal = self.ctx.calib
        phi = math.radians(cal.belt_dir_deg)
        u_hat, v_hat = np.array([math.cos(phi), math.sin(phi)]), np.array([-math.sin(phi), math.cos(phi)])
        p0 = a * u_hat + b * v_hat
        ang = math.radians(theta_deg + cal.belt_dir_deg)
        p1 = p0 + 5.0 * np.array([math.cos(ang), math.sin(ang)])
        uv = cal.world_to_pix(np.array([p0, p1]))
        du, dv = uv[1] - uv[0]
        return float(uv[0][0]), float(uv[0][1]), math.degrees(math.atan2(-dv, du)) % 180.0     # image v grows downwards (pixel_grasp convention)

    def step(self, t, frame, belt, state) -> Command:
        if self.finished:
            return Command(None, None, "DONE")
        if frame is not None and t - self.t0 >= self.settle_s:
            img = np.ascontiguousarray(frame.img)
            depth = getattr(frame, "depth_mm", None)
            if depth is None:
                depth = getattr(frame.img, "depth_mm", None)
            snap = self.det.gt.objects_at_capture(frame.img)
            dets = list(self.det.detect(frame.img, 0.0).dets)
            if len(snap) != 1 or len(dets) != 1:
                self.finished, self.outcome = True, f"refcap_bad:{len(snap)}obj/{len(dets)}det"
                return Command(None, None, "DONE")
            name, o = next(iter(snap.items()))
            d = dets[0]
            u, v, ang = self._to_pixel(d.a_mm, d.b_mm, d.theta_deg)
            cv2.imwrite(os.path.join(self.out, f"{name}.png"), img)
            if depth is not None:
                np.save(os.path.join(self.out, f"{name}_depth.npy"), np.asarray(depth, np.float32))
            sp = self.det.gt.spec(name)
            rec = {"name": name, "image": f"{name}.png", "depth": f"{name}_depth.npy" if depth is not None else None,
                   "grasp_px": {"u": u, "v": v, "angle_deg": ang, "width_mm": float(d.width_mm)},
                   "grasp_belt": {"a_mm": float(d.a_mm), "b_mm": float(d.b_mm), "theta_deg": float(d.theta_deg)},
                   "pose": {k: (float(x) if np.isscalar(x) else [float(y) for y in x]) for k, x in o.items() if k in ("a_mm", "b_mm", "yaw_deg", "pos_mm")},
                   "height_mm": float(sp.height_mm), "footprint_radius_mm": float(sp.footprint_radius_mm),
                   "t_capture": float(t), "image_size": [int(img.shape[1]), int(img.shape[0])]}
            with open(os.path.join(self.out, f"{name}.json"), "w") as f:
                json.dump(rec, f, indent=1)
            self.events.append(TrialEvent(t, "refcap", {"object": name, "u": round(u, 1), "v": round(v, 1), "angle": round(ang, 1)}))
            self.finished, self.outcome = True, "refcap"
            return Command(None, None, "DONE")
        return Command(None, None, "REFCAP")

    def close(self) -> None:
        pass


@register("REFCAP", privileged=True, doc="writes reference views for ports/ (object alone, stopped belt); not a method under test")
def make_refcap(ctx: MethodContext):
    if ctx.gt is None:
        raise RuntimeError("REFCAP needs the ground-truth tap")
    out = ctx.extra.get("refcap_out")
    if not out:
        raise RuntimeError("REFCAP: --method-arg refcap_out=DIR")
    return RefCapture(ctx, out, float(ctx.extra.get("settle_s", 0.5)))
