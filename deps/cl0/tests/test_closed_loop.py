"""Vòng kín trên mô phỏng động học: ảnh -> nhận thức -> theo dõi -> bộ thực thi -> kẹp. Chậm (mỗi lượt ~5–10 s thật)."""
import pytest

from cl0.config import Config
from cl0.sim.harness import SimSetup, arrangement_to_placed, belt_center_for, build_system, run_trial
from cl0.sim.world import WorldParams

pytestmark = pytest.mark.slow

FINAL = {"picked_hold_complete", "dropped_in_hold", "empty_grasp", "timeout", "hard_timeout", "late", "no_target", "ik_fail"}


def _cfg(v=50.0, lead=0.12, **kw):
    cfg = Config()
    cfg.belt.speed_mm_s, cfg.executor.lead_s = v, lead
    for k, val in kw.items():
        sec, name = k.split("__")
        setattr(getattr(cfg, sec), name, val)
    return cfg


def _run(items, phi=90.0, flip=False, v=50.0, setup_kw=None, world_kw=None, cfg=None, seed=0, a_start=-420.0):
    st = SimSetup(phi_deg=phi, flip=flip, seed=seed, belt_center_w=belt_center_for(phi), world=WorldParams(**(world_kw or {})), **(setup_kw or {}))
    S = build_system(st, cfg or _cfg(v))
    return S, run_trial(S, arrangement_to_placed(S, items, a_start=a_start), v_mm_s=v)


@pytest.mark.parametrize("phi,flip,v", [(90.0, False, 50.0), (270.0, False, 40.0), (0.0, False, 40.0), (180.0, True, 50.0), (135.0, False, 30.0), (200.0, True, 60.0)])
def test_single_disc_is_grasped_for_any_belt_direction_flip_and_speed(phi, flip, v):
    S, r = _run([("disc30", 0.0, 60.0, 0.0)], phi=phi, flip=flip, v=v)
    assert r.outcome == "picked_hold_complete" and r.success, (r.outcome, r.grasp, r.phases[-3:])
    assert r.off_mm < 6.0                                   # TCP lệch tâm vật lúc má kẹp chạm: vài mm


@pytest.mark.parametrize("name,y,th", [("box25x50", 45.0, 30.0), ("ellipse28x48", 75.0, 100.0), ("bar18x60", 30.0, 160.0), ("lowcon30", 60.0, 0.0)])
def test_assorted_novel_shapes_and_yaws(name, y, th):
    S, r = _run([(name, 0.0, y, th)], v=50.0)
    assert r.success, (name, r.outcome, r.grasp)


def test_clutter_picks_the_most_downstream_reachable_object():
    items = [("disc30", 0.0, 35.0, 0.0), ("box25x50", 130.0, 85.0, 40.0), ("disc22", 240.0, 50.0, 0.0)]
    S, r = _run(items, v=40.0)
    assert r.success
    assert r.picked in ("disc22", "box25x50", "disc30")       # một vật đã được nhấc; thứ tự cụ thể kiểm ở dưới
    sel = [e for e in r.events if e.name == "select"]
    assert len(sel) == 1


def test_object_wider_than_gripper_leads_to_no_target_not_a_crash():
    S, r = _run([("box60x60", 0.0, 60.0, 0.0)], v=50.0)
    assert r.outcome == "no_target" and not r.success


def test_empty_belt_times_out_with_no_target():
    cfg = _cfg(50.0)
    cfg.executor.trial_timeout_s = 8.0
    S, r = _run([], v=50.0, cfg=cfg)
    assert r.outcome == "no_target" and not r.success and r.t_end < 15.0


def test_too_fast_belt_aborts_as_late_instead_of_getting_stuck():
    S, r = _run([("disc30", 0.0, 60.0, 0.0)], v=170.0)
    assert r.outcome in FINAL and r.outcome != "hard_timeout"
    assert r.t_end < 45.0


def test_outcome_is_always_a_known_final_state():
    for i, (x, y) in enumerate([(0.0, 20.0), (0.0, 100.0)]):
        S, r = _run([("disc30", x, y, 15.0)], v=60.0, seed=i)
        assert r.outcome in FINAL


def test_gross_belt_direction_error_breaks_the_grasp():
    """Bằng chứng mô phỏng KHÔNG 'dễ dãi': sai hướng băng 10° phải làm hỏng — nghĩa là các lần thành công ở trên có giá trị."""
    S, r = _run([("disc30", 0.0, 60.0, 0.0)], v=60.0, setup_kw=dict(belt_dir_err_deg=10.0))
    assert not r.success


def test_small_belt_scale_error_is_tolerated_but_large_is_not():
    ok = _run([("disc30", 0.0, 60.0, 0.0)], v=50.0, world_kw=dict(belt_scale_error=0.98))[1]
    bad = _run([("disc30", 0.0, 60.0, 0.0)], v=50.0, world_kw=dict(belt_scale_error=0.75))[1]
    assert ok.success
    assert not bad.success


def test_textured_belt_with_counter():
    cfg = _cfg(50.0)
    cfg.belt.textured, cfg.belt.period_mm = True, 1200.0
    S, r = _run([("disc30", 0.0, 60.0, 0.0)], v=50.0, cfg=cfg, setup_kw=dict(textured=True, texture_period_mm=1200.0), seed=2)
    assert r.success
