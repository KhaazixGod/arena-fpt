"""Measured-latency emulation for the lockstep arena (thesis Section 8.8, real-time check).

The arena is lockstep: whatever a method computes at a tick is available at that same tick, so the 0.55 s that a chunk of the Diffusion Policy needs (100 denoising steps on the RTX 3070 Ti,
Table 8.9) and the 36 ms per frame of the CL-0 detector cost the simulated robot nothing.  A real controller has to live with them.  These two classes make the lockstep method behave as if
its heavy computations ran asynchronously on the measured hardware, without changing the simulation:

  * chunk latency: when the policy replans at tick t, the new chunk is computed at once but is ADOPTED only at t + (measured wall time of that sampling, times EMU_SCALE); until then the
    previous chunk keeps running, indexed by its own anchor time (that is how the executor already works).  The first chunk of a trial is adopted at once (the robot stands still).
  * detector latency (M4 only): the detector handles one camera frame at a time; frames that arrive while it is busy are dropped, and its result updates the tracker only at
    t + (measured wall time of the detection), with the capture time and belt travel of the frame it processed.

Environment: EMU_SCALE (default 1.0) multiplies the measured times (2.0 = a machine half as fast).  Served like any method:

    DP_CKPT=... python -m fptros.policy_node --factory fptros.emulated:make_dpvs2 --path m4v2 --path m4 --path . --path ../cl0     (M4 v2)
    DP_CKPT=... python -m fptros.policy_node --factory fptros.emulated:make_dp --path . --path ../cl0                               (M3)
"""
from __future__ import annotations

import os
import time

import numpy as np


class _ChunkLatency:
    """Mixin for DPI2Method subclasses: delayed adoption of a new chunk."""
    _pend = None               # (t_adopt, chunk, t_img or None)
    _t_img_eff = 0.0
    _t_now = 0.0
    emu_scale = 1.0

    @property
    def t_img(self):
        return self._t_img_eff

    @t_img.setter
    def t_img(self, v):
        if self._pend is not None and self._pend[2] is None:
            self._pend = (self._pend[0], self._pend[1], float(v))      # the anchor of the pending chunk; the running chunk keeps its own
        else:
            self._t_img_eff = float(v)

    def reset(self, t0, state) -> None:
        self._pend = None
        self.emu_scale = float(os.environ.get("EMU_SCALE", "1.0"))
        super().reset(t0, state)
        self.diag.update({"emu_chunk_latency_s_sum": 0.0, "emu_chunks": 0})

    def _sample(self, b):
        a = time.perf_counter()
        new = super()._sample(b)
        lat = (time.perf_counter() - a) * self.emu_scale
        if self.chunk is None:                       # nothing to run yet: the robot waits for its first chunk
            return new
        self._pend = (self._t_now + lat, new, None)
        self.diag["emu_chunk_latency_s_sum"] += lat
        self.diag["emu_chunks"] += 1
        return self.chunk                            # keep running the old chunk

    def _adopt_due(self, t):
        if self._pend is not None and self._pend[2] is not None and t >= self._pend[0]:
            self.chunk, self._t_img_eff = self._pend[1], self._pend[2]
            self._pend = None
            if hasattr(self, "c"):
                self.c[:] = 0.0                      # M4: the correction restarts with the chunk it was anchored to
            return True
        return False

    def step(self, t, frame, belt, state):
        self._t_now = t
        self._adopt_due(t)
        return super().step(t, frame, belt, state)


def _dp_class():
    from arena.methods.diffusion_i2 import DPI2Method

    class DPEmu(_ChunkLatency, DPI2Method):
        phase = "DP_EMU"
    return DPEmu


