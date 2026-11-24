"""M4 v2 of the thesis: M4 (m4/diffusion_vs.py, frozen by PREREGISTRATION_M4.md) with ONE change, the descent release.

Why (diagnosis of the M4 TEST, 22/11/2026, runs/m4_test_c2_l05_*; scratch analysis in the thesis notes):
  M4 v1 holds z at the pre-grasp height until the gripper is over the gated object, then releases it.  The policy's own z reference has kept descending during
  the hold, so at the release the target jumps from the pre-grasp height to grasp height and the arm drops at the joint-rate limit.  Measured on the 60-scene TEST sheet:
  maximum descent speed in successful trials, median 148 mm/s for DP_W (M3) and 726 mm/s for M4 v1; in the 20 s before the first object displaced > 10 mm in the
  collision failures, median 18 mm/s (M3) and 486 mm/s (M4 v1); median max displacement of a pushed object 19.3 mm (M3) against 33.2 mm (M4 v1); collision failures 54 (M3), 66 (M4 v1).
  The correction offsets at the closing time are small in every class of failure (median 1.4-2.1 mm), so the xy/yaw correction itself is not what pushes.

v2: after the hold ends, the commanded z is not allowed to fall faster than VS2_VDESC (mm/s, default 150 = the natural DP descent) until it has caught up with the policy
z; while it is catching up and the policy wants to close, the gripper is kept open (the v1 authorization keeps its other conditions).  When no hold ever happened,
v2 behaves exactly like v1.  Everything else (checkpoints, tracker, gate, gains, authorization) is v1.

    DP_CKPT=... env -u PYTHONPATH ~/venvs/lerobot_data/bin/python remote_server.py --factory diffusion_vs2:make_method --name DPVS2 --port 6201 \
        --path m4v2 --path m4 --path . --path ../cl0 --repeat
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace

import numpy as np

from cl0.config import config_from_dict
from cl0.geometry import PlaneCalib, Rectifier
from cl0.kinematics import SO101Kinematics
from cl0.perception import BackgroundModel, Detector, window_of

from diffusion_vs import DPVSMethod, VSParams, _resolve


@dataclass
class VS2Params:
    vdesc: float = 150.0         # VS2_VDESC (mm/s): fastest z descent while catching up after a hold; 0 = v1 behaviour
    hold_open: bool = True       # VS2_HOLDOPEN: keep the gripper open while catching up
    mode: str = "rate"           # VS2_MODE: "rate" = rate-limited release (above); "pause" = the policy clock is paused while the descent is held, so the policy resumes its own descent at its own speed

    @staticmethod
    def from_env() -> "VS2Params":
        return VS2Params(vdesc=float(os.environ.get("VS2_VDESC", 150.0)), hold_open=os.environ.get("VS2_HOLDOPEN", "1") == "1", mode=os.environ.get("VS2_MODE", "rate"))


class DPVS2Method(DPVSMethod):
    phase = "DPVS2"

    def reset(self, t0, state) -> None:
        super().reset(t0, state)
        self.vs2 = VS2Params.from_env()
        self.z_prev = None
        self.catching = False
        self.diag.update({"v2_catch_ticks": 0, "v2_catch_open_ticks": 0, "v2_holds": 0, "v2_pause_ticks": 0})
        self.events[0].data["vs2"] = {"vdesc": self.vs2.vdesc, "hold_open": self.vs2.hold_open, "mode": self.vs2.mode}

    def _correct(self, t, tgt, x, s_now, dt):
        tgt_c, g_out, row = super()._correct(t, tgt, x, s_now, dt)
        v2 = self.vs2
        if v2.mode == "pause" and not (self.vs.off or self.closed_seen):
            if float(tgt_c[2]) > float(tgt[2]) + 1e-6:             # v1 is holding z above the policy reference: the policy clock waits too (its chunk is anchored at t_img)
                self.t_img += dt
                self.diag["v2_pause_ticks"] += 1
            return tgt_c, g_out, row
        if self.vs.off or self.closed_seen or v2.vdesc <= 0.0:
            self.catching, self.z_prev = False, float(tgt_c[2])
            return tgt_c, g_out, row
        z_pol, z_c = float(tgt[2]), float(tgt_c[2])
        if z_c > z_pol + 1e-6:                                   # v1 is holding z above the policy reference
            if not self.catching:
                self.diag["v2_holds"] += 1
            self.catching, self.z_prev = True, z_c
        elif self.catching:
            z_new = max(z_pol, float(self.z_prev) - v2.vdesc * dt)
            if z_new <= z_pol + 0.5:
                z_new, self.catching = z_pol, False
            tgt_c[2], self.z_prev = z_new, z_new
            self.diag["v2_catch_ticks"] += 1
            if v2.hold_open and self.catching and float(np.clip(tgt[5], 0.0, 100.0)) < self.vs.close_cmd_thr:
                g_out = max(g_out, self.g_open)
                self.diag["v2_catch_open_ticks"] += 1
            row["vs_zcmd"] = round(float(tgt_c[2]), 1)
            row["vs_gout"] = round(float(g_out), 1)
        else:
            self.z_prev = z_c
        return tgt_c, g_out, row


def make_method(info):
    cfg_d, calib_d = info["cfg"], info["calib"]
    cfg = config_from_dict(cfg_d)
    rb = cfg_d["robot"]
    kin = SO101Kinematics(urdf=rb.get("urdf") or None, tcp_offset_mm=rb["tcp_offset_mm"], margin_deg=rb["joint_margin_deg"])
    calib = PlaneCalib.load(_resolve(info["calib_path"]))
    bg = BackgroundModel.load(_resolve(info["background_path"]))
    det = Detector(Rectifier(calib, window_of(bg)), bg, cfg.perception)
    dur = float(os.environ.get("DP_T_S", cfg_d["executor"]["trial_timeout_s"]))
    return DPVS2Method(os.environ["DP_CKPT"], dur, kin, float(calib_d["belt_dir_deg"]), float(calib_d["z_plane_mm"]), rb, cfg_d["executor"],
                       int(os.environ.get("DP_REPLAN", "0")), os.environ.get("DP_DEVICE", "cuda"), int(os.environ.get("DP_STEPS", "0")),
                       det, replace(cfg.track, lost_s=max(cfg.track.lost_s, 6.0)), float(cfg.executor.arm_exclusion_mm), VSParams.from_env())
