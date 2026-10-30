"""LABEL_RULES.md on synthetic ground truth."""
import numpy as np

from arena.labeler import label
from arena.objects import INTERIM_SPECS

SPECS = {s.name: s for s in INTERIM_SPECS}
TOP, END, W = -2.4, 300.0, 60.0


def make(n_ticks, objs, tcp_ab, s=None):
    """objs: {name: (a(t), b(t), lift_bottom(t))} arrays; tcp_ab: (a(t), b(t)).  phi = 90: x = -b, y = a."""
    t = np.arange(n_ticks) * 0.02
    s = np.zeros(n_ticks) if s is None else s
    cols = ["t", "belt_s_gt", "tcp_x", "tcp_y", "tcp_z", "jaw_yaw", "grip_pos"]
    data = [t, s, -tcp_ab[1], tcp_ab[0], np.full(n_ticks, 50.0), np.zeros(n_ticks), np.zeros(n_ticks)]
    for n, (a, b, lift) in objs.items():
        cols += [f"{n}.a", f"{n}.b", f"{n}.z", f"{n}.yaw"]
        data += [a, b, TOP + SPECS[n].height_mm / 2 + lift, np.zeros(n_ticks)]
    return np.stack(data, axis=1), cols


def pl(*names):
    return [{"name": n, "a_mm": 0.0, "b_mm": -180.0, "yaw_deg": 0.0} for n in names]


def lab(gt, cols, events=(), phases=(), outcome="", diag=None, placements=(), v=0.0):
    return label(gt, cols, list(events), list(phases), outcome, diag or {}, list(placements), v, SPECS, TOP, END, W, 90.0)


def test_success_needs_lift_and_jaws():
    n = 300
    lift = np.where(np.arange(n) >= 100, 40.0, 0.0)
    gt, cols = make(n, {"cyl35": (np.zeros(n), np.full(n, -180.0), lift)}, (np.zeros(n), np.full(n, -180.0)))
    r = lab(gt, cols, placements=pl("cyl35"))
    assert r["success"] == 1 and r["target"] == "cyl35" and abs(r["t_success_s"] - (100 + 100) * 0.02) < 0.03
    gt2, _ = make(n, {"cyl35": (np.zeros(n), np.full(n, -180.0), lift)}, (np.zeros(n), np.full(n, -120.0)))     # TCP 60 mm away: not in the jaws
    assert lab(gt2, cols, placements=pl("cyl35"))["success"] == 0


def test_slip_and_collision():
    n = 300
    lift = np.where((np.arange(n) >= 100) & (np.arange(n) < 150), 30.0, 0.0)          # lifted 1 s, then lost
    gt, cols = make(n, {"cyl35": (np.zeros(n), np.full(n, -180.0), lift)}, (np.zeros(n), np.full(n, -180.0)))
    r = lab(gt, cols, phases=[(1.0, "CLOSE"), (2.0, "LIFT")], outcome="dropped_in_hold", placements=pl("cyl35"))
    assert r["success"] == 0 and r["fail_cause_auto"] == "slip"
    other_a = np.where(np.arange(n) >= 30, 15.0, 0.0)                                  # the neighbour is pushed 15 mm before the close
    gt, cols = make(n, {"cyl35": (np.zeros(n), np.full(n, -180.0), np.zeros(n)), "cube35": (60 + other_a, np.full(n, -180.0), np.zeros(n))},
                    (np.zeros(n), np.full(n, -180.0)))
    r = lab(gt, cols, phases=[(1.0, "CLOSE")], outcome="empty_grasp", placements=pl("cyl35", "cube35"))
    assert r["fail_cause_auto"] == "collision"


def test_timing_vs_grasp_point_and_no_target():
    n = 200
    obj = {"cyl35": (np.zeros(n), np.full(n, -180.0), np.zeros(n))}
    gt, cols = make(n, obj, (np.full(n, 15.0), np.full(n, -180.0)))                    # 15 mm along the belt at CLOSE
    assert lab(gt, cols, phases=[(1.0, "CLOSE")], outcome="empty_grasp", placements=pl("cyl35"), v=40.0)["fail_cause_auto"] == "timing"
    assert lab(gt, cols, phases=[(1.0, "CLOSE")], outcome="empty_grasp", placements=pl("cyl35"), v=0.0)["fail_cause_auto"] == "grasp_point"
    gt, cols = make(n, obj, (np.zeros(n), np.full(n, -192.0)))                          # 12 mm across: grasp_point even when moving
    assert lab(gt, cols, phases=[(1.0, "CLOSE")], outcome="empty_grasp", placements=pl("cyl35"), v=40.0)["fail_cause_auto"] == "grasp_point"
    assert lab(gt, cols, outcome="no_target", diag={"n_ok_dets": 0}, placements=pl("cyl35"))["fail_cause_auto"] == "seg_miss"
    assert lab(gt, cols, outcome="no_target", diag={"n_ok_dets": 12}, placements=pl("cyl35"))["fail_cause_auto"] == "other"
    assert lab(gt, cols, outcome="timeout", placements=pl("cyl35"))["fail_cause_auto"] == "timing"


def test_merge_and_calib():
    n = 200
    objs = {"cyl35": (np.zeros(n), np.full(n, -180.0), np.zeros(n)), "cyl28": (np.full(n, 34.0), np.full(n, -180.0), np.zeros(n))}
    gt, cols = make(n, objs, (np.zeros(n), np.full(n, -150.0)))
    sel = [{"t": 0.5, "name": "select", "data": {"a_b": 17.0, "b": -180.0}}]          # between two touching objects
    assert lab(gt, cols, events=sel, outcome="no_target", diag={"n_ok_dets": 3}, placements=pl("cyl35", "cyl28"))["fail_cause_auto"] == "merge"
    gt, cols = make(n, {"cyl35": objs["cyl35"]}, (np.zeros(n), np.full(n, -150.0)))
    sel = [{"t": 0.5, "name": "select", "data": {"a_b": 0.0, "b": -168.0}}]           # 12 mm off an isolated object
    assert lab(gt, cols, events=sel, outcome="no_target", diag={"n_ok_dets": 3}, placements=pl("cyl35"))["fail_cause_auto"] == "calib"


def test_calib_uses_last_estimate_before_close():
    n = 200
    gt, cols = make(n, {"cyl35": (np.zeros(n), np.full(n, -180.0), np.zeros(n))}, (np.zeros(n), np.full(n, -180.0)))
    ev = [{"t": 0.2, "name": "select", "data": {"a_b": 12.0, "b": -180.0}},                     # 12 mm off at selection ...
          {"t": 0.6, "name": "freeze", "data": {"est": "(1.0, -180.5, 90.0)"}}]                 # ... but refined to 1 mm before the close
    r = lab(gt, cols, events=ev, phases=[(1.0, "CLOSE")], outcome="empty_grasp", placements=pl("cyl35"))
    assert r["fail_cause_auto"] == "grasp_point" and r["details"]["estimate_err_mm"] < 2
    ev[1]["data"]["est"] = "(-9.5, -180.0, 90.0)"                                               # frozen 9.5 mm off: calib
    assert lab(gt, cols, events=ev, phases=[(1.0, "CLOSE")], outcome="empty_grasp", placements=pl("cyl35"))["fail_cause_auto"] == "calib"
