"""Belt control: the belt's surface velocity (world frame, metres/s) along the direction of travel u."""
from __future__ import annotations

from .scene import belt_axes


def set_speed(stage, belt_path: str, dir_deg: float, v_mm_s: float) -> None:
    """Set the belt surface speed (mm/s, signed). Call arena.physics.flush(...) or step afterwards; the E1 check shows it takes effect on the next step."""
    from pxr import Gf, PhysxSchema
    u, _ = belt_axes(dir_deg)
    v = v_mm_s * 1e-3
    PhysxSchema.PhysxSurfaceVelocityAPI(stage.GetPrimAtPath(belt_path)).GetSurfaceVelocityAttr().Set(Gf.Vec3f(v * u[0], v * u[1], 0.0))
