"""Diffusion Policy with interface I2 (paper-dev; KE_HOACH_PAPER.md P4).  Same executor as ACT_I2 (arena/methods/act_i2.py: belt-frame targets turned into
world targets at execution time with the belt counter, IK seeded with the last command, joint rate limit, z guard); only the policy differs.
Trained with train_dp_i2.py on to_lerobot_i2.py data.  Served like ACT_I2:

    DP_CKPT=runs/dp_w_s1000/checkpoints/last/pretrained_model env -u PYTHONPATH ~/venvs/lerobot_data/bin/python remote_server.py \
        --factory arena.methods.diffusion_i2:make_method --name DP_I2 --port 6101 --path . --path ../cl0 --repeat

Diffusion Policy looks at the last n_obs_steps observations (2: the newest frame and the one 1/30 s before, as in training).  So EVERY camera frame is
preprocessed and pushed into the policy's observation queue (state at the frame's capture time, as the demos recorded it); every DP_REPLAN frames
(default the policy's n_action_steps) a chunk is sampled from the queue.  The chunk starts at the newest observation, whose state the relative step has
cached, and the postprocessor turns it into absolute belt-frame targets for t_capture + k / fps.  Env: DP_CKPT, DP_REPLAN, DP_T_S (default
executor.trial_timeout_s), DP_DEVICE, DP_STEPS (number of denoising steps at inference; default the checkpoint's).
"""
from __future__ import annotations

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

from arena.i2 import belt_unit, to_vec
from arena.methods.act_i2 import ACTI2Method
from arena.methods.act_lerobot import CAMERA, JPEG_Q, SIZE


class DPI2Method(ACTI2Method):
    phase = "DP_I2"

    def __init__(self, ckpt: str, duration_s: float, kin: SO101Kinematics, belt_dir_deg: float, z_belt_mm: float, robot: dict, executor: dict,
                 replan: int = 0, device: str = "cuda", n_infer_steps: int = 0):
        import arena.dp_i2  # noqa: F401  (registers the relative step of the saved preprocessor)
        from lerobot.policies.diffusion.modeling_diffusion import DiffusionPolicy
        from lerobot.policies.factory import make_pre_post_processors
        from lerobot.policies.utils import populate_queues

        self._populate = populate_queues
        self.policy = DiffusionPolicy.from_pretrained(ckpt)
        if n_infer_steps > 0:
            self.policy.diffusion.num_inference_steps = int(n_infer_steps)
        self.policy.to(device).eval()
        self.pre, self.post = make_pre_post_processors(self.policy.config, pretrained_path=ckpt,
                                                       preprocessor_overrides={"device_processor": {"device": device}})
        self.fps = 30.0
        self.replan = replan or self.policy.config.n_action_steps
        self.commit, self.commit_thr = False, 20.0
        self.kin, self.u = kin, belt_unit(belt_dir_deg)
        self.tilt, self.margin, self.qdot = float(robot["tilt_deg"]), float(robot["joint_margin_deg"]), float(robot["q_dot_max_deg_s"])
        self.z_min = z_belt_mm + float(executor["min_z_above_belt_mm"])
        self.duration_s, self.ckpt = duration_s, ckpt
        self.needs_task = False
        self.task_vec = None
        self.reset(0.0, None)

    def reset(self, t0, state) -> None:
        super().reset(t0, state)                                       # ACT_I2's reset + policy.reset() (empties DP's queues)
        self.events: List[TrialEvent] = [TrialEvent(t0, "phase:DP_I2", {"ckpt": self.ckpt, "replan": self.replan,
                                                                        "infer_steps": int(self.policy.diffusion.num_inference_steps)})]

    @torch.inference_mode()
    def _observe(self, img_bgr: np.ndarray, vec: np.ndarray) -> dict:
        """Preprocess one observation (as act_i2/act_lerobot: resize, JPEG round trip) and push it into DP's queues; returns the batch."""
        img = cv2.resize(img_bgr, SIZE, interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        rgb = cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        obs = {"observation.state": torch.from_numpy(vec.astype(np.float32)),
               CAMERA: torch.from_numpy(rgb).permute(2, 0, 1).float().div(255.0)}
        b = self.pre(obs)                                              # caches THIS state for the absolute step
        b.pop("action", None)
        b = dict(b)
        b["observation.images"] = torch.stack([b[k] for k in self.policy.config.image_features], dim=-4)
        self.policy._queues = self._populate(self.policy._queues, b)
        return b

    @torch.inference_mode()
    def _sample(self, b: dict) -> np.ndarray:
        chunk = self.policy.predict_action_chunk(b)                    # (1, n_action_steps, 6) relative, normalised, from the newest observation on
        return self.post(chunk).squeeze(0).float().cpu().numpy()        # absolute belt-frame targets

    def step(self, t, frame, belt, state) -> Command:                 # = ACTI2Method.step with "observe every frame, sample every `replan` frames"
        if t - self.t0 >= self.duration_s:
            self.finished, self.outcome = True, "dp_timeout"
            self.events.append(TrialEvent(t, "phase:DONE", {}))
            return Command(None, None, "DONE")
        dt, self.t_prev = max(t - self.t_prev, 1e-3), t
        x = np.r_[np.asarray(state.q_deg, float), float(state.gripper)]
        if self.q_last is None:
            self.q_last = x[:5].copy()
        self.hist_t.append(float(t)); self.hist_x.append(x)
        if frame is not None:
            t_img = float(frame.t_capture)
            xs = self._state_at(t_img)
            s_img = belt.s_at(t_img)
            vec = to_vec(self.kin, xs[:5], xs[5], s_img, self.u)
            b = self._observe(frame.img, vec)
            self.frames_since += 1
            if self.chunk is None or self.frames_since >= self.replan:
                self.chunk, self.t_img, self.frames_since = self._sample(b), t_img, 0
                self.diag["plans"] += 1
                self.log.append({"t": round(float(t), 4), "t_img": round(t_img, 4), "s_img": round(float(s_img), 2),
                                 **{f"st{i}": round(float(v), 3) for i, v in enumerate(vec)},
                                 **{f"a0_{i}": round(float(v), 3) for i, v in enumerate(self.chunk[0])}})
        if self.chunk is None:
            return self.cmd
        from arena.i2 import to_world
        k = min(max((t - self.t_img) * self.fps, 0.0), len(self.chunk) - 1.0)
        i = int(k); w = k - i
        tgt = self.chunk[i] if i + 1 >= len(self.chunk) else (1 - w) * self.chunk[i] + w * self.chunk[i + 1]
        p, yaw, g = to_world(tgt, belt.s_at(t), self.u)
        self.cmd = Command(self._ik(t, p, yaw, dt), float(np.clip(g, 0.0, 100.0)), "DP_I2")
        return self.cmd


def make_method(info):
    cfg, calib = info["cfg"], info["calib"]
    rb = cfg["robot"]
    kin = SO101Kinematics(urdf=rb.get("urdf") or None, tcp_offset_mm=rb["tcp_offset_mm"], margin_deg=rb["joint_margin_deg"])
    dur = float(os.environ.get("DP_T_S", cfg["executor"]["trial_timeout_s"]))
    return DPI2Method(os.environ["DP_CKPT"], dur, kin, float(calib["belt_dir_deg"]), float(calib["z_plane_mm"]), rb, cfg["executor"],
                      int(os.environ.get("DP_REPLAN", "0")), os.environ.get("DP_DEVICE", "cuda"), int(os.environ.get("DP_STEPS", "0")))
