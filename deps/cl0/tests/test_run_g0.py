"""Bộ chạy G0: CSV đúng định dạng g0_analyze.py, tiếp tục được, người thử, và một lượt mô phỏng thật (chậm)."""
import argparse
import csv
import importlib.util
import json
import os
import shutil

import pytest

from cl0 import run_g0 as G
from cl0.arrangements import Arrangement, Item, read_arrangements
from cl0.config import Config
from cl0.types import TrialEvent

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------------------------------------- tiện ích
class FakeRunner:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def run(self, arr, speed, out_dir, trial_id, record_video):
        self.calls.append((arr.arrangement_id, speed, trial_id, record_video))
        out = self.outcomes.pop(0)
        if isinstance(out, BaseException):
            raise out
        log = [dict(t=0.0, phase="WAIT", q=(1.0, 2.0, 3.0, 4.0, 5.0), qc=None), dict(t=0.02, phase="WAIT", q=(1.0, 2.0, 3.0, 4.0, 5.0), qc=(1, 2, 3, 4, 5))]
        return G.TrialData(out, 9.5, [(0.0, "WAIT")], [TrialEvent(0.0, "phase:WAIT", {"x": 1.0})], log, {"frames": 3}, True, "disc30")

    def close(self):
        pass


class ScriptOperator:
    """Người thử có kịch bản: before -> hành động; judge -> Judgement lấy từ hàng đợi."""

    def __init__(self, before, judgements):
        self.before, self.j = list(before), list(judgements)

    def before_trial(self, arr, text, img_path):
        return self.before.pop(0)

    def judge(self, td):
        return self.j.pop(0)


def _arrs(n=3):
    return {str(i): Arrangement(str(i), "A", [Item(1, "disc30", 0.0, 60.0, 0.0)]) for i in range(1, n + 1)}


def _args(**kw):
    d = dict(csv=None, method="CL0", cell="dev_t", only=None, speed=40.0, operator="tester", no_video=True)
    d.update(kw)
    return argparse.Namespace(**d)


def _run(tmp_path, runner, op, arrs=None, **kw):
    return G.run_session(Config(), _args(**kw), runner, op, str(tmp_path), arrs or _arrs(), {"disc30": 30.0}, "c" * 64, "d" * 64, say=lambda *a, **k: None)


# ---------------------------------------------------------------------------------------------------------- gợi ý nguyên nhân
@pytest.mark.parametrize("outcome,reason,cause", [("no_target", "", "seg_miss"), ("late", "", "timing"), ("timeout", "", "timing"),
                                                  ("empty_grasp", "", "grasp_point"), ("dropped_in_hold", "", "slip"), ("ik_fail", "", "other"),
                                                  ("empty_grasp", "collision", "collision"), ("empty_grasp", "miss", "timing"),
                                                  ("xyz", "", "other")])
def test_suggest_cause(outcome, reason, cause):
    assert G.suggest_cause(outcome, reason) == cause
    assert cause in G.CAUSES


def test_parse_only():
    assert G.parse_only(None) is None and G.parse_only("") is None
    assert G.parse_only("1-3,7, 9") == {"1", "2", "3", "7", "9"}


# ---------------------------------------------------------------------------------------------------------- phiên chạy
def test_session_writes_csv_trial_files_and_log(tmp_path):
    runner = FakeRunner(["picked_hold_complete", "empty_grasp"])
    op = ScriptOperator(["run", "run"], [G.Judgement(1, 1, "", "ok"), G.Judgement(0, 1, "grasp_point", "trượt")])
    rows = _run(tmp_path, runner, op, arrs=_arrs(2))
    assert [r["trial_id"] for r in rows] == [1, 2]
    csv_rows = G.read_csv_rows(str(tmp_path / "g0_trials.csv"))
    assert list(csv_rows[0].keys()) == G.CSV_COLUMNS
    assert csv_rows[0]["success"] == "1" and csv_rows[1]["fail_cause"] == "grasp_point" and csv_rows[1]["speed_mm_s"] == "40.0"
    assert csv_rows[0]["config_sha"] == "d" * 12 and csv_rows[0]["code_sha"] == "c" * 12 and csv_rows[0]["operator"] == "tester"
    meta = json.load(open(tmp_path / "trial_0002.json", encoding="utf-8"))
    assert meta["outcome"] == "empty_grasp" and meta["arrangement_id"] == "2" and meta["events"][0]["name"] == "phase:WAIT"
    lines = open(tmp_path / "trial_0001_log.csv", encoding="utf-8").read().splitlines()
    assert lines[0].split(",")[:4] == ["t", "phase", "q0", "q1"] and len(lines) == 3         # tuple trải thành q0..q4
    assert (tmp_path / "placement_1.png").exists()


