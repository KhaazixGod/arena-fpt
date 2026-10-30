"""Nothing a method receives (frame, robot state, belt) leads to the world, the platform or the ground-truth tap (plan §2 'chặn rò rỉ')."""
import types

import numpy as np


def _reachable(roots, max_depth=6):
    seen, out, todo = set(), [], [(r, 0) for r in roots]
    while todo:
        x, d = todo.pop()
        if id(x) in seen or d > max_depth:
            continue
        seen.add(id(x))
        out.append(x)
        if isinstance(x, (types.ModuleType, types.FunctionType, type, str, bytes, int, float, bool, type(None), np.ndarray)):
            continue
        kids = []
        if isinstance(x, types.MethodType):
            kids.append(x.__self__)
        if isinstance(x, dict):
            kids += list(x.keys()) + list(x.values())
        elif isinstance(x, (list, tuple, set, frozenset)):
            kids += list(x)
        if hasattr(x, "__dict__"):
            kids += list(vars(x).values())
        for sl in getattr(type(x), "__slots__", ()):
            if hasattr(x, sl):
                kids.append(getattr(x, sl))
        todo += [(k, d + 1) for k in kids]
    return out


def test_method_inputs_do_not_reach_the_world(fake_platform):
    from arena.platform import IsaacPlatform
    from arena.run_arena import GTTap
    plat, w = fake_platform
    tap = GTTap(w)
    plat.frame_hooks.append(tap.on_capture)
    plat.reset_trial([{"name": "cyl35", "a_mm": 0.0, "b_mm": -180.0, "yaw_deg": 0.0}])
    plat.start_belt(40.0)
    fr = None
    for _ in range(20):
        plat.wait_tick()
        fr = plat.poll_frame() or fr
    state = plat.robot_state()
    bad = (IsaacPlatform, type(w), GTTap)
    leaks = [type(x).__name__ for x in _reachable([plat.belt, fr, state]) if isinstance(x, bad)]
    assert fr is not None
    assert leaks == [], f"method inputs reach {leaks}"


def test_only_privileged_methods_get_ground_truth(arena_cfg):
    from arena.methods import REGISTRY, register
    from arena.run_arena import build_methods
    from cl0.types import Command
    seen = {}

    class Dummy:
        finished, outcome, events, log, diag = True, "x", [], [], {}

        def reset(self, t, s):
            pass

        def step(self, t, f, b, s):
            return Command(None, None, "X")

    @register("_T_PLAIN")
    def plain(ctx):
        seen["plain"] = ctx.gt
        return Dummy()

    @register("_T_PRIV", privileged=True)
    def priv(ctx):
        seen["priv"] = ctx.gt
        return Dummy()

    try:
        tap = object()
        build_methods(["_T_PLAIN", "_T_PRIV"], arena_cfg, None, None, "", "", tap)
        assert seen["plain"] is None and seen["priv"] is tap
    finally:
        REGISTRY.pop("_T_PLAIN", None)
        REGISTRY.pop("_T_PRIV", None)


def test_oracle_sees_capture_time_not_now(fake_platform):
    """With rendering skipped, frames are still distinct objects and the GT tap returns the pose AT CAPTURE (0.1 s old), never the current one."""
    from arena.run_arena import GTTap
    plat, w = fake_platform
    tap = GTTap(w)
    plat.frame_hooks.append(tap.on_capture)
    plat.render_enabled = False
    plat.reset_trial([{"name": "cyl35", "a_mm": -100.0, "b_mm": -180.0, "yaw_deg": 0.0}])
    plat.start_belt(60.0)
    ids, checked = set(), 0
    for _ in range(100):
        plat.wait_tick()
        fr = plat.poll_frame()
        if fr is None:
            continue
        ids.add(id(fr.img))
        snap = tap.objects_at_capture(fr.img)
        now = w.gt_objects()["cyl35"]["a_mm"]
        if plat.belt_s_true() > 20.0:                       # belt at speed: the capture-time pose lags the current one by v * latency
            assert 4.0 < now - snap["cyl35"]["a_mm"] < 8.0
            checked += 1
    assert checked > 5 and len(ids) > 20