def _dpvs2_class():
    from diffusion_vs2 import DPVS2Method

    class DPVS2Emu(_ChunkLatency, DPVS2Method):
        phase = "DPVS2_EMU"
        det_busy_until = -1.0
        det_queue = None

        def reset(self, t0, state) -> None:
            self.det_busy_until, self.det_queue = -1.0, []
            super().reset(t0, state)
            self.diag.update({"emu_det_frames": 0, "emu_det_dropped": 0, "emu_det_latency_s_sum": 0.0})

        def _apply_det(self, t):
            while self.det_queue and self.det_queue[0][0] <= t:
                _, res, s_img, t_cap = self.det_queue.pop(0)
                self.tracker.update(res.dets, s_img, t_cap)
                self.tracker.prune(t, keep=self.tid)
                for d in res.dets:
                    if d.ok:
                        tr = self.tracker.match(d.a_mm - s_img, d.b_mm)
                        if tr is not None:
                            self.aspect.setdefault(tr.tid, []).append(float(d.aspect))
                            self.aspect[tr.tid] = self.aspect[tr.tid][-6:]

        def _perceive(self, t, frame, belt, p_ee_w) -> None:
            self._apply_det(t)
            if self.closed_seen:
                return
            if t < self.det_busy_until:
                self.diag["emu_det_dropped"] += 1
                return
            s_img = belt.s_at(frame.t_capture)
            exclude = [(float(p_ee_w @ np.r_[self.uu, 0.0]), float(p_ee_w @ np.r_[self.vv, 0.0]), self.arm_excl)]
            a = time.perf_counter()
            res = self.det.detect(frame.img, s_img, exclude)
            lat = (time.perf_counter() - a) * self.emu_scale
            self.diag["vs_det_s"] += lat / self.emu_scale
            self.diag["vs_frames"] += 1
            self.diag["emu_det_frames"] += 1
            self.diag["emu_det_latency_s_sum"] += lat
            self.det_busy_until = t + lat
            self.det_queue.append((t + lat, res, s_img, frame.t_capture))
    return DPVS2Emu


def make_dp(info):
    import arena.methods.diffusion_i2 as m
    cfg, calib = info["cfg"], info["calib"]
    rb = cfg["robot"]
    from cl0.kinematics import SO101Kinematics
    kin = SO101Kinematics(urdf=rb.get("urdf") or None, tcp_offset_mm=rb["tcp_offset_mm"], margin_deg=rb["joint_margin_deg"])
    dur = float(os.environ.get("DP_T_S", cfg["executor"]["trial_timeout_s"]))
    return _dp_class()(os.environ["DP_CKPT"], dur, kin, float(calib["belt_dir_deg"]), float(calib["z_plane_mm"]), rb, cfg["executor"],
                       int(os.environ.get("DP_REPLAN", "0")), os.environ.get("DP_DEVICE", "cuda"), int(os.environ.get("DP_STEPS", "0")))


def make_dpvs2(info):
    import diffusion_vs2 as v
    from dataclasses import replace
    from cl0.config import config_from_dict
    from cl0.geometry import PlaneCalib, Rectifier
    from cl0.kinematics import SO101Kinematics
    from cl0.perception import BackgroundModel, Detector, window_of
    from diffusion_vs import VSParams, _resolve
    cfg_d, calib_d = info["cfg"], info["calib"]
    cfg = config_from_dict(cfg_d)
    rb = cfg_d["robot"]
    kin = SO101Kinematics(urdf=rb.get("urdf") or None, tcp_offset_mm=rb["tcp_offset_mm"], margin_deg=rb["joint_margin_deg"])
    calib = PlaneCalib.load(_resolve(info["calib_path"]))
    bg = BackgroundModel.load(_resolve(info["background_path"]))
    det = Detector(Rectifier(calib, window_of(bg)), bg, cfg.perception)
    dur = float(os.environ.get("DP_T_S", cfg_d["executor"]["trial_timeout_s"]))
    return _dpvs2_class()(os.environ["DP_CKPT"], dur, kin, float(calib_d["belt_dir_deg"]), float(calib_d["z_plane_mm"]), rb, cfg_d["executor"],
                          int(os.environ.get("DP_REPLAN", "0")), os.environ.get("DP_DEVICE", "cuda"), int(os.environ.get("DP_STEPS", "0")),
                          det, replace(cfg.track, lost_s=max(cfg.track.lost_s, 6.0)), float(cfg.executor.arm_exclusion_mm), VSParams.from_env())
