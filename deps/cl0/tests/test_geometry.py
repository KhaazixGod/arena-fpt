import math

import numpy as np
import pytest

from cl0 import calib_tools as ct
from cl0.geometry import (PlaneCalib, Rectifier, Window, auto_window, calib_from_board, fit_belt_motion, fit_plane_homography,
                          fit_rigid_2d, perp, to_belt_frame, to_world_frame, unit, wrap180, wrap_axis_diff)
from cl0.sim.scene import SceneRenderer, SimCameraCfg, look_at_homography


def _H_wp(flip=False, z=-40.0):
    return look_at_homography((200.0, 0.0, z + 450.0), (200.0, 0.0, z), 520.0, (640, 480), z_plane=z, flip=flip)


def _px(H, xy):
    p = np.c_[xy, np.ones(len(xy))] @ H.T
    return p[:, :2] / p[:, 2:3]


@pytest.mark.parametrize("flip", [False, True])
def test_fit_plane_homography_recovers_map(flip):
    rng = np.random.default_rng(0)
    H = _H_wp(flip)
    P = np.c_[rng.uniform(120, 280, 24), rng.uniform(-150, 150, 24)]
    px = _px(H, P) + rng.normal(0, 0.3, (24, 2))
    cal = fit_plane_homography(px, P, z_plane_mm=-40.0)
    Q = np.c_[rng.uniform(130, 270, 300), rng.uniform(-140, 140, 300)]
    err = np.linalg.norm(cal.pix_to_world(_px(H, Q)) - Q, axis=1)
    assert err.mean() < 0.4 and err.max() < 1.5
    back = cal.world_to_pix(Q)
    assert np.abs(back - _px(H, Q)).max() < 1.0


def test_frames_roundtrip_and_conventions():
    assert np.allclose(unit(90.0), [0, 1], atol=1e-12)
    assert np.allclose(perp(90.0), [-1, 0], atol=1e-12)            # v̂ = bên TRÁI chiều băng chạy
    p = np.array([-20.0, 150.0])
    pb = to_belt_frame(p, 100.0, 90.0)
    assert np.allclose(pb, [-20.0, 50.0])
    assert np.allclose(to_world_frame(pb, 100.0, 90.0), p)
    assert wrap180(190.0) == pytest.approx(10.0)                      # gói về [0, 180)
    assert wrap_axis_diff(100.0) == pytest.approx(-80.0)
    assert wrap_axis_diff(-100.0) == pytest.approx(80.0)
    assert wrap_axis_diff(180.0) == pytest.approx(0.0)


@pytest.mark.parametrize("phi", [0.0, 37.0, 90.0, 179.0, -120.0, -179.9])
def test_fit_belt_motion_direction_and_scale(phi):
    rng = np.random.default_rng(1)
    u, v = unit(phi), perp(phi)
    tracks = []
    for k in range(3):
        steps = np.linspace(0, 6000, 25) + 400 * k
        xy = np.array([(30.0 + 0.05 * s) * u + (10.0 * k - 12.0) * v for s in steps]) + rng.normal(0, 0.2, (25, 2))
        tracks.append((steps, xy))
    ph, m, lat = fit_belt_motion(tracks)
    assert abs((ph - phi + 180.0) % 360.0 - 180.0) < 0.4
    assert m == pytest.approx(0.05, rel=0.01)
    assert lat < 0.5


def test_rigid_fit_with_reflection():
    rng = np.random.default_rng(2)
    src = rng.uniform(-50, 50, (9, 2))
    F = np.diag([1.0, -1.0])
    th = math.radians(23.0)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    dst = (R @ F @ src.T).T + np.array([120.0, -30.0])
    f1 = fit_rigid_2d(src, dst, allow_reflection=True)
    assert f1.reflected and f1.rms < 1e-9
    f0 = fit_rigid_2d(src, dst, allow_reflection=False)
    assert f0.rms > 5.0                                       # không cho phản xạ thì không khớp được
    dst2 = (R @ src.T).T + np.array([5.0, 6.0])
    f2 = fit_rigid_2d(src, dst2, allow_reflection=True)
    assert (not f2.reflected) and f2.rms < 1e-9


def test_rigid_fit_needs_three_points():
    with pytest.raises(ValueError):
        fit_rigid_2d(np.zeros((2, 2)), np.zeros((2, 2)))


def _exact_calib(H_wp, phi, z=-40.0):
    return PlaneCalib(H=np.linalg.inv(H_wp).tolist(), z_plane_mm=z, belt_dir_deg=phi, image_size=(640, 480))


