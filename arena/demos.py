"""E6: record expert demonstrations (normally ORACLE) as raw episodes inside Isaac; arena/to_lerobot.py turns them into a LeRobotDataset.

One episode = one trial.  At every camera frame (30 fps): the image (resized, JPEG q95), observation.state = measured joints (5 deg, LeRobot order) + gripper
(0-100), action = the targets the expert had commanded at that instant (5 deg + gripper; before its first command: the current state).  Same feature names as
the real lerobot-record of an SO-101 follower: "shoulder_pan.pos" ... "gripper.pos".  Saved: <dir>/episode_XXXX.npz with the arrays + JPEG bytes.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

import cv2
import numpy as np

JOINT_NAMES = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]


class DemoRecorder:
    """Platform frame hook.  ``method`` = the TimedMethod (its ``last_cmd`` is the expert's latest command)."""

    def __init__(self, plat, method, size=(640, 360), jpeg_quality: int = 95):
        self.plat, self.method, self.size, self.q = plat, method, size, jpeg_quality
        self.t: List[float] = []
        self.state: List[np.ndarray] = []
        self.action: List[np.ndarray] = []
        self.jpeg: List[bytes] = []
        self._act: Optional[np.ndarray] = None

    def __call__(self, t: float, img: np.ndarray) -> None:
        rs = self.plat.robot_state()
        st = np.r_[rs.q_deg, rs.gripper].astype(np.float32)
        if self._act is None:
            self._act = st.copy()
        cmd = getattr(self.method, "last_cmd", None)
        if cmd is not None:
            if cmd.q_deg is not None:
                self._act[:5] = np.asarray(cmd.q_deg, np.float32)
            if cmd.gripper is not None:
                self._act[5] = float(cmd.gripper)
        ok, buf = cv2.imencode(".jpg", cv2.resize(img, self.size, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, self.q])
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        self.t.append(t); self.state.append(st); self.action.append(self._act.copy()); self.jpeg.append(buf.tobytes())

    def save(self, path: str, meta: dict) -> int:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez_compressed(path, t=np.asarray(self.t, np.float64), state=np.stack(self.state), action=np.stack(self.action),
                            jpeg=np.array(self.jpeg, dtype=object), names=np.array(JOINT_NAMES), meta=json.dumps(meta, default=float))
        return len(self.t)
