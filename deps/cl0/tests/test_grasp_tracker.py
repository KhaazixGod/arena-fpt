import math

import cv2
import numpy as np
import pytest

from cl0.config import TrackCfg
from cl0.geometry import wrap_axis_diff
from cl0.grasp import GraspParams, analyze_component, chord_width_px, watershed_split
from cl0.perception import Detection
from cl0.tracker import Tracker, circ_mean_axis_deg

RES = 0.5


def _canvas(h=240, w=320):
    return np.zeros((h, w), np.uint8)


def _disc(m, cx, cy, d):
    cv2.circle(m, (int(cx / RES), int(cy / RES)), int(d / 2 / RES), 255, -1)
    return m


def _bar(m, cx, cy, L, W, ang_deg):
    box = cv2.boxPoints(((cx / RES, cy / RES), (L / RES, W / RES), ang_deg))
    cv2.fillPoly(m, [np.round(box).astype(np.int32)], 255)
    return m


def test_disc_grasp_point_center_and_width():
    m = _disc(_canvas(), 80, 60, 30)
    c = analyze_component(m, RES, GraspParams())
    assert c is not None and c.reject == "" and c.isotropic
    assert abs(c.width_mm - 30) < 1.5
    assert math.hypot(c.col * RES - 80, c.row * RES - 60) < 1.0


@pytest.mark.parametrize("ang", [0, 25, 90, 140])
def test_bar_closing_axis_is_perpendicular_to_long_axis(ang):
    m = _bar(_canvas(), 80, 60, 60, 18, ang)
    c = analyze_component(m, RES, GraspParams())
    assert c is not None and c.reject == ""
    assert abs(c.width_mm - 18) < 1.5
    assert abs(wrap_axis_diff(c.theta_deg - (ang + 90))) < 3.0


def test_wide_object_rejected_and_thin_rejected():
    c = analyze_component(_disc(_canvas(), 80, 60, 50), RES, GraspParams())
    assert c is not None and c.reject == "wide"
    c2 = analyze_component(_bar(_canvas(), 80, 60, 60, 1.0, 10), RES, GraspParams())
    assert c2 is None or c2.reject != ""


def test_ring_uses_body_not_hole():
    m = _canvas()
    _disc(m, 80, 60, 34)
    cv2.circle(m, (int(80 / RES), int(60 / RES)), int(11 / RES), 0, -1)
    c = analyze_component(m, RES, GraspParams())
    assert c is not None
    r = math.hypot(c.col * RES - 80, c.row * RES - 60)
    assert 11 < r < 17


def test_chord_width_through_disc():
    m = _disc(_canvas(), 80, 60, 30)
    w = chord_width_px(m, 80 / RES, 60 / RES, 0.3) * RES
    assert abs(w - 30) < 1.0


def test_watershed_splits_touching_discs():
    m = _canvas()
    _disc(m, 70, 60, 30)
    _disc(m, 100.5, 60, 30)
    parts = watershed_split(m)
    assert len(parts) == 2
    assert watershed_split(_disc(_canvas(), 80, 60, 30)).__len__() == 1


def test_circular_mean_of_axes_handles_wraparound():
    assert abs(wrap_axis_diff(circ_mean_axis_deg([179.0, 1.0]) - 0.0)) < 1e-6
    assert abs(circ_mean_axis_deg([85.0, 95.0]) - 90.0) < 1e-6


def _det(a, b, th=40.0, w=25.0, ok=True):
    return Detection(a_mm=a, b_mm=b, theta_deg=th, width_mm=w, area_mm2=800.0, dt_r_mm=12.0, aspect=1.0, centroid_ab=(a, b),
                     reject="" if ok else "wide")


def test_tracker_confirms_after_n_obs_and_uses_belt_frame():
    tr = Tracker(TrackCfg(n_confirm=3, window=6, gate_mm=12.0, max_std_mm=5.0, lost_s=1.5))
    rng = np.random.default_rng(0)
    v = 50.0
    for k in range(6):
        t = 0.1 * k
        s = v * t
        a_w = -100.0 + s + rng.normal(0, 0.4)           # vật đứng yên trong hệ băng: a_w tăng theo s
        tr.update([_det(a_w, 20.0 + rng.normal(0, 0.4))], s, t)
        if k < 2:
            assert tr.confirmed() == []
    c = tr.confirmed()
    assert len(c) == 1
    a_b, b, th, w, std = c[0].estimate()
    assert abs(a_b + 100.0) < 0.6 and abs(b - 20.0) < 0.6 and abs(th - 40.0) < 1e-6 and std < 1.5


def test_tracker_separates_objects_and_ignores_rejected_dets():
    tr = Tracker(TrackCfg())
    for k in range(5):
        tr.update([_det(-100.0, 0.0), _det(-20.0, 40.0), _det(60.0, -30.0, ok=False)], 0.0, 0.1 * k)
    assert len(tr.confirmed()) == 2


def test_tracker_prunes_lost_tracks_but_keeps_target():
    tr = Tracker(TrackCfg(lost_s=1.5))
    for k in range(4):
        tr.update([_det(-100.0, 0.0), _det(0.0, 30.0)], 0.0, 0.1 * k)
    tids = [t.tid for t in tr.tracks]
    tr.prune(t_now=5.0, keep=tids[0])
    assert [t.tid for t in tr.tracks] == [tids[0]]
    tr.prune(t_now=10.0)
    assert tr.tracks == []


def test_tracker_unstable_object_not_confirmed():
    tr = Tracker(TrackCfg(max_std_mm=5.0, gate_mm=30.0))
    for k, a in enumerate([-100, -90, -80, -70, -60]):
        tr.update([_det(float(a), 0.0)], 0.0, 0.1 * k)       # vật trượt trong hệ băng => độ lệch chuẩn lớn
    assert tr.confirmed() == []
