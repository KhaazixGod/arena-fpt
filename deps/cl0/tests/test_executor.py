"""Bộ thực thi bám băng (BeltExecutor) chạy trên thế giới mô phỏng động học có trễ servo (không cần ảnh)."""
import dataclasses
import math

import numpy as np
import pytest

from cl0.config import Config
from cl0.executor import BeltExecutor
from cl0.geometry import perp, unit
from cl0.sim.world import SimWorld, WorldParams
from cl0.types import Command

PHI, ZB = 90.0, -40.0


def _drive(kin, cfg, v=40.0, T=5.0, tgt=(-130.0, -170.0), z_ref=-30.0, th=0.0, lag=None):
    """Chạy executor 50 Hz trên SimWorld; trả (sai lệch đo được trong hệ băng theo thời gian, executor, world)."""
    w = SimWorld(PHI, ZB, None, [], kin, cfg.robot.home_q_deg, cfg.robot.gripper_open, lag or WorldParams(), accel=cfg.belt.accel_mm_s2)
    u, vv = unit(PHI), perp(PHI)
    exe = BeltExecutor(cfg, kin, PHI, ZB)
    exe.reset(np.asarray(cfg.robot.home_q_deg, float))
    w.start_belt(v)
    t, dt = 0.0, 0.02
    errs, started = [], False
    while t < T:
        for _ in range(4):
            w.step(t, 0.005)
            t += 0.005
        st = w.robot_state(t)
        p, _, _, _, yaw = kin.tool_axes(st.q_deg)
        tcp = dict(x=float(p[0]), y=float(p[1]), z=float(p[2]), a=float(p @ np.r_[u, 0.0]), b=float(p @ np.r_[vv, 0.0]), theta=float(yaw - PHI))
        s_now, sdot = w.s_at(t), w.speed_at(t)
        if not started:
            exe.start(tcp, s_now, sdot)
            started = True
        q, err, _ = exe.step(t, dt, s_now, sdot, tcp, np.asarray(tgt, float), th, z_ref)
        w.send(t, Command(q, cfg.robot.gripper_open, "T"))
        errs.append((t, err, tcp["z"] - z_ref))
    return np.asarray(errs), exe, w


def _cfg(**kw):
    cfg = Config()
    for k, val in kw.items():
        setattr(cfg.executor, k, val)
    return cfg


def test_tracking_error_without_compensation_is_about_v_times_lag(kin):
    errs, _, _ = _drive(kin, _cfg(lead_s=0.0, lag_ki=0.0))
    assert 2.5 < errs[-50:, 1].mean() < 9.0                # ≈ v·(τ + trễ lệnh) = 40·0.12 ≈ 5 mm


def test_lead_compensates_servo_lag(kin):
    errs, _, _ = _drive(kin, _cfg(lead_s=0.12, lag_ki=0.0))
    assert errs[-50:, 1].max() < 1.8


def test_integral_compensation_removes_residual_lag_without_lead(kin):
    errs, exe, _ = _drive(kin, _cfg(lead_s=0.0, lag_ki=2.5), T=7.0)
    assert errs[-50:, 1].max() < 1.8
    assert abs(errs[-50:, 2]).max() < 2.0                  # z cũng bám (bù võng trọng lực)
    assert np.linalg.norm(exe.int_xy) < cfg_int_max(exe)


def cfg_int_max(exe):
    return exe.cfg.executor.lag_int_max_mm + 1e-6


@pytest.mark.parametrize("v", [20.0, 60.0])
def test_tracking_at_other_belt_speeds(kin, v):
    errs, _, _ = _drive(kin, _cfg(lead_s=0.12, lag_ki=2.5), v=v, T=6.0, tgt=(-150.0 if v > 40 else -80.0, -170.0))
    assert errs[-50:, 1].max() < 2.0


def test_joint_rate_limit_on_target_jump(kin):
    cfg = _cfg()
    exe = BeltExecutor(cfg, kin, PHI, ZB)
    q0 = np.asarray(cfg.robot.home_q_deg, float)
    exe.reset(q0)
    p, _, _, _, yaw = kin.tool_axes(q0)
    u, vv = unit(PHI), perp(PHI)
    tcp = dict(x=p[0], y=p[1], z=p[2], a=float(p[:2] @ u), b=float(p[:2] @ vv), theta=float(yaw - PHI))
    exe.start(tcp, 0.0, 0.0)
    qs = [q0]
    for k in range(40):
        q, _, _ = exe.step(0.02 * k, 0.02, 0.0, 0.0, tcp, np.array([60.0, -230.0]), 60.0, -30.0)
        qs.append(q)
    dq = np.abs(np.diff(np.asarray(qs), axis=0)).max()
    assert dq <= cfg.robot.q_dot_max_deg_s * 0.02 + 1e-6


def test_unreachable_target_holds_last_command_and_counts_failure_time(kin):
    cfg = _cfg()
    exe = BeltExecutor(cfg, kin, PHI, ZB)
    q0 = np.asarray(cfg.robot.home_q_deg, float)
    exe.reset(q0)
    p, _, _, _, yaw = kin.tool_axes(q0)
    u, vv = unit(PHI), perp(PHI)
    tcp = dict(x=p[0], y=p[1], z=p[2], a=float(p[:2] @ u), b=float(p[:2] @ vv), theta=float(yaw - PHI))
    exe.start(tcp, 0.0, 0.0)
    qs = []
    for k in range(150):
        q, _, _ = exe.step(0.02 * k, 0.02, 0.0, 0.0, tcp, np.array([0.0, -900.0]), 0.0, -30.0)     # x = 900 mm: ngoài tầm
        qs.append(q)
    assert exe.ik_fail_t > 0.5
    lo, hi = kin.limits_deg
    assert np.all(q >= lo - 1e-6) and np.all(q <= hi + 1e-6)
    assert np.allclose(qs[-1], qs[-10], atol=1e-9)                       # khi IK hỏng thì giữ nguyên lệnh cuối, không văng ra giá trị rác


def test_command_height_never_below_belt_clearance(kin):
    cfg = _cfg()
    exe = BeltExecutor(cfg, kin, PHI, ZB)
    q0 = np.asarray(cfg.robot.home_q_deg, float)
    exe.reset(q0)
    p, _, _, _, yaw = kin.tool_axes(q0)
    u, vv = unit(PHI), perp(PHI)
    tcp = dict(x=p[0], y=p[1], z=p[2], a=float(p[:2] @ u), b=float(p[:2] @ vv), theta=float(yaw - PHI))
    exe.start(tcp, 0.0, 0.0)
    for k in range(300):
        q, _, _ = exe.step(0.02 * k, 0.02, 0.0, 0.0, tcp, np.array([-100.0, -180.0]), 0.0, ZB - 50.0)     # đòi thấp hơn mặt băng 50 mm
    pz = kin.tool_axes(q)[0][2]
    assert pz >= ZB + cfg.executor.min_z_above_belt_mm - 1.0