def test_trial_json_records_the_hash_of_the_calibration_files_used(tmp_path, monkeypatch):
    """Hiệu chuẩn thay đổi theo buổi và không nằm trong băm đóng băng: mỗi lượt phải ghi băm calib.json/background.npz để truy vết."""
    import hashlib
    cal, bg = tmp_path / "calib.json", tmp_path / "background.npz"
    cal.write_bytes(b"calib-bytes")
    bg.write_bytes(b"bg-bytes")
    cfg = Config()
    cfg.calib_path, cfg.background_path = str(cal), str(bg)
    out = tmp_path / "runs"
    G.run_session(cfg, _args(), FakeRunner(["picked_hold_complete"]), ScriptOperator(["run"], [G.Judgement(1, 1)]), str(out), _arrs(1), {}, "c" * 64, "d" * 64,
                  say=lambda *a, **k: None)
    meta = json.load(open(out / "trial_0001.json", encoding="utf-8"))
    assert meta["calib_sha256"] == hashlib.sha256(b"calib-bytes").hexdigest()
    assert meta["background_sha256"] == hashlib.sha256(b"bg-bytes").hexdigest()
    G.run_session(Config(), _args(cell="dev_nofiles"), FakeRunner(["picked_hold_complete"]), ScriptOperator(["run"], [G.Judgement(1, 1)]),
                  str(tmp_path / "runs2"), _arrs(1), {}, "c" * 64, "d" * 64, say=lambda *a, **k: None)    # file không tồn tại -> null, không lỗi
    assert json.load(open(tmp_path / "runs2" / "trial_0001.json", encoding="utf-8"))["calib_sha256"] is None


def test_resume_skips_arrangements_with_a_valid_trial_and_reruns_invalid_ones(tmp_path):
    arrs = _arrs(3)
    _run(tmp_path, FakeRunner(["picked_hold_complete", "empty_grasp", "picked_hold_complete"]),
         ScriptOperator(["run"] * 3, [G.Judgement(1, 1), G.Judgement(0, 0, "", "ngắt khẩn cấp"), G.Judgement(1, 1)]), arrs=arrs)
    r2 = FakeRunner(["picked_hold_complete"])
    rows = _run(tmp_path, r2, ScriptOperator(["run"], [G.Judgement(1, 1)]), arrs=arrs)
    assert [c[0] for c in r2.calls] == ["2"]                                         # chỉ sắp xếp có lượt KHÔNG hợp lệ được chạy lại
    assert rows[0]["trial_id"] == 4
    all_rows = G.read_csv_rows(str(tmp_path / "g0_trials.csv"))
    assert [r["trial_id"] for r in all_rows] == ["1", "2", "3", "4"]
    # cùng lệnh lần nữa: không còn gì để chạy
    r3 = FakeRunner([])
    assert _run(tmp_path, r3, ScriptOperator([], []), arrs=arrs) == [] and r3.calls == []


def test_resume_is_per_method_and_cell(tmp_path):
    arrs = _arrs(1)
    _run(tmp_path, FakeRunner(["picked_hold_complete"]), ScriptOperator(["run"], [G.Judgement(1, 1)]), arrs=arrs)
    for kw in ({"cell": "dev_other"}, {"method": "I2"}):
        r = FakeRunner(["picked_hold_complete"])
        _run(tmp_path, r, ScriptOperator(["run"], [G.Judgement(1, 1)]), arrs=arrs, **kw)
        assert len(r.calls) == 1, kw


def test_operator_can_skip_or_quit_and_only_filters(tmp_path):
    runner = FakeRunner(["picked_hold_complete"])
    op = ScriptOperator(["skip", "run", "quit"], [G.Judgement(1, 1)])
    rows = _run(tmp_path, runner, op, arrs=_arrs(5), only="2-4")
    assert [r["arrangement_id"] for r in rows] == ["3"] and len(runner.calls) == 1        # "2" bị bỏ qua, "3" chạy, "4" thoát; "1","5" ngoài --only


def test_keyboard_interrupt_stops_without_recording(tmp_path):
    runner = FakeRunner([KeyboardInterrupt()])
    rows = _run(tmp_path, runner, ScriptOperator(["run"], []), arrs=_arrs(2))
    assert rows == [] and not (tmp_path / "g0_trials.csv").exists()


