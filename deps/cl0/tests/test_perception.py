import dataclasses
import math

import numpy as np
import pytest

from cl0.config import Config
from cl0.geometry import wrap_axis_diff
from cl0.perception import Detector, PerceptionParams
from cl0.sim.harness import SimSetup, build_system
from cl0.sim.scene import Placed


def _place(sys_, name, a_b, b, th=0.0):
    return Placed(sys_.lib[name], sys_.ca + a_b, sys_.cb + b, th)


def _detect(sys_, objs, s=0.0, exclude=(), gain=None, det=None):
    img = sys_.renderer.render(s, objs, sys_.marks_home, gain=gain)          # cánh tay ở nhà có trong cảnh như trong nền
    return (det or sys_.detector).detect(img, s, exclude)


@pytest.mark.parametrize("th", [0.0, 30.0, 75.0, 120.0, 170.0])
@pytest.mark.parametrize("s", [0.0, 137.0])
def test_bar_pose_width_and_closing_axis(sim_sys, th, s):
    """Thanh 18×60: tâm sai ≲ 2 mm, bề ngang ≈ 18, trục khép ⟂ trục dài (th + 90)."""
    po = _place(sim_sys, "bar18x60", -20.0, 10.0, th)
    res = _detect(sim_sys, [po], s)
    ok = [d for d in res.dets if d.ok]
    assert len(ok) == 1, [(d.reject, d.a_mm, d.b_mm) for d in res.dets]
    d = ok[0]
    ca, cb = po.a_b + s, po.b
    # điểm kẹp nằm trên 'cao nguyên' DT dọc trục dài của thanh nên sai khác DỌC trục dài là hợp lệ (vài mm); sai ngang trục phải nhỏ
    t = math.radians(th)
    ex, ey = d.a_mm - ca, d.b_mm - cb
    along, across = ex * math.cos(t) + ey * math.sin(t), -ex * math.sin(t) + ey * math.cos(t)
    assert abs(across) < 1.5 and abs(along) < 4.0, (along, across)
    assert 17.0 < d.width_mm < 21.5            # bề rộng đo được lớn hơn thật ~2–3 mm (nhoè ảnh + ngưỡng thấp); đã tính trong width_margin_mm
    assert abs(wrap_axis_diff(d.theta_deg - (th + 90.0))) < 4.0


def test_disc_is_isotropic_and_centered(sim_sys):
    po = _place(sim_sys, "disc30", 15.0, -12.0, 0.0)
    d = [x for x in _detect(sim_sys, [po]).dets if x.ok][0]
    assert math.hypot(d.a_mm - (po.a_b), d.b_mm - po.b) < 1.5
    assert 29.0 < d.width_mm < 33.5
    assert abs(wrap_axis_diff(d.theta_deg - sim_sys.cfg.perception.grasp.isotropic_theta_deg)) < 1e-6      # vật đẳng hướng: góc mặc định


def test_object_wider_than_gripper_is_rejected_wide(sim_sys):
    res = _detect(sim_sys, [_place(sim_sys, "box60x60", 0.0, 0.0, 20.0)])
    assert len(res.dets) == 1 and res.dets[0].reject == "wide"


def test_ring_grasp_point_is_on_the_body_not_the_hole(sim_sys):
    po = _place(sim_sys, "ring34", 0.0, 0.0, 0.0)
    ok = [d for d in _detect(sim_sys, [po]).dets if d.ok]
    assert len(ok) == 1
    r = math.hypot(ok[0].a_mm - po.a_b, ok[0].b_mm - po.b)
    assert 8.0 < r < 15.0, f"điểm kẹp cách tâm {r:.1f} mm — phải nằm trên thân vòng (bán kính 11–17 mm), không ở lỗ"


def test_ring_closing_axis_is_radial_only_with_local_yaw(sim_sys):
    """Vật đẳng hướng (vòng): CL-0 gốc dùng góc khép cố định (có thể trúng tiếp tuyến); yaw_mode='local' (nút tinh chỉnh) khép theo bán kính."""
    po = _place(sim_sys, "ring34", 0.0, 0.0, 0.0)
    g = dataclasses.replace(sim_sys.cfg.perception.grasp, yaw_mode="local")
    det = Detector(sim_sys.rect, sim_sys.detector.bg, dataclasses.replace(sim_sys.cfg.perception, grasp=g))
    ok = [d for d in _detect(sim_sys, [po], det=det).dets if d.ok]
    assert len(ok) == 1
    d = ok[0]
    assert d.width_mm < 10.0                                     # bề dày thân vòng ~6 mm (+ nhoè)
    radial = math.degrees(math.atan2(d.b_mm - po.b, d.a_mm - po.a_b))
    assert abs(wrap_axis_diff(d.theta_deg - radial)) < 12.0


