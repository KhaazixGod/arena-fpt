"""Đóng băng CL-0 (§3.4): ghi băm mã + cấu hình; kiểm tra phát hiện đúng sự thay đổi."""
import json
import os
import shutil

import pytest

from cl0 import freeze
from cl0.system import code_sha256, file_sha256

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def cfg_path(tmp_path):
    p = tmp_path / "cl0.toml"
    shutil.copy(os.path.join(ROOT, "configs", "sim_test.toml"), p)
    return str(p)


def test_freeze_writes_hashes_and_check_passes(cfg_path):
    assert freeze.main(["--config", cfg_path, "--hours", "10", "--notes", "dev: 4 vật"]) == 0
    fp = os.path.join(os.path.dirname(cfg_path), "frozen.json")
    d = json.load(open(fp, encoding="utf-8"))
    assert d["config_sha256"] == file_sha256(cfg_path) and d["code_sha256"] == code_sha256()
    assert d["tuning_hours"] == 10 and d["notes"] == "dev: 4 vật" and d["amendments"] == []
    ok, msg = freeze.check_frozen(cfg_path)
    assert ok and "khớp" in msg


def test_check_detects_config_change(cfg_path):
    freeze.main(["--config", cfg_path])
    with open(cfg_path, "a", encoding="utf-8") as f:
        f.write("\n# sửa nhẹ\n")
    ok, msg = freeze.check_frozen(cfg_path)
    assert not ok and "cấu hình đã đổi" in msg and "mã" not in msg


def test_check_detects_code_change(cfg_path, monkeypatch):
    freeze.main(["--config", cfg_path])
    monkeypatch.setattr(freeze, "code_sha256", lambda: "0" * 64)
    ok, msg = freeze.check_frozen(cfg_path)
    assert not ok and "mã cl0 đã đổi" in msg


def test_check_fails_when_not_frozen_yet(cfg_path):
    ok, msg = freeze.check_frozen(cfg_path)
    assert not ok and "freeze" in msg


def test_freeze_refuses_to_overwrite_without_force(cfg_path, capsys):
    assert freeze.main(["--config", cfg_path]) == 0
    assert freeze.main(["--config", cfg_path]) == 1
    assert "đã tồn tại" in capsys.readouterr().out
    assert freeze.main(["--config", cfg_path, "--force", "--notes", "đóng băng lại: lý do"]) == 0


def test_force_requires_a_reason_and_keeps_the_audit_trail(cfg_path, capsys):
    fp = os.path.join(os.path.dirname(cfg_path), "frozen.json")
    assert freeze.main(["--config", cfg_path, "--hours", "12", "--notes", "bản đầu"]) == 0
    first = json.load(open(fp, encoding="utf-8"))
    assert first["amendments"] == []
    assert freeze.main(["--config", cfg_path, "--force"]) == 1                      # không lý do => từ chối
    assert "--notes" in capsys.readouterr().out
    assert json.load(open(fp, encoding="utf-8")) == first                           # và không đụng tới file
    with open(cfg_path, "a", encoding="utf-8") as f:                                # sửa cấu hình vì lỗi, đóng băng lại
        f.write("\n# sửa lỗi cổng serial\n")
    assert freeze.main(["--config", cfg_path, "--force", "--hours", "13", "--notes", "SỬA ĐỔI: sai cổng serial"]) == 0
    second = json.load(open(fp, encoding="utf-8"))
    assert second["notes"] == "SỬA ĐỔI: sai cổng serial" and second["config_sha256"] == file_sha256(cfg_path)
    assert len(second["amendments"]) == 1
    am = second["amendments"][0]
    assert am["config_sha256"] == first["config_sha256"] and am["code_sha256"] == first["code_sha256"]
    assert am["notes"] == "bản đầu" and am["tuning_hours"] == 12 and am["reason"] == "SỬA ĐỔI: sai cổng serial"
    with open(cfg_path, "a", encoding="utf-8") as f:                                # lần sửa thứ hai: chuỗi dài ra, không mất bản đầu
        f.write("# lần hai\n")
    assert freeze.main(["--config", cfg_path, "--force", "--notes", "SỬA ĐỔI: lần hai"]) == 0
    third = json.load(open(fp, encoding="utf-8"))
    assert [x["notes"] for x in third["amendments"]] == ["bản đầu", "SỬA ĐỔI: sai cổng serial"]
    assert freeze.check_frozen(cfg_path)[0]


def test_force_copes_with_a_corrupt_old_file(cfg_path):
    fp = os.path.join(os.path.dirname(cfg_path), "frozen.json")
    with open(fp, "w", encoding="utf-8") as f:
        f.write("{không phải json")
    assert freeze.main(["--config", cfg_path, "--force", "--notes", "khôi phục"]) == 0
    d = json.load(open(fp, encoding="utf-8"))
    assert len(d["amendments"]) == 1 and d["amendments"][0]["reason"] == "khôi phục"


def test_freeze_warns_when_tuning_exceeds_two_days(cfg_path, capsys):
    freeze.main(["--config", cfg_path, "--hours", "20"])
    assert "CẢNH BÁO" in capsys.readouterr().out


def test_custom_frozen_path(cfg_path, tmp_path):
    out = str(tmp_path / "x" / "my_frozen.json")
    os.makedirs(os.path.dirname(out))
    assert freeze.main(["--config", cfg_path, "--out", out]) == 0
    assert freeze.check_frozen(cfg_path, out)[0]


def test_code_hash_is_deterministic_and_ignores_pycache_and_sim():
    h = code_sha256()
    assert h == code_sha256() and len(h) == 64
    import cl0.system as S
    src = open(S.__file__, "rb").read()
    assert b'"__pycache__", "sim", "tests"' in src                                  # ghi nhớ: sim/ không thuộc mã chạy thật