def test_other_exceptions_propagate_so_safety_errors_are_not_swallowed(tmp_path):
    from cl0.hw.arm import SafetyError
    with pytest.raises(SafetyError):
        _run(tmp_path, FakeRunner([SafetyError("nhảy")]), ScriptOperator(["run"], []), arrs=_arrs(1))


class FaultOperator(ScriptOperator):
    """Như ScriptOperator, thêm cách phân loại lượt bị cắt giữa chừng."""

    def __init__(self, before, judgements, faults):
        super().__init__(before, judgements)
        self.faults, self.seen = list(faults), []

    def after_fault(self, msg, link_lost):
        self.seen.append((msg, link_lost))
        return self.faults.pop(0)


def test_link_loss_mid_trial_is_logged_as_invalid_and_the_arrangement_is_rerun_on_resume(tmp_path):
    from cl0.hw.platform import BeltCommError
    arrs = _arrs(2)
    op = FaultOperator(["run", "run"], [G.Judgement(1, 1)], ["invalid"])
    rows = _run(tmp_path, FakeRunner([BeltCommError("mất dòng bộ đếm"), "picked_hold_complete"]), op, arrs=arrs)
    assert len(rows) == 2 and op.seen == [("BeltCommError: mất dòng bộ đếm", True)]
    csv_rows = G.read_csv_rows(str(tmp_path / "g0_trials.csv"))
    assert [(r["arrangement_id"], r["valid"], r["success"], r["outcome"]) for r in csv_rows] == \
        [("1", "0", "0", "aborted:BeltCommError"), ("2", "1", "1", "picked_hold_complete")]
    assert csv_rows[0]["fail_cause"] == "" and "mất dòng bộ đếm" in csv_rows[0]["note"]
    meta = json.load(open(tmp_path / "trial_0001.json", encoding="utf-8"))
    assert meta["link_lost"] is True and "BeltCommError" in meta["traceback"] and meta["arrangement_id"] == "1"
    r2 = FakeRunner(["picked_hold_complete"])                                       # chạy lại cùng lệnh: chỉ sắp xếp 1 (chưa có lượt hợp lệ)
    _run(tmp_path, r2, ScriptOperator(["run"], [G.Judgement(1, 1)]), arrs=arrs)
    assert [c[0] for c in r2.calls] == ["1"]


def test_non_link_fault_chosen_as_failure_counts_as_a_valid_failure(tmp_path):
    from cl0.hw.arm import SafetyError
    op = FaultOperator(["run"], [], ["fail"])
    rows = _run(tmp_path, FakeRunner([SafetyError("lệnh nhảy 60°")]), op, arrs=_arrs(1))
    assert op.seen[0][1] is False                                                    # không phải mất liên lạc: người thử phải tự chọn
    r = G.read_csv_rows(str(tmp_path / "g0_trials.csv"))[0]
    assert (r["valid"], r["success"], r["fail_cause"], r["outcome"]) == ("1", "0", "other", "aborted:SafetyError")
    assert len(rows) == 1


def test_fault_then_quit_records_nothing_and_stops(tmp_path):
    runner = FakeRunner([RuntimeError("x"), "picked_hold_complete"])
    rows = _run(tmp_path, runner, FaultOperator(["run", "run"], [G.Judgement(1, 1)], ["quit"]), arrs=_arrs(2))
    assert rows == [] and len(runner.calls) == 1 and not (tmp_path / "g0_trials.csv").exists()


def test_too_many_invalid_trials_trigger_the_protocol_warning(tmp_path):
    from cl0.types import LinkLost
    said = []
    arrs = _arrs(6)
    runner = FakeRunner([LinkLost("a"), "picked_hold_complete", "picked_hold_complete", "picked_hold_complete", "picked_hold_complete", LinkLost("b")])
    op = FaultOperator(["run"] * 6, [G.Judgement(1, 1)] * 4, ["invalid", "invalid"])
    G.run_session(Config(), _args(), runner, op, str(tmp_path), arrs, {}, "c" * 64, "d" * 64, say=lambda *a, **k: said.append(" ".join(map(str, a))))
    assert any("CẢNH BÁO §4.3" in m for m in said)
    assert any("Lượt không hợp lệ ở ô dev_t: 2/6" in m for m in said)


def test_console_after_fault_prompt_defaults_by_kind_of_fault():
    op, _ = _console([""])                                                           # mất liên lạc: Enter = không hợp lệ
    assert op.after_fault("BeltCommError: x", True) == "invalid"
    op, _ = _console(["", "zzz", "f"])                                               # lỗi khác: không có mặc định, phải chọn
    assert op.after_fault("SafetyError: x", False) == "fail"
    op, _ = _console(["q"])
    assert op.after_fault("BeltCommError: x", True) == "quit"
    assert G.AutoOperator().after_fault("x", False) == "quit"


