"""Hàm thuần của các bước hiệu chuẩn (cl0/calib_tools.py): bàn cờ, điểm chạm, vạch đánh dấu, độ trễ ảnh↔băng, độ trễ tay."""
import math

import cv2
import numpy as np
import pytest

from cl0.calib_tools import (board_object_points, default_touch_indices, detect_board, estimate_arm_lag, estimate_latency, find_marker,
                             reject_touch_outliers)
from cl0.geometry import fit_rigid_2d


# --------------------------------------------------------------------------------------------------------------- bàn cờ
def _checker_img(cols=7, rows=4, sq=40, margin=60, angle_deg=0.0, size=(640, 480)):
    """Bàn cờ (cols+1)×(rows+1) ô => cols×rows góc trong. Trả (ảnh BGR, góc kỳ vọng (cols*rows, 2) theo thứ tự hàng trước)."""
    W, H = (cols + 1) * sq, (rows + 1) * sq
    board = np.full((H + 2 * margin, W + 2 * margin), 235, np.uint8)
    for j in range(rows + 1):
        for i in range(cols + 1):
            if (i + j) % 2 == 0:
                board[margin + j * sq: margin + (j + 1) * sq, margin + i * sq: margin + (i + 1) * sq] = 25
    # biên ô nằm GIỮA hai pixel: trong hệ toạ độ tâm-pixel của OpenCV là (k·sq − 0,5)
    exp = np.array([[margin + (i + 1) * sq - 0.5, margin + (j + 1) * sq - 0.5] for j in range(rows) for i in range(cols)], float)
    canvas = np.full((size[1], size[0]), 120, np.uint8)
    M = cv2.getRotationMatrix2D((board.shape[1] / 2, board.shape[0] / 2), angle_deg, 1.0)
    M[:, 2] += [(size[0] - board.shape[1]) / 2, (size[1] - board.shape[0]) / 2]
    warped = cv2.warpAffine(board, M, size, flags=cv2.INTER_LINEAR, borderValue=120)
    exp = exp @ M[:, :2].T + M[:, 2]
    return cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR), exp


def test_board_object_points_layout():
    P = board_object_points(7, 4, 15.0)
    assert P.shape == (28, 2)
    assert np.allclose(P[0], [0, 0]) and np.allclose(P[6], [90, 0]) and np.allclose(P[7], [0, 15]) and np.allclose(P[27], [90, 45])


@pytest.mark.parametrize("angle", [0.0, 12.0, -20.0])
def test_detect_board_finds_corners_in_row_major_order(angle):
    img, exp = _checker_img(angle_deg=angle)
    c = detect_board(img, 7, 4)
    assert c is not None and c.shape == (28, 2)
    # thứ tự có thể bắt đầu từ đầu kia (bàn cờ đối xứng 180°) nhưng phải là hàng trước và liền kề; so khớp với một trong hai chiều
    err = min(np.abs(c - exp).max(), np.abs(c - exp[::-1]).max())
    assert err < 0.4, err


def test_detect_board_returns_none_when_absent():
    assert detect_board(np.full((480, 640, 3), 128, np.uint8), 7, 4) is None


def test_detect_board_accepts_grayscale():
    img, _ = _checker_img()
    assert detect_board(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 7, 4) is not None


# --------------------------------------------------------------------------------------------------------------- điểm chạm
@pytest.mark.parametrize("cols,rows", [(7, 4), (9, 6), (6, 5), (4, 3), (3, 3), (2, 2)])
def test_default_touch_indices_are_valid_unique_and_cover_the_board(cols, rows):
    idx = default_touch_indices(cols, rows)
    assert len(idx) == len(set(idx)) and all(0 <= k < cols * rows for k in idx)
    assert {0, cols - 1, (rows - 1) * cols, rows * cols - 1} <= set(idx)             # 4 góc
    if cols >= 3 and rows >= 3:
        assert len(idx) == 9


