"""ACT with interface I2 (KE_HOACH_HUONG_1.md §3.2): actions are EE targets in the BELT frame, relative to the EE at image time; this executor converts
them to W at EXECUTION time with the belt counter and solves IK.  Trained with train_act_i2.py on to_lerobot_i2.py data.  Served like act_lerobot.py:

    ACT_CKPT=runs/act_i2_s1000/checkpoints/last/pretrained_model env -u PYTHONPATH ~/venvs/lerobot_data/bin/python remote_server.py \
        --factory arena.methods.act_i2:make_method --name ACT_I2 --port 6001 --path . --path ../cl0 --repeat

At each planning frame (every ACT_REPLAN camera frames, default the policy's n_action_steps):
    state  = I2 vector of the joints measured at the frame's CAPTURE time (as the demos recorded it) with s = belt.s_at(t_capture)
    chunk  = postprocess(model(preprocess(image, state)))       # absolute belt-frame targets for t_capture + k / fps, k = 0..chunk-1
Every control tick t: target = chunk interpolated at (t - t_capture) * fps, p_w = to_world(target, belt.s_at(t)), IK at the fixed tilt seeded with the
last command, joint rate limit cfg.robot.q_dot_max_deg_s, z >= belt + executor.min_z_above_belt_mm (the same guards as cl0.executor.BeltExecutor).
Image preprocessing as act_lerobot.py.  The method never declares success; it ends after ACT_T_S seconds (default executor.trial_timeout_s).
"""
from __future__ import annotations

import bisect
import os
from typing import List

import cv2
import numpy as np
import torch

try:
    from cl0.types import Command, TrialEvent
except Exception:                          # noqa: BLE001  (remote_server.py's fallbacks have the same fields)
    from remote_server import Command, TrialEvent  # type: ignore
from cl0.kinematics import SO101Kinematics

from arena.i2 import belt_unit, to_vec, to_world
from arena.methods.act_lerobot import CAMERA, JPEG_Q, SIZE


