"""ACT (LeRobot) as an arena method.  LeRobot is not in Isaac's Python, so it is served with remote_server.py from ~/venvs/lerobot_data (README §2.C):

    ACT_CKPT=runs/act_j0_s1000/checkpoints/last/pretrained_model env -u PYTHONPATH ~/venvs/lerobot_data/bin/python remote_server.py \
        --factory arena.methods.act_lerobot:make_method --name ACT_J0 --port 6001 --path . --repeat
    ~/env_isaac/bin/python -m arena.run_arena --methods REMOTE --method-arg remote=localhost:6001 ...

Observation as the demos were recorded (arena/demos.py): at each camera frame the image resized to 640x360 (INTER_AREA) and JPEG q95 round-tripped,
RGB, + state (5 joints deg + gripper 0-100).  One action per camera frame (the dataset is 30 fps), held between frames.  Interface I0: no belt input.
The method never declares success (the arena labels from GT); it ends after ACT_T_S seconds (default executor.trial_timeout_s).
Joint-space actions: a pipeline check, NOT the thesis policy (KE_HOACH_HUONG_1.md §3.3 fixes EE actions).
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

SIZE = (640, 360)
JPEG_Q = 95
CAMERA = "observation.images.front"


class ACTMethod:
    phase = "ACT"

    def __init__(self, ckpt: str, duration_s: float, device: str = "cuda"):
        from lerobot.policies.act.modeling_act import ACTPolicy
        from lerobot.policies.factory import make_pre_post_processors

        self.policy = ACTPolicy.from_pretrained(ckpt)
        self.policy.to(device).eval()
        self.pre, self.post = make_pre_post_processors(self.policy.config, pretrained_path=ckpt,
                                                       preprocessor_overrides={"device_processor": {"device": device}})
        self.duration_s, self.ckpt = duration_s, ckpt
        self.reset(0.0, None)

    def reset(self, t0, state) -> None:
        self.policy.reset()
        self.t0, self.finished, self.outcome = t0, False, ""
        self.events: List[TrialEvent] = [TrialEvent(t0, "phase:ACT", {"ckpt": self.ckpt})]
        self.log: list = []
        self.diag: dict = {}
        self.cmd = Command(None, None, "ACT")

    @torch.inference_mode()
    def _act(self, img_bgr: np.ndarray, state) -> np.ndarray:
        img = cv2.resize(img_bgr, SIZE, interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        rgb = cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        obs = {"observation.state": torch.from_numpy(np.r_[state.q_deg, state.gripper].astype(np.float32)),
               CAMERA: torch.from_numpy(rgb).permute(2, 0, 1).float().div(255.0)}
        a = self.post(self.policy.select_action(self.pre(obs)))
        return a.squeeze(0).float().cpu().numpy()

    def step(self, t, frame, belt, state) -> Command:
        if t - self.t0 >= self.duration_s:
            self.finished, self.outcome = True, "act_timeout"
            self.events.append(TrialEvent(t, "phase:DONE", {}))
            return Command(None, None, "DONE")
        if frame is not None:
            a = self._act(frame.img, state)
            self.cmd = Command(a[:5].astype(float), float(np.clip(a[5], 0.0, 100.0)), "ACT")
            self.log.append({"t": round(float(t), 4), **{f"a{i}": round(float(x), 3) for i, x in enumerate(a)}})
        return self.cmd

    def close(self) -> None:
        pass


def make_method(info):
    ckpt = os.environ["ACT_CKPT"]
    dur = float(os.environ.get("ACT_T_S", info["cfg"]["executor"]["trial_timeout_s"]))
    return ACTMethod(ckpt, dur, os.environ.get("ACT_DEVICE", "cuda"))