def test_empty_belt_has_no_false_positives(sim_sys):
    rng = np.random.default_rng(0)
    for s in rng.uniform(0, 800, 25):
        res = _detect(sim_sys, [], float(s))
        assert [d for d in res.dets if d.ok] == [], f"phát hiện giả ở s={s:.0f}: {[(d.a_mm, d.b_mm, d.area_mm2) for d in res.dets]}"


def test_global_exposure_change_is_compensated(sim_sys):
    po = _place(sim_sys, "disc30", 0.0, 0.0)
    for g in (0.85, 1.15):
        res = _detect(sim_sys, [po], gain=g)
        ok = [d for d in res.dets if d.ok]
        assert len(ok) == 1 and math.hypot(ok[0].a_mm - po.a_b, ok[0].b_mm - po.b) < 2.0, f"gain={g}"


def test_arm_exclusion_disc_suppresses_detection(sim_sys):
    po = _place(sim_sys, "disc30", 0.0, 0.0)
    res = _detect(sim_sys, [po], exclude=[(po.a_b, po.b, 55.0)])
    assert [d for d in res.dets if d.ok] == []


def test_two_touching_discs_split_only_with_watershed(sim_sys):
    p1, p2 = _place(sim_sys, "disc30", -15.0, 0.0), _place(sim_sys, "disc30", 15.5, 0.0)
    plain = [d for d in _detect(sim_sys, [p1, p2]).dets if d.ok]
    prm = dataclasses.replace(sim_sys.cfg.perception, split="watershed")
    det_ws = Detector(sim_sys.rect, sim_sys.detector.bg, prm)
    ws = [d for d in _detect(sim_sys, [p1, p2], det=det_ws).dets if d.ok]
    assert len(plain) == 1                                   # CL-0 gốc: một khối
    assert len(ws) == 2
    got = sorted((d.a_mm for d in ws))
    assert abs(got[0] - p1.a_b) < 5.0 and abs(got[1] - p2.a_b) < 5.0


def test_textured_belt_is_compensated_by_shift_with_counter():
    cfg = Config()
    cfg.belt.textured, cfg.belt.period_mm = True, 1200.0
    S = build_system(SimSetup(textured=True, texture_period_mm=1200.0, seed=2), cfg)
    rng = np.random.default_rng(1)
    for s in (0.0, 333.0, 987.0):
        a_world = float(rng.uniform(-50, 50))
        po = Placed(S.lib["disc30"], S.ca + a_world - s, S.cb + 5.0, 0.0)       # nằm trong cửa sổ tại thời điểm s
        img = S.renderer.render(s, [po], S.marks_home)
        ok = [d for d in S.detector.detect(img, s).dets if d.ok]
        assert len(ok) == 1 and math.hypot(ok[0].a_mm - (S.ca + a_world), ok[0].b_mm - po.b) < 2.5, f"s={s}: {[(d.a_mm, d.b_mm) for d in ok]}"
        assert [d for d in S.detector.detect(S.renderer.render(s, [], S.marks_home), s).dets if d.ok] == [], f"phát hiện giả ở s={s}"


def test_background_save_load_roundtrip(sim_sys, tmp_path):
    from cl0.perception import BackgroundModel, window_of
    import copy
    bg = copy.copy(sim_sys.detector.bg)                       # bản sao nông: không sửa nền dùng chung của cả phiên test
    bg.meta = dict(calib_sha="abc", n_frames=12)
    p = tmp_path / "bg.npz"
    bg.save(str(p))
    b2 = BackgroundModel.load(str(p))
    assert b2.rows == bg.rows and b2.cols == bg.cols and b2.res == bg.res and b2.a_min == bg.a_min and b2.b_min == bg.b_min
    assert b2.meta.get("calib_sha") == "abc"
    assert np.allclose(b2.mean, bg.mean)
    w = window_of(b2)
    assert abs(w.a_min - bg.a_min) < 1e-9 and abs(w.b_min - bg.b_min) < 1e-9