def test_touch_order_goes_around_the_perimeter_then_center():
    idx = default_touch_indices(7, 4)
    P = board_object_points(7, 4, 1.0)[idx]
    hops = np.linalg.norm(np.diff(P, axis=0), axis=1)
    assert hops[:-1].max() <= 3.01 + 1e-9                                            # vòng quanh viền: không nhảy xuyên bàn cờ
    assert np.allclose(P[-1], [3, 2], atol=1.01)                                     # điểm cuối là tâm


def _rigid_case(rng, K=9, noise=0.0, reflect=True, ang=23.0, t=(310.0, -45.0)):
    B = board_object_points(7, 4, 15.0)[default_touch_indices(7, 4)][:K]
    a = math.radians(ang)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    if reflect:
        R = R @ np.diag([1.0, -1.0])
    W = B @ R.T + np.array(t) + rng.normal(0, noise, B.shape)
    return B, W


def test_reject_touch_outliers_flags_one_bad_touch():
    rng = np.random.default_rng(0)
    B, W = _rigid_case(rng, noise=0.4)
    W[4] += [7.0, -5.0]
    keep, loo = reject_touch_outliers(B, W)
    assert list(np.nonzero(~keep)[0]) == [4]
    assert loo[4] == loo.max()


def test_reject_touch_outliers_keeps_everything_when_clean():
    rng = np.random.default_rng(1)
    B, W = _rigid_case(rng, noise=0.4)
    keep, _ = reject_touch_outliers(B, W)
    assert keep.all()


def test_reject_touch_outliers_needs_enough_touches():
    rng = np.random.default_rng(2)
    B, W = _rigid_case(rng, K=5, noise=0.2)
    W[2] += [9.0, 9.0]
    keep, _ = reject_touch_outliers(B, W, min_k=6)
    assert keep.all()                                                                # quá ít điểm: không dám loại


def test_reject_touch_outliers_rarely_rejects_with_realistic_hand_noise():
    """Nhiễu tay ~1 mm đồng đều: tỉ lệ loại oan phải thấp (nếu không, người dùng bị loại điểm tốt liên tục)."""
    rng = np.random.default_rng(3)
    n_rej = 0
    for _ in range(200):
        B, W = _rigid_case(rng, noise=1.0)
        n_rej += int((~reject_touch_outliers(B, W)[0]).any())
    assert n_rej <= 8, n_rej


def test_fit_rigid_after_rejection_recovers_the_transform():
    rng = np.random.default_rng(4)
    B, W = _rigid_case(rng, noise=0.5)
    W[0] += [8.0, 6.0]
    keep, _ = reject_touch_outliers(B, W)
    f = fit_rigid_2d(B[keep], W[keep], allow_reflection=True)
    B_all, W_true = _rigid_case(np.random.default_rng(0), noise=0.0)
    assert np.abs(f.apply(B_all) - W_true).max() < 1.2


# --------------------------------------------------------------------------------------------------------------- vạch đánh dấu
def _scene(h=240, w=320):
    ref = np.full((h, w, 3), 90, np.uint8)
    ref += np.random.default_rng(0).integers(0, 4, ref.shape, dtype=np.uint8)
    return ref


def test_find_marker_centroid_and_area():
    ref = _scene()
    img = ref.copy()
    img[100:112, 150:180] = (255, 255, 255)
    u, v, area = find_marker(img, ref)
    assert abs(u - 164.5) < 0.6 and abs(v - 105.5) < 0.6
    assert 300 < area < 480


def test_find_marker_none_when_nothing_changed():
    ref = _scene()
    assert find_marker(ref.copy(), ref) is None


def test_find_marker_ignores_specks_and_takes_the_largest():
    ref = _scene()
    img = ref.copy()
    img[20:24, 20:24] = 255                                                          # hạt nhỏ
    img[100:112, 150:180] = 255
    img[200:210, 60:64] = 255
    u, v, _ = find_marker(img, ref)
    assert abs(u - 164.5) < 1.0 and abs(v - 105.5) < 1.0


def test_find_marker_works_on_grayscale():
    ref = _scene()[:, :, 0]
    img = ref.copy()
    img[100:112, 150:180] = 255
    r = find_marker(img, ref)
    assert r is not None and abs(r[0] - 164.5) < 0.6


