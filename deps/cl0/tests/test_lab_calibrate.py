"""'Phòng thí nghiệm ảo': chạy CHÍNH các lệnh cl0.calibrate (board → belt → background → lag) với người thử ảo trên thế giới mô phỏng
theo thời gian ảo, rồi dựng chồng CL-0 từ các file sinh ra và chạy lượt thử vòng kín.

Giới hạn trung thực: người thử ảo chạm với nhiễu Gauss 1 mm; camera/thế giới là mô phỏng. Con số ở đây là mức SAI SỐ MONG ĐỢI trong điều kiện
đó, KHÔNG phải bảo đảm cho phần cứng thật."""
import json
import os

import cv2
import numpy as np
import pytest

import labkit
from cl0 import tune as T
from cl0.config import Config, load_config
from cl0.geometry import PlaneCalib
from cl0.sim.harness import SimSetup, arrangement_to_placed, build_system
from cl0.sim.lab import LabSession, Operator

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def pl(tmp_path_factory):
    return labkit.run_pipeline(str(tmp_path_factory.mktemp("lab")), SimSetup(seed=3))


def test_pipeline_wrote_all_calibration_files(pl):
    for f in ("calib.json", "background.npz", "cfg.toml", "board_preview.png", "background_preview.png"):
        assert os.path.exists(os.path.join(pl.D, f)), f
    cal = PlaneCalib.load(os.path.join(pl.D, "calib.json"))
    assert cal.mm_per_step > 0 and 0 <= cal.latency_s < 0.5


def test_board_step_maps_image_to_world_within_a_few_mm(pl):
    cal, lab, s = pl.calib, pl.lab, pl.sys
    A, B = np.linspace(-200, 200, 9), np.linspace(-50, 50, 5)
    u, v = np.array([0.0, 1.0]), np.array([-1.0, 0.0])                       # φ = 90°
    W = np.array([(s.ca + a) * u + (s.cb + b) * v for a in A for b in B])
    err = np.linalg.norm(cal.pix_to_world(lab.w_to_px(W)) - W, axis=1)
    assert err.mean() < 2.5 and err.max() < 5.0, (err.mean(), err.max())
    assert abs(cal.z_plane_mm - s.setup.z_belt) < 1.5


def test_belt_step_recovers_direction_scale_and_latency(pl):
    cal, s = pl.calib, pl.sys
    assert abs((cal.belt_dir_deg - 90.0 + 180) % 360 - 180) < 1.5
    assert abs(cal.mm_per_step / s.setup.mm_per_step - 1.0) < 0.02
    assert abs(cal.latency_s - pl.lab.lat) < 0.015


def test_lag_step_suggests_a_lead_near_the_true_servo_delay(pl):
    assert 0.07 < pl.lead < 0.18, pl.lead                                    # mô hình servo: τ = 0,10 s + trễ lệnh 0,02 s


def test_calibration_log_reports_the_diagnostics_users_need(pl):
    for s in ("sai số leave-one-out", "tỉ lệ kích thước thực/danh nghĩa", "độ nhạy", "Cửa sổ nhìn từ trên", "lead_s"):
        assert s in pl.log, s


def test_stack_built_from_calibration_files_grasps_robust_shapes(pl, tmp_path_factory):
    """Cả chuỗi: hiệu chuẩn -> file -> build_stack -> vòng kín. Các dạng 'dễ' (lồi, đủ cao, đủ hẹp) phải gắp được với sai số hiệu chuẩn thực tế."""
    names = ["disc30", "box25x50", "ellipse28x48", "lowcon30", "disc22", "bar18x60"]
    rng = np.random.default_rng(1)
    items = [[(n, 0.0, float(rng.uniform(45, 75)), float(rng.uniform(0, 180)))] for n in names]
    res = labkit.trials(pl, items, cache_dir=str(tmp_path_factory.mktemp("reach")))
    bad = [(n, r) for n, r in zip(names, res) if not r[0]]
    assert not bad, bad
    assert all(r[3] < 4.0 for r in res), [r[3] for r in res]                 # TCP lệch tâm vật lúc má kẹp chạm: vài mm


def test_known_hard_cases_fail_for_the_documented_reasons(pl, tmp_path_factory):
    """Giới hạn đã biết của CL-0: vật rộng hơn kẹp, vật dẹt thấp hơn độ cao kẹp cố định. Phải thất bại ĐÚNG lý do (không hỏng lặng lẽ)."""
    res = labkit.trials(pl, [[("box60x60", 0.0, 60.0, 0.0)], [("plate20x45", 0.0, 60.0, 0.0)]], cache_dir=str(tmp_path_factory.mktemp("reach")))
    assert (res[0][0], res[0][1]) == (False, "no_target")
    assert not res[1][0] and res[1][1] == "empty_grasp" and res[1][2] == "too_high"


def test_tune_reach_and_watch_run_on_calibration_files(pl):
    cfgp = pl.cfg_path
    lab = pl.lab
    lab.world.objects.extend(arrangement_to_placed(pl.sys, [("disc30", 0, 60, 0), ("box25x50", 100, 40, 30)], a_start=-100))
    lab.advance(1.0)
    frame = os.path.join(pl.D, "frame.png")
    cv2.imwrite(frame, lab.world.render(0.0))
    out_png = os.path.join(pl.D, "reach.png")
    assert T.main(["reach", "--config", cfgp, "--image", frame, "--out", out_png]) == 0
    assert os.path.exists(out_png) and cv2.imread(out_png) is not None
    with LabSession(lab, Operator(lab)):
        assert T.main(["watch", "--config", cfgp, "--seconds", "3", "--out", os.path.join(pl.D, "watch"), "--reach", "--save-every", "1.0"]) == 0
    summ = json.load(open(os.path.join(pl.D, "watch", "watch_summary.json"), encoding="utf-8"))
    assert summ["frames"] >= 5 and "detect_ms_p95" in json.dumps(summ)


def test_wrong_belt_scale_in_config_is_caught_by_closed_loop(pl, tmp_path_factory):
    """Cấu hình sai mm/xung 25% (quên cập nhật sau khi đo lại) phải làm hỏng lượt gắp - nghĩa là các lượt đúng ở trên có giá trị kiểm."""
    items = [[("disc30", 0.0, 60.0, 0.0)]]
    good = labkit.trials(pl, items, cache_dir=str(tmp_path_factory.mktemp("reach")))
    assert good[0][0]
    cfg = load_config(pl.cfg_path)
    saved = pl.calib.mm_per_step
    try:
        pl.calib.mm_per_step = saved * 1.25                                  # chỉ ảnh hưởng world.belt_scale_error trong trials()
        bad = labkit.trials(pl, items, cache_dir=str(tmp_path_factory.mktemp("reach")))
    finally:
        pl.calib.mm_per_step = saved
    assert not bad[0][0], bad
