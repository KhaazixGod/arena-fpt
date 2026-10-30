"""CL0: the frozen-candidate baseline, unchanged (cl0.system.build_stack with arena.toml, calib.json and background.npz generated from the scene)."""
from __future__ import annotations

import copy

from cl0.system import build_stack

from .base import MethodContext, register


@register("CL0", doc="CL-0 baseline (cl0 package, unchanged)")
def make_cl0(ctx: MethodContext):
    cfg = copy.deepcopy(ctx.cfg)
    return build_stack(cfg, ctx.calib_path, ctx.background_path, cache_dir=ctx.cache_dir).ctrl