# --------------------------------------------------------------------------------------------------------------- độ trễ ảnh↔băng
def _belt_history(v=60.0, t_on=2.0, accel=300.0, hz=200.0, T=6.0):
    t = np.arange(0.0, T, 1.0 / hz)
    s = np.zeros_like(t)
    for i, ti in enumerate(t):
        dt = max(ti - t_on, 0.0)
        tr = v / accel
        s[i] = 0.5 * accel * dt ** 2 if dt <= tr else 0.5 * accel * tr ** 2 + v * (dt - tr)
    return t, s


def _marker_obs(delta, noise=0.15, fps=30.0, seed=0, a0=-80.0, **kw):
    th, sh = _belt_history(**kw)
    rng = np.random.default_rng(seed)
    tr = np.arange(0.2, th[-1] - 0.3, 1.0 / fps) + rng.uniform(0, 1.0 / fps)
    a = a0 + np.interp(tr - delta, th, sh) + rng.normal(0, noise, len(tr))
    return tr, a, th, sh


@pytest.mark.parametrize("delta", [0.0, 0.045, 0.1, 0.17, 0.3])
def test_estimate_latency_recovers_true_delay(delta):
    tr, a, th, sh = _marker_obs(delta)
    d, rms, sens = estimate_latency(tr, a, th, sh)
    assert abs(d - delta) < 0.008, (d, delta)
    assert rms < 0.4 and sens > 0.2


def test_estimate_latency_shifts_one_to_one_with_the_belt_clock_offset():
    """Đồng hồ băng chạy sớm hơn c giây => δ ước lượng nhỏ đi đúng c. Vì vậy ``Belt`` phải gắn dấu thời gian bằng CÙNG đồng hồ với camera."""
    tr, a, th, sh = _marker_obs(0.1)
    d0, _, _ = estimate_latency(tr, a, th, sh)
    d1, _, _ = estimate_latency(tr, a, th + 0.02, sh)
    assert abs((d1 - d0) + 0.02) < 0.004


def test_estimate_latency_requires_a_static_stretch():
    th, sh = _belt_history(t_on=0.0)                                                 # băng chạy ngay từ đầu: không có đoạn tĩnh
    tr = np.arange(0.5, 5.0, 1 / 30.0)
    a = -80 + np.interp(tr - 0.1, th, sh)
    with pytest.raises(ValueError, match="TRƯỚC khi băng chạy"):
        estimate_latency(tr, a, th, sh)


def test_estimate_latency_requires_the_belt_to_move():
    th = np.arange(0, 5, 0.01)
    with pytest.raises(ValueError, match="không chạy"):
        estimate_latency(np.arange(0.2, 4.5, 1 / 30), np.full(int(4.3 * 30) + 1, -80.0)[:len(np.arange(0.2, 4.5, 1 / 30))], th, np.zeros_like(th))


def test_estimate_latency_flags_insensitive_data():
    """Băng chậm / rất ngắn: độ nhạy thấp để người dùng biết kết quả không đáng tin."""
    tr, a, th, sh = _marker_obs(0.1, v=3.0, accel=300.0, noise=0.15)
    _, _, sens = estimate_latency(tr, a, th, sh)
    assert sens < 0.2


# --------------------------------------------------------------------------------------------------------------- độ trễ tay
@pytest.mark.parametrize("tau,v", [(0.05, 40.0), (0.128, 40.0), (0.2, -60.0)])
def test_estimate_arm_lag(tau, v):
    t = np.arange(0.0, 3.0, 0.02)
    cmd = v * t
    meas = np.where(t > tau, v * (t - tau), 0.0) + np.random.default_rng(0).normal(0, 0.1, len(t))
    est, sd = estimate_arm_lag(t, cmd, meas, v)
    assert abs(est - tau) < 0.01 and sd < 0.01


def test_estimate_arm_lag_rejects_short_or_still_segments():
    t = np.arange(0.0, 1.05, 0.2)
    with pytest.raises(ValueError):
        estimate_arm_lag(t, t * 10, t * 10, 10.0)
    with pytest.raises(ValueError):
        estimate_arm_lag(np.arange(0, 3, 0.02), np.zeros(150), np.zeros(150), 0.0)
