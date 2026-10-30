"""Yaw-aware reachability by exact IK (cached), for the arena's ORACLE and the CL0_YAW variant.

cl0.reach.TopDownReach is built with the wrist roll fixed at 0, so it ignores how the grasp yaw moves the TCP when robot.tcp_offset_mm is large (here 29 mm
along the closing axis: gripper_frame_link sits on the fixed jaw).  E3 found an object at x = 147 mm whose lift pose is IK-reachable for closing-axis yaws
45..135 deg but not for 0/180, which is the yaw CL-0 uses for round objects (isotropic_theta_deg = 90 with phi = 90): the map says "unreachable" and CL-0
never selects it.  This class answers "reachable at THIS yaw?" with SO101Kinematics.ik + within_margin, cached on a 2 mm / 5 deg grid.
Same interface as TopDownReach.contains(x, y, z, inner_mm); the yaw is set on the object (``yaw_deg``) by the caller before asking.
"""
from __future__ import annotations

import math
from typing import Dict, Tuple

from cl0.kinematics import SO101Kinematics


class YawReach:
    def __init__(self, kin: SO101Kinematics, margin_deg: float, tilt_deg: float = 90.0, grid_mm: float = 2.0, grid_deg: float = 5.0):
        self.kin, self.margin, self.tilt = kin, margin_deg, tilt_deg
        self.grid_mm, self.grid_deg = grid_mm, grid_deg
        self.yaw_deg = 0.0
        self._cache: Dict[Tuple[int, int, int, int], bool] = {}
        self.n_ik = 0

    def ok(self, x: float, y: float, z: float, yaw_deg: float) -> bool:
        g, gd = self.grid_mm, self.grid_deg
        key = (int(round(x / g)), int(round(y / g)), int(round(z / g)), int(round((yaw_deg % 180.0) / gd)) % int(round(180.0 / gd)))
        v = self._cache.get(key)
        if v is None:
            xs, ys, zs, yw = key[0] * g, key[1] * g, key[2] * g, key[3] * gd
            r = self.kin.ik([xs, ys, zs], yw, tilt_deg=self.tilt)
            v = bool(r.ok and self.kin.within_margin(r.q_deg, self.margin))
            self._cache[key] = v
            self.n_ik += 1
        return v

    def contains(self, x: float, y: float, z: float, inner_mm: float = 0.0) -> bool:
        """TopDownReach-compatible.  ``inner_mm``: the point must also be reachable ``inner_mm`` farther from and closer to the pan axis."""
        if not self.ok(x, y, z, self.yaw_deg):
            return False
        if inner_mm > 0:
            r = math.hypot(x, y) or 1.0
            ux, uy = x / r, y / r
            return self.ok(x + inner_mm * ux, y + inner_mm * uy, z, self.yaw_deg) and self.ok(x - inner_mm * ux, y - inner_mm * uy, z, self.yaw_deg)
        return True
