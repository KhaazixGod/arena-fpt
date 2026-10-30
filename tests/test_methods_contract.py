"""Every registered method implements the contract; NOOP/ORACLE behave as documented; a method's exception is its own failure."""
import math
import os

import numpy as np
import pytest

from conftest import ARENA


def _ctx(cfg, gt=None):
    from arena.methods import MethodContext
    from cl0.geometry import PlaneCalib
    from cl0.kinematics import SO101Kinematics
    cdir = os.path.join(ARENA, "runs", "calib")
    calib = PlaneCalib.load(os.path.join(cdir, "calib.json"))
    kin = SO101Kinematics(tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
    return MethodContext(cfg, kin, calib, os.path.join(cdir, "calib.json"), os.path.join(cdir, "background.npz"), (1280, 720), 50.0, gt=gt)


needs_calib = pytest.mark.skipif(not os.path.exists(os.path.join(ARENA, "runs", "calib", "background.npz")), reason="run calib_from_scene.py first")


def test_noop(arena_cfg):
    from arena.methods import REGISTRY, check_contract
    m = REGISTRY["NOOP"].factory(_ctx(arena_cfg) if os.path.exists(os.path.join(ARENA, "runs", "calib", "calib.json")) else type("C", (), {"cfg": arena_cfg})())
    assert check_contract(m) == []
    m.reset(0.0, None)
    t = 0.0
    while not m.finished:
        cmd = m.step(t, None, None, None)
        assert cmd.q_deg is None and cmd.gripper is None
        t += 0.02
    assert m.outcome == "noop" and math.isclose(t, arena_cfg.executor.trial_timeout_s, abs_tol=0.05)     # +1 tick of float accumulation


@needs_calib
def test_cl0_and_oracle_contract(arena_cfg):
    from arena.methods import REGISTRY, check_contract

    class Tap:
        belt_top_mm = -2.4

        def objects_at_capture(self, img):
            return {}

        def spec(self, n):
            raise KeyError(n)
    assert check_contract(REGISTRY["CL0"].factory(_ctx(arena_cfg))) == []
    assert check_contract(REGISTRY["CL0_YAW"].factory(_ctx(arena_cfg))) == []
    assert check_contract(REGISTRY["ORACLE"].factory(_ctx(arena_cfg, Tap()))) == []
    with pytest.raises(RuntimeError):
        REGISTRY["ORACLE"].factory(_ctx(arena_cfg, None))


@needs_calib
def test_oracle_detector_geometry(arena_cfg):
    from arena.methods.oracle import OracleDetector
    from arena.objects import INTERIM_SPECS, ObjSpec
    specs = {s.name: s for s in INTERIM_SPECS}
    specs["wide"] = ObjSpec("wide", "box", (80.0, 70.0, 20.0), (1, 1, 1), 50.0)
    top = -2.4
    img = np.zeros((2, 2, 3), np.uint8)

    def o(a, b, h, yaw, lift=0.0):
        return {"a_mm": a, "b_mm": b, "pos_mm": np.array([-b, a, top + h / 2 + lift]), "yaw_deg": yaw}

    snap = {"bar50x25": o(10.0, -180.0, 22.0, 120.0), "cyl35": o(-60.0, -170.0, 30.0, 0.0), "cube35": o(500.0, -180.0, 25.0, 0.0),
            "cyl28": o(50.0, -200.0, 40.0, 0.0, lift=40.0), "wide": o(-150.0, -180.0, 20.0, 90.0)}

    class Tap:
        belt_top_mm = top

        def objects_at_capture(self, im):
            return snap if im is img else {}

        def spec(self, n):
            return specs[n]

    det = OracleDetector(_ctx(arena_cfg, Tap()))
    res = det.detect(img, 0.0, exclude=[(-60.0, -170.0, 20.0)])
    d = {round(x.a_mm): x for x in res.dets}
    assert set(d) == {10, -60, -150}                     # outside the window (a = 500) and the lifted one are not seen
    bar = d[10]
    assert math.isclose(bar.theta_deg, (120 + 90 - 90) % 180, abs_tol=0.01) and bar.width_mm == 25.0 and bar.ok   # calibrated phi = 89.998
    radial = math.degrees(math.atan2(-60.0 - 0.0, 170.0 - 38.8))                     # round object: closing axis tangential to the pan circle
    assert d[-60].reject == "arm" and math.isclose(d[-60].theta_deg, (radial + 90.0 - 90.0) % 180.0, abs_tol=0.05)
    assert d[-150].reject == "wide"


def test_method_exception_is_method_failure():
    from arena.trial import TimedMethod

    class Bad:
        finished, outcome, events, log, diag = False, "", [], [], {}

        def reset(self, t, s):
            pass

        def step(self, t, f, b, s):
            raise ValueError("boom")
    m = TimedMethod(Bad())
    m.reset(0.0, None)
    cmd = m.step(0.0, None, None, None)
    assert m.finished and m.outcome == "method_exception:ValueError" and cmd.q_deg is None
    assert "boom" in m.exc_trace


def test_yaw_reach_matches_the_e3_case(arena_cfg):
    """The E3 case: cyl28 at x = 147 mm, y = 0, lift height: unreachable for a radial closing axis (yaw 0), reachable for a tangential one (yaw 90)."""
    from arena.reach_yaw import YawReach
    from cl0.kinematics import SO101Kinematics
    kin = SO101Kinematics(tcp_offset_mm=arena_cfg.robot.tcp_offset_mm, margin_deg=arena_cfg.robot.joint_margin_deg)
    yr = YawReach(kin, arena_cfg.robot.joint_margin_deg)
    z_lift = -2.4 + arena_cfg.executor.lift_height_mm
    assert not yr.ok(146.9, 0.0, z_lift, 0.0)
    assert yr.ok(146.9, 0.0, z_lift, 90.0)
    n = yr.n_ik
    yr.ok(146.5, 0.3, z_lift, 91.0)                                                # same 2 mm / 5 deg cell: cached
    assert yr.n_ik == n


@needs_calib
def test_pixel_grasp_adapter_maps_pixels_to_the_belt(arena_cfg):
    """A grasp given in pixels lands at the belt-frame point the calibration says, with the right closing angle; the example plug-in loads by path."""
    from arena.methods import check_contract, resolve
    from arena.methods.pixel_grasp import PixelGrasp, PixelGraspDetector
    ctx = _ctx(arena_cfg)
    x, y = 190.0, 30.0                                         # W point on the belt: a = y, b = -x for phi = 90
    u, v = ctx.calib.world_to_pix(np.array([[x, y]]))[0]
    det = PixelGraspDetector(ctx, lambda img, d: [PixelGrasp(u, v, 0.0, 30.0)])
    res = det.detect(np.zeros((720, 1280, 3), np.uint8), 0.0)
    assert len(res.dets) == 1
    g = res.dets[0]
    assert abs(g.a_mm - y) < 0.5 and abs(g.b_mm + x) < 0.5
    # image +u (right) is the belt direction u in this camera set-up, so a closing axis along image u has theta ~ 0 (mod 180)
    assert min(g.theta_deg, 180.0 - g.theta_deg) < 1.0 and g.ok
    m = resolve("arena.methods.examples.blob:make_method").factory(ctx)
    assert check_contract(m) == []
