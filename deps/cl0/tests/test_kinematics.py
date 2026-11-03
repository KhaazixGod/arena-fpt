import numpy as np
import pytest


def _topdown_q(kin, rng, tilt=90.0):
    lo, hi = kin.limits_deg
    for _ in range(1000):
        pan = rng.uniform(lo[0] + 15, hi[0] - 15)
        lift = rng.uniform(lo[1] + 15, hi[1] - 15)
        elbow = rng.uniform(lo[2] + 15, hi[2] - 15)
        flex = tilt - lift - elbow - kin._pitch_c0
        roll = rng.uniform(lo[4] + 15, hi[4] - 15)
        if lo[3] + 10 < flex < hi[3] - 10:
            return np.array([pan, lift, elbow, flex, roll])
    raise RuntimeError("không sinh được cấu hình thẳng đứng")


def test_fk_ik_roundtrip(kin):
    rng = np.random.default_rng(0)
    n = 0
    for _ in range(40):
        q = _topdown_q(kin, rng)
        p, _, _, _, yaw = kin.tool_axes(q)
        r = kin.ik(p, yaw, tilt_deg=90.0)
        assert r.ok, f"IK không hội tụ cho q={q.round(1)} p={p.round(1)}"
        p2, _, _, _, yaw2 = kin.tool_axes(r.q_deg)
        assert np.linalg.norm(p2 - p) < 0.1
        dy = (yaw2 - yaw + 90) % 180 - 90                 # yaw xác định mod 180
        assert abs(dy) < 0.3
        n += 1
    assert n == 40


def test_ik_unreachable_is_reported(kin):
    assert not kin.ik([900.0, 0.0, 0.0], 0.0, tilt_deg=90.0).ok
    assert not kin.ik([-400.0, 0.0, 0.0], 0.0, tilt_deg=90.0).ok


def test_tool_axis_points_down_for_tilt90(kin):
    r = kin.ik([200.0, 30.0, -20.0], 25.0, tilt_deg=90.0)
    assert r.ok
    p, approach, closing, pitch, yaw = kin.tool_axes(r.q_deg)
    assert approach[2] < -0.999                         # trục tiến vào thẳng xuống
    assert abs(((yaw - 25.0) + 90) % 180 - 90) < 0.3


def test_warm_start_ik_is_continuous(kin):
    q = np.array([0.0, -49.0, 48.0, 91.0, 0.0])          # tư thế nhà: nhánh roll gần 0 (như bộ điều khiển thật)
    prev = None
    for y in np.arange(-60.0, 60.0, 1.0):
        r = kin.ik([200.0, y, -10.0], 0.0, q0_deg=q, max_seeds=1, max_iter=15 if prev is not None else 60)
        assert r.ok, f"y={y}"
        if prev is not None:
            assert np.max(np.abs(r.q_deg - prev)) < 4.0, f"nhảy nghiệm tại y={y}"
        q = prev = r.q_deg


def test_ik_branch_fallback_when_warm_start_stuck(kin):
    """Yaw 30° cho hai nghiệm roll cách nhau 180°; khởi động nóng ở nhánh xa có thể kẹt nhưng IK nhiều hạt giống phải tìm được nghiệm."""
    r = kin.ik([200.0, 32.0, -10.0], 30.0, max_seeds=4, max_iter=60)
    assert r.ok and kin.within_margin(r.q_deg, 3.0)


def test_pan_axis_position(kin):
    p = kin.pan_axis_xy_mm()
    assert abs(p[0] - 38.8) < 1.5 and abs(p[1]) < 1.0


def test_within_margin_flags_limits(kin):
    lo, hi = kin.limits_deg
    q = (lo + hi) / 2
    assert kin.within_margin(q, 3.0)
    q2 = q.copy()
    q2[1] = lo[1] + 1.0
    assert not kin.within_margin(q2, 3.0)


def test_tcp_offset_moves_tcp(kin):
    from cl0.kinematics import SO101Kinematics
    k2 = SO101Kinematics(tcp_offset_mm=(0.0, 0.0, 10.0), margin_deg=3.0)
    q = np.array([0.0, -49.0, 48.0, 91.0, 0.0])
    p0, _ = kin.fk(q)
    p1, _ = k2.fk(q)
    assert abs(np.linalg.norm(p1 - p0) - 10.0) < 1e-6