class ACTI2Method:
    phase = "ACT_I2"
    commit = False                  # ACT_COMMIT=1: replan every `replan` frames while the policy's own gripper command is OPEN; once it commands CLOSE,
    commit_thr = 20.0               # follow that chunk to its end (n_action_steps frames).  Open 40, close 0 in the demos.  See ARENA_SETUP_REPORT.md E16.

    def __init__(self, ckpt: str, duration_s: float, kin: SO101Kinematics, belt_dir_deg: float, z_belt_mm: float, robot: dict, executor: dict,
                 replan: int = 0, device: str = "cuda", commit: bool = False, commit_thr: float = 20.0):
        from lerobot.policies.act.modeling_act import ACTPolicy
        from lerobot.policies.factory import make_pre_post_processors

        self.policy = ACTPolicy.from_pretrained(ckpt)
        self.policy.to(device).eval()
        self.pre, self.post = make_pre_post_processors(self.policy.config, pretrained_path=ckpt,
                                                       preprocessor_overrides={"device_processor": {"device": device}})
        self.fps = 30.0
        self.replan = replan or self.policy.config.n_action_steps
        self.commit, self.commit_thr = commit, commit_thr
        self.kin, self.u = kin, belt_unit(belt_dir_deg)
        self.tilt, self.margin, self.qdot = float(robot["tilt_deg"]), float(robot["joint_margin_deg"]), float(robot["q_dot_max_deg_s"])
        self.z_min = z_belt_mm + float(executor["min_z_above_belt_mm"])
        self.duration_s, self.ckpt = duration_s, ckpt
        self.reset(0.0, None)

    def reset(self, t0, state) -> None:
        if self.policy is not None:
            self.policy.reset()
        self.t0, self.finished, self.outcome = t0, False, ""
        self.events: List[TrialEvent] = [TrialEvent(t0, "phase:ACT_I2", {"ckpt": self.ckpt, "replan": self.replan})]
        self.log: list = []
        self.diag: dict = {"plans": 0, "ik_fail_ticks": 0, "ik_fail_ticks_lt6s": 0, "ik_fail_first_t": -1.0, "commit_t": -1.0}
        self.hist_t: list = []
        self.hist_x: list = []
        self.chunk = None
        self.t_img = 0.0
        self.frames_since = 0
        self.q_last = None if state is None else np.asarray(state.q_deg, float).copy()
        self.t_prev = t0
        self.cmd = Command(None, None, "ACT_I2")

    def _state_at(self, t: float) -> np.ndarray:
        """[q 5 deg, gripper] measured at time t, linear between the recorded control ticks."""
        i = bisect.bisect_left(self.hist_t, t)
        if i <= 0:
            return self.hist_x[0]
        if i >= len(self.hist_t):
            return self.hist_x[-1]
        t0, t1 = self.hist_t[i - 1], self.hist_t[i]
        w = (t - t0) / max(t1 - t0, 1e-9)
        return (1 - w) * self.hist_x[i - 1] + w * self.hist_x[i]

    @torch.inference_mode()
    def _plan(self, img_bgr: np.ndarray, vec: np.ndarray, t_img: float):
        """-> (chunk (n, 6) absolute belt-frame targets, time of chunk[0])."""
        img = cv2.resize(img_bgr, SIZE, interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        rgb = cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        obs = {"observation.state": torch.from_numpy(vec.astype(np.float32)),
               CAMERA: torch.from_numpy(rgb).permute(2, 0, 1).float().div(255.0)}
        chunk = self.policy.predict_action_chunk(self.pre(obs))          # relative, normalised; the preprocessor cached THIS state
        return self.post(chunk).squeeze(0).float().cpu().numpy(), t_img   # (chunk, 6) absolute belt-frame targets

    def _ik(self, t: float, p, yaw, dt: float) -> np.ndarray:
        p = np.array([p[0], p[1], max(p[2], self.z_min)])
        r = self.kin.ik(p, yaw, q0_deg=self.q_last, tilt_deg=self.tilt, max_seeds=1, max_iter=15)
        if not (r.ok and self.kin.within_margin(r.q_deg, self.margin)):
            r = self.kin.ik(p, yaw, q0_deg=self.q_last, tilt_deg=self.tilt, max_seeds=4, max_iter=25)
        if not (r.ok and self.kin.within_margin(r.q_deg, self.margin)):
            self.diag["ik_fail_ticks"] += 1
            if t - self.t0 < 6.0:
                self.diag["ik_fail_ticks_lt6s"] += 1
            if self.diag["ik_fail_first_t"] < 0:
                self.diag["ik_fail_first_t"] = round(float(t - self.t0), 3)
                self.diag["ik_fail_first"] = {"p": [round(float(x), 1) for x in p], "yaw": round(float(yaw), 1), "pos_err_mm": round(float(r.pos_err_mm), 2),
                                              "q": [round(float(x), 1) for x in r.q_deg], "ok": bool(r.ok)}
            return self.q_last.copy()
        lim = self.qdot * dt
        self.q_last = self.q_last + np.clip(r.q_deg - self.q_last, -lim, lim)
        return self.q_last.copy()

    def step(self, t, frame, belt, state) -> Command:
        if t - self.t0 >= self.duration_s:
            self.finished, self.outcome = True, "act_timeout"
            self.events.append(TrialEvent(t, "phase:DONE", {}))
            return Command(None, None, "DONE")
        dt, self.t_prev = max(t - self.t_prev, 1e-3), t
        x = np.r_[np.asarray(state.q_deg, float), float(state.gripper)]
        if self.q_last is None:
            self.q_last = x[:5].copy()
        self.hist_t.append(float(t)); self.hist_x.append(x)
        if frame is not None:
            self.frames_since += 1
            interval = self.replan
            if self.commit and self.cmd.gripper is not None and self.cmd.gripper < self.commit_thr:
                interval = self.policy.config.n_action_steps
                if self.diag["commit_t"] < 0:
                    self.diag["commit_t"] = round(float(t - self.t0), 3)
            if self.chunk is None or self.frames_since >= interval:
                t_img = float(frame.t_capture)
                xs = self._state_at(t_img)
                s_img = belt.s_at(t_img)
                vec = to_vec(self.kin, xs[:5], xs[5], s_img, self.u)
                (self.chunk, self.t_img), self.frames_since = self._plan(frame.img, vec, t_img), 0
                self.diag["plans"] += 1
                self.log.append({"t": round(float(t), 4), "t_img": round(t_img, 4), "s_img": round(float(s_img), 2),
                                 **{f"st{i}": round(float(v), 3) for i, v in enumerate(vec)},
                                 **{f"a0_{i}": round(float(v), 3) for i, v in enumerate(self.chunk[0])}})
        if self.chunk is None:
            return self.cmd
        k = min(max((t - self.t_img) * self.fps, 0.0), len(self.chunk) - 1.0)
        i = int(k); w = k - i
        tgt = self.chunk[i] if i + 1 >= len(self.chunk) else (1 - w) * self.chunk[i] + w * self.chunk[i + 1]
        p, yaw, g = to_world(tgt, belt.s_at(t), self.u)
        self.cmd = Command(self._ik(t, p, yaw, dt), float(np.clip(g, 0.0, 100.0)), "ACT_I2")
        return self.cmd

    def close(self) -> None:
        pass


def make_method(info):
    cfg, calib = info["cfg"], info["calib"]
    rb = cfg["robot"]
    kin = SO101Kinematics(urdf=rb.get("urdf") or None, tcp_offset_mm=rb["tcp_offset_mm"], margin_deg=rb["joint_margin_deg"])
    dur = float(os.environ.get("ACT_T_S", cfg["executor"]["trial_timeout_s"]))
    return ACTI2Method(os.environ["ACT_CKPT"], dur, kin, float(calib["belt_dir_deg"]), float(calib["z_plane_mm"]), rb, cfg["executor"],
                       int(os.environ.get("ACT_REPLAN", "0")), os.environ.get("ACT_DEVICE", "cuda"),
                       os.environ.get("ACT_COMMIT", "0") == "1", float(os.environ.get("ACT_COMMIT_THR", "20")))