def test_speed_defaults_to_config_and_zero_is_allowed(tmp_path):
    r = FakeRunner(["no_target"])
    _run(tmp_path, r, ScriptOperator(["run"], [G.Judgement(0, 1, "seg_miss")]), arrs=_arrs(1), speed=0.0)
    assert r.calls[0][1] == 0.0
    r2 = FakeRunner(["no_target"])
    _run(tmp_path / "b", r2, ScriptOperator(["run"], [G.Judgement(0, 1, "seg_miss")]), arrs=_arrs(1), speed=None)
    assert r2.calls[0][1] == Config().belt.speed_mm_s


# ---------------------------------------------------------------------------------------------------------- người thử bàn phím
def _console(answers):
    it = iter(answers)
    out = []
    return G.ConsoleOperator(input_fn=lambda prompt="": next(it), print_fn=lambda *a, **k: out.append(" ".join(map(str, a)))), out


def _td(outcome="picked_hold_complete", reason=""):
    return G.TrialData(outcome, 5.0, [], [], [], {}, True, "disc30", None, reason)


def test_console_before_trial_actions():
    for ans, act in (("", "run"), ("s", "skip"), ("q", "quit"), ("zzz", "skip")):
        op, _ = _console([ans])
        assert op.before_trial(Arrangement("1", "A", []), "text", "") == act


def test_console_judge_accepts_default_and_overrides():
    op, _ = _console(["", ""])                                                       # Enter = theo gợi ý; ghi chú trống
    j = op.judge(_td())
    assert (j.success, j.valid, j.fail_cause) == (1, 1, "")
    op, _ = _console(["0", "", ""])                                                  # thất bại: nguyên nhân mặc định theo gợi ý, ghi chú trống
    j = op.judge(_td("picked_hold_complete"))
    assert (j.success, j.valid, j.fail_cause) == (0, 1, "other") and "đổi success 1->0" in j.note
    op, _ = _console(["1", "ghi chú"])
    j = op.judge(_td("empty_grasp"))
    assert j.success == 1 and "đổi success 0->1" in j.note and j.note.startswith("ghi chú")


def test_console_judge_reprompts_on_invalid_cause_and_handles_invalid_trial():
    op, _ = _console(["", "bậy", "slip", ""])
    j = op.judge(_td("empty_grasp"))
    assert j.fail_cause == "slip" and j.success == 0
    op, _ = _console(["i", "dây USB rơi"])
    j = op.judge(_td())
    assert (j.success, j.valid, j.note) == (0, 0, "dây USB rơi")


def test_auto_operator_uses_ground_truth():
    td = _td("empty_grasp", "slip")
    td.truth_success = False
    j = G.AutoOperator().judge(td)
    assert j.success == 0 and j.valid == 1 and j.fail_cause == "grasp_point"
    td.truth_success = True
    assert G.AutoOperator().judge(td).success == 1


