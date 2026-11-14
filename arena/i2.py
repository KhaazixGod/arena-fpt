"""Interface I2 (KE_HOACH_HUONG_1.md §3.2): EE pose in the BELT frame, shared by the demo relabeller (to_lerobot_i2.py) and the policy (methods/act_i2.py).

Vector (6): [x_b, y_b, z, cos 2yaw, sin 2yaw, gripper]
    p_b = p_w - s(t) * u     (u = unit belt direction in W, s = belt travel in mm; z has no belt component)
    yaw = azimuth of the closing axis, mod 180 (SO101Kinematics.tool_axes), encoded as (cos 2yaw, sin 2yaw) so that 89 deg and -89 deg are neighbours
    tilt is fixed at cfg.robot.tilt_deg (the E6 ORACLE demos are within 1 deg of it on 99.4 % of frames)
Training uses LeRobot's RelativeActionsProcessorStep on x_b, y_b, z: the network predicts a_k = p_b,target(t_img + k/fps) - p_b,EE(t_img), exactly §3.2.
Joint-free on purpose: the network sees the image and this vector only.
"""
from __future__ import annotations

import math

import numpy as np

NAMES = ["x_b.mm", "y_b.mm", "z.mm", "yaw_cos2", "yaw_sin2", "gripper.pos"]
RELATIVE_EXCLUDE = ["yaw", "gripper"]          # RelativeActionsProcessorStep keeps these absolute (token match on NAMES)


def belt_unit(belt_dir_deg: float) -> np.ndarray:
    r = math.radians(belt_dir_deg)
    return np.array([math.cos(r), math.sin(r)])


def to_vec(kin, q_deg, gripper: float, s_mm: float, u: np.ndarray) -> np.ndarray:
    """Joints (5 deg) + gripper (0-100) -> I2 vector at belt travel s_mm."""
    p, _, _, _, yaw = kin.tool_axes(np.asarray(q_deg, float)[:5])
    y2 = math.radians(2.0 * yaw)
    return np.array([p[0] - s_mm * u[0], p[1] - s_mm * u[1], p[2], math.cos(y2), math.sin(y2), gripper], np.float64)


def to_world(vec, s_mm: float, u: np.ndarray):
    """I2 vector -> (p_w mm (3,), yaw deg in (-90, 90], gripper) at belt travel s_mm."""
    v = np.asarray(vec, float)
    yaw = 0.5 * math.degrees(math.atan2(v[4], v[3]))
    return np.array([v[0] + s_mm * u[0], v[1] + s_mm * u[1], v[2]]), yaw, float(v[5])
