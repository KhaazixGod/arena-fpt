"""Logic CHỌN vật của CL-0 (nhanh, không chạy mô phỏng đầy đủ): vùng với tới, dẫn trước, cửa sổ nhặt, luật 'hạ lưu nhất'."""
import copy

import numpy as np
import pytest

from cl0.config import Config
from cl0.controller import CL0Controller
from cl0.perception import Detection


@pytest.fixture()
def ctl_factory(sim_sys):
    def make(**exec_kw):
        cfg = copy.deepcopy(sim_sys.cfg)
        for k, v in exec_kw.items():
            setattr(cfg.executor, k, v)
        st = sim_sys.setup
        return CL0Controller(cfg, sim_sys.kin, sim_sys.detector, sim_sys.reach, st.phi_deg, st.z_belt)
    return make


def _interval(ctl, b, step=2.0):
    """[a_lo, a_hi] mà tại đó điểm (a, b) với tới được ở MỌI độ cao dùng trong một lượt (kẹp/chờ/nhấc), biên trong 5 mm."""
    zg, zp, zl = ctl._zs()
    ok = []
    for a in np.arange(-500.0, 500.0, step):
        xy = a * ctl.u + b * ctl.v
        if all(ctl.reach.contains(float(xy[0]), float(xy[1]), z, inner_mm=5.0) for z in (zg, zp, zl)):
            ok.append(float(a))
    assert ok, "không có điểm nào với tới được: sai hình học thử nghiệm"
    assert np.all(np.diff(ok) <= step + 1e-9), "vùng với tới theo a không liền khối"
    return ok[0], ok[-1]


def test_reach_interval_is_wide_enough_for_the_tests(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    assert hi - lo > 250.0


def test_object_still_outside_reach_is_not_picked_even_if_it_will_enter(ctl_factory, sim_sys):
    """Hồi quy lỗi mô phỏng bắt được: chọn vật chỉ vào vùng ở lúc kẹp làm tay đuổi theo vị trí HIỆN TẠI ngoài tầm -> ik_fail."""
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    v = 50.0
    assert v * ctl.cfg.executor.t_to_grasp_s > 30.0                       # lúc kẹp thì đã nằm trong vùng
    assert ctl._pick_a_grasp(lo - 15.0, sim_sys.cb, 0.0, v) is None       # nhưng bây giờ còn ở ngoài (thượng nguồn)
    a_in = ctl._pick_a_grasp(lo + 10.0, sim_sys.cb, 0.0, v)                # vừa vào vùng: chọn được
    assert a_in is not None and abs(a_in - (lo + 10.0 + v * ctl.cfg.executor.t_to_grasp_s)) < 1e-6


def test_object_that_will_leave_reach_before_lift_is_not_picked(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    v, ex = 50.0, ctl.cfg.executor
    need = v * (ex.t_to_grasp_s + ex.follow_margin_s + ex.lead_s)
    assert ctl._pick_a_grasp(hi - need - 15.0, sim_sys.cb, 0.0, v) is not None
    assert ctl._pick_a_grasp(hi - need + 15.0, sim_sys.cb, 0.0, v) is None


def test_lead_is_included_in_the_reach_check(ctl_factory, sim_sys):
    """Lệnh dẫn trước s(t + lead_s): vật sát biên hạ lưu mà lệnh dẫn trước đã vượt biên thì không được chọn."""
    lead = 0.5
    ctl = ctl_factory(lead_s=lead)
    ctl0 = ctl_factory(lead_s=0.0)
    lo, hi = _interval(ctl, sim_sys.cb)
    v, ex = 60.0, ctl.cfg.executor
    t_end = ex.t_to_grasp_s + ex.follow_margin_s
    a_edge = hi - v * t_end - 10.0                                        # vật còn 10 mm tới biên ở cuối lúc nhấc
    assert ctl0._pick_a_grasp(a_edge, sim_sys.cb, 0.0, v) is not None
    assert ctl._pick_a_grasp(a_edge, sim_sys.cb, 0.0, v) is None          # lead 0,5 s × 60 = 30 mm vượt biên


def test_pick_window_applies_only_at_grasp_and_lift(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    v, ex = 40.0, ctl.cfg.executor
    a_now = lo + 20.0
    a_grasp = a_now + v * ex.t_to_grasp_s
    ctl_w = ctl_factory(a_pick_min=a_grasp - 5.0, a_pick_max=a_grasp + v * ex.follow_margin_s + 5.0)
    assert ctl_w._pick_a_grasp(a_now, sim_sys.cb, 0.0, v) is not None     # a hiện tại < a_pick_min vẫn được (chỉ lúc kẹp phải trong cửa sổ)
    ctl_w2 = ctl_factory(a_pick_max=a_grasp - 5.0)
    assert ctl_w2._pick_a_grasp(a_now, sim_sys.cb, 0.0, v) is None


def test_s_now_is_added_to_the_belt_frame_position(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    v = 40.0
    a_b, s_now = lo + 20.0 - 300.0, 300.0                                 # a_b hệ băng + s = a thế giới
    r = ctl._pick_a_grasp(a_b, sim_sys.cb, s_now, v)
    assert r is not None and abs(r - (lo + 20.0 + v * ctl.cfg.executor.t_to_grasp_s)) < 1e-6


def _det(a, b, th=0.0, w=25.0):
    return Detection(a_mm=a, b_mm=b, theta_deg=th, width_mm=w, area_mm2=500.0, dt_r_mm=w / 2, aspect=1.0, centroid_ab=(a, b))


def test_select_chooses_the_most_downstream_feasible_track(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    v = 40.0
    ex = ctl.cfg.executor
    a_far = hi - v * (ex.t_to_grasp_s + ex.follow_margin_s) - 20.0       # hạ lưu nhất còn nhặt được
    cand = [lo + 10.0, 0.5 * (lo + a_far), a_far, hi + 80.0]              # vật cuối đã quá biên hạ lưu: bị loại
    for i in range(ctl.cfg.track.n_confirm):
        ctl.tracker.update([_det(a, sim_sys.cb + 5.0 * k) for k, a in enumerate(cand)], 0.0, 0.1 * i)
    assert len(ctl.tracker.confirmed()) == 4
    assert ctl._select(1.0, 0.0, v)
    sel = ctl.events[-1]
    assert sel.name == "select"
    assert abs(sel.data["a_b"] - a_far) < 1.0


def test_select_returns_false_when_nothing_is_feasible(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    for i in range(ctl.cfg.track.n_confirm):
        ctl.tracker.update([_det(lo - 60.0, sim_sys.cb), _det(hi + 60.0, sim_sys.cb)], 0.0, 0.1 * i)
    assert not ctl._select(1.0, 0.0, 40.0)
    assert ctl.target_tid is None


def test_unconfirmed_tracks_are_not_selected(ctl_factory, sim_sys):
    ctl = ctl_factory()
    lo, hi = _interval(ctl, sim_sys.cb)
    ctl.tracker.update([_det(lo + 40.0, sim_sys.cb)], 0.0, 0.0)           # mới thấy 1 lần
    assert ctl.tracker.confirmed() == []
    assert not ctl._select(0.1, 0.0, 40.0)