# ---------------------------------------------------------------------------------------------------------- CSV tương thích g0_analyze
def _load_g0_analyze():
    for cand in (os.path.join(ROOT, "..", "dir1", "g0_analyze.py"), os.path.join(ROOT, "dir1", "g0_analyze.py")):
        if os.path.exists(cand):
            spec = importlib.util.spec_from_file_location("g0_analyze", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def test_csv_is_readable_by_g0_analyze(tmp_path):
    mod = _load_g0_analyze()
    if mod is None:
        pytest.skip("không có dir1/g0_analyze.py cạnh gói cl0")
    runner = FakeRunner(["picked_hold_complete", "empty_grasp", "no_target"])
    op = ScriptOperator(["run"] * 3, [G.Judgement(1, 1), G.Judgement(0, 1, "grasp_point"), G.Judgement(0, 0, "", "lỗi cáp")])
    _run(tmp_path, runner, op, arrs=_arrs(3))
    rows, warns = mod.read_trials(str(tmp_path / "g0_trials.csv"))
    assert warns == [] and len(rows) == 3
    assert mod.counts(rows, "CL0", "dev_t")[:2] == (2, 1)                            # 2 lượt hợp lệ, 1 thành công; lượt không hợp lệ bị loại


# ---------------------------------------------------------------------------------------------------------- tờ sắp xếp ví dụ đi kèm
EXAMPLE_ARR = os.path.join(ROOT, "configs", "arr_dev_example.csv")


def test_shipped_example_arrangements_are_valid():
    """configs/arr_dev_example.csv là file người dùng sẽ chạy đầu tiên: phải đọc được, đúng tên vật mô phỏng, nằm trong băng 150 mm,
    các vật không chạm nhau (theo đường kính bao quanh)."""
    from cl0.sim.scene import default_library
    arrs = read_arrangements(EXAMPLE_ARR)
    assert sorted(arrs) == ["1", "2", "3", "4", "5"]
    lib = default_library()
    for a in arrs.values():
        assert [it.idx for it in a.items] == list(range(1, len(a.items) + 1))
        assert a.items[0].x_mm == 0.0
        for it in a.items:
            assert it.obj in lib, it.obj
            assert 20.0 <= it.y_mm <= 130.0, (a.arrangement_id, it)
        for i, p in enumerate(a.items):
            for q in a.items[i + 1:]:
                assert ((p.x_mm - q.x_mm) ** 2 + (p.y_mm - q.y_mm) ** 2) ** 0.5 > 60.0, (a.arrangement_id, p, q)


# ---------------------------------------------------------------------------------------------------------- một lượt mô phỏng thật
@pytest.mark.slow
def test_cli_sim_end_to_end(tmp_path):
    arr = tmp_path / "arr.csv"
    arr.write_text("arrangement_id,first_method,idx,object,x_mm,y_mm,yaw_deg\n"
                   "1,A,1,disc30,0,60,0\n"
                   "2,B,1,box25x50,0,45,30\n"
                   "2,B,2,disc22,160,85,0\n", encoding="utf-8")
    cfg = tmp_path / "cfg.toml"
    shutil.copy(os.path.join(ROOT, "configs", "sim_test.toml"), cfg)
    out = tmp_path / "runs"
    assert G.main(["--sim", "--config", str(cfg), "--arrangements", str(arr), "--cell", "dev_sim", "--out", str(out), "--no-video",
                   "--operator", "pytest"]) == 0
    rows = G.read_csv_rows(str(out / "g0_trials.csv"))
    assert [r["arrangement_id"] for r in rows] == ["1", "2"]
    assert all(r["valid"] == "1" and r["method"] == "CL0" and r["cell"] == "dev_sim" for r in rows)
    assert all(r["success"] == "1" for r in rows), [(r["arrangement_id"], r["outcome"], r["fail_cause"]) for r in rows]
    assert (out / "trial_0001.json").exists() and (out / "trial_0002_log.csv").exists() and (out / "placement_2.png").exists()
    # chạy lại cùng lệnh: tiếp tục, không thêm dòng
    assert G.main(["--sim", "--config", str(cfg), "--arrangements", str(arr), "--cell", "dev_sim", "--out", str(out), "--no-video"]) == 0
    assert len(G.read_csv_rows(str(out / "g0_trials.csv"))) == 2


@pytest.mark.slow
def test_shipped_example_arrangements_run_in_sim(tmp_path):
    """Người dùng thử `--sim` với chính file ví dụ trước khi đụng phần cứng: một vật, và hai/ba vật."""
    cfg = tmp_path / "cfg.toml"
    shutil.copy(os.path.join(ROOT, "configs", "sim_test.toml"), cfg)
    out = tmp_path / "runs"
    assert G.main(["--sim", "--config", str(cfg), "--arrangements", EXAMPLE_ARR, "--cell", "dev_sim", "--out", str(out), "--no-video",
                   "--only", "1,4,5"]) == 0
    rows = G.read_csv_rows(str(out / "g0_trials.csv"))
    assert [r["arrangement_id"] for r in rows] == ["1", "4", "5"]
    assert all(r["success"] == "1" for r in rows), [(r["arrangement_id"], r["outcome"], r["fail_cause"]) for r in rows]


def test_require_frozen_refuses_unfrozen_config(tmp_path, capsys):
    arr = tmp_path / "arr.csv"
    arr.write_text("arrangement_id,first_method,idx,object,x_mm,y_mm,yaw_deg\n1,A,1,disc30,0,60,0\n", encoding="utf-8")
    cfg = tmp_path / "cfg.toml"
    shutil.copy(os.path.join(ROOT, "configs", "sim_test.toml"), cfg)
    rc = G.main(["--sim", "--config", str(cfg), "--arrangements", str(arr), "--cell", "x", "--out", str(tmp_path / "o"), "--require-frozen"])
    assert rc == 2 and "chưa có" in capsys.readouterr().out
    assert not (tmp_path / "o" / "g0_trials.csv").exists()