@pytest.mark.parametrize("flip,phi", [(False, 90.0), (True, 90.0), (False, 20.0)])
def test_rectifier_maps_pixels_back_to_world(flip, phi):
    H = _H_wp(flip)
    cal = _exact_calib(H, phi)
    xy = np.array([180.0, 20.0])                                       # vật đặt tại W (x, y) = (180, 20)
    a_t, b_t = float(xy @ unit(phi)), float(xy @ perp(phi))
    win = Window(a_t - 100, a_t + 100, b_t - 80, b_t + 80, 0.5)
    rect = Rectifier(cal, win)
    rng = np.random.default_rng(3)
    for _ in range(20):
        a, b = rng.uniform(a_t - 90, a_t + 90), rng.uniform(b_t - 70, b_t + 70)
        col, row = rect.px_from_ab(a, b)
        a2, b2 = rect.ab_from_px(col, row)
        assert (a2, b2) == pytest.approx((a, b), abs=1e-9)
        assert rect.world_to_ab(rect.ab_to_world(a, b)) == pytest.approx((a, b), abs=1e-9)
    # ảnh rectified của một đĩa sáng nằm đúng vị trí
    from cl0.sim.scene import Placed, default_library
    ren = SceneRenderer(H, phi, SimCameraCfg(noise_sigma=0.0, blur_px=0.0, vignette=0.0))
    img = ren.render(0.0, [Placed(default_library()["disc30"], a_t, b_t, 0.0)])
    P = rect.rectify(img)
    m = (np.abs(P.astype(int) - np.array([46, 43, 41])).max(axis=2) > 40)
    ys, xs = np.nonzero(m)
    assert len(xs) > 500
    a_m, b_m = rect.ab_from_px(xs.mean(), ys.mean())
    assert abs(a_m - a_t) < 0.8 and abs(b_m - b_t) < 0.8


@pytest.mark.parametrize("flip", [False, True])
def test_board_calibration_with_noisy_touches(flip):
    """Bàn cờ vẽ trong thế giới ảo -> phát hiện góc -> chạm điểm (có nhiễu 1 mm) -> hiệu chuẩn; sai số trong vùng chạm ≲ 2 mm."""
    H = _H_wp(flip)
    cfg = SimCameraCfg(noise_sigma=1.5, blur_px=0.8)
    ren = SceneRenderer(H, 90.0, cfg, seed=3)
    cols, rows, sq = 7, 4, 15.0
    a0, b0, th = -60.0, -230.0, 12.0
    img = ren.render(0.0, [], [("checker", a0, b0, th, cols + 1, rows + 1, sq)])
    c = ct.detect_board(img, cols, rows)
    assert c is not None and len(c) == cols * rows
    bxy = ct.board_object_points(cols, rows, sq)
    # vị trí thật của góc k trong W: dò từ pixel bằng homography thật
    Hi = np.linalg.inv(H)
    pw = np.c_[c, np.ones(len(c))] @ Hi.T
    pw = pw[:, :2] / pw[:, 2:3]
    touch = ct.default_touch_indices(cols, rows)
    assert len(touch) == 9 and len(set(touch)) == 9
    rng = np.random.default_rng(4)
    tw = pw[touch] + rng.normal(0, 1.0, (len(touch), 2))
    cal = calib_from_board(c, bxy, bxy[touch], tw, -40.0, image_size=(640, 480))
    assert cal.method == "board" and cal.n_touch == 9
    A = np.c_[rng.uniform(150, 250, 200), rng.uniform(-60, 60, 200)]       # vùng gần bàn cờ (W)
    err = np.linalg.norm(cal.pix_to_world(_px(H, A)) - A, axis=1)
    assert err.mean() < 2.0 and err.max() < 4.0


def test_auto_window_inside_image_and_ranges():
    H = _H_wp()
    cal = _exact_calib(H, 90.0)
    w = auto_window(cal, 0.5, 10.0)
    assert w.a_max > w.a_min and w.b_max > w.b_min
    w2 = auto_window(cal, 0.5, 10.0, a_range=(-50.0, 60.0), b_range=(-260.0, -140.0))
    assert w2.a_min >= -50.0 - 1e-9 and w2.a_max <= 60.0 + 1e-9 and w2.b_min >= -260.0 - 1e-9 and w2.b_max <= -140.0 + 1e-9
    with pytest.raises(ValueError):
        auto_window(cal, 0.5, 10.0, a_range=(1e5, 2e5))


def test_plane_calib_json_roundtrip(tmp_path):
    cal = _exact_calib(_H_wp(), 33.0)
    cal.latency_s, cal.mm_per_step, cal.method = 0.123, 0.0456, "board"
    p = tmp_path / "calib.json"
    cal.save(str(p))
    c2 = PlaneCalib.load(str(p))
    assert c2.belt_dir_deg == 33.0 and c2.latency_s == 0.123 and c2.mm_per_step == 0.0456 and c2.method == "board"
    assert np.allclose(c2.H_np(), cal.H_np())
