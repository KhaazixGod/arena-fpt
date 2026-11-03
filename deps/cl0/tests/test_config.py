"""Cấu hình: khoá lạ phải báo lỗi, mẫu sinh tự động khớp mặc định, các file mẫu nạp được."""
import dataclasses
import os

import pytest

from cl0.config import Config, config_from_dict, dump_config, load_config, template_toml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_unknown_top_level_key_is_an_error():
    with pytest.raises(KeyError, match="khoá lạ"):
        config_from_dict({"excutor": {}})


def test_unknown_nested_key_is_an_error_and_names_the_section():
    with pytest.raises(KeyError, match="executor"):
        config_from_dict({"executor": {"lead_ss": 0.1}})
    with pytest.raises(KeyError, match="perception.grasp"):
        config_from_dict({"perception": {"grasp": {"gripper_ww_mm": 20}}})


def test_partial_config_keeps_other_defaults():
    cfg = config_from_dict({"executor": {"lead_s": 0.15}, "belt": {"speed_mm_s": 35.0}})
    d = Config()
    assert cfg.executor.lead_s == 0.15 and cfg.belt.speed_mm_s == 35.0
    assert cfg.executor.omega_xy == d.executor.omega_xy and cfg.robot == d.robot


def test_tuple_fields_stay_tuples():
    cfg = config_from_dict({"robot": {"home_q_deg": [1, 2, 3, 4, 5], "tcp_offset_mm": [0, 0, 12.5]}})
    assert cfg.robot.home_q_deg == (1, 2, 3, 4, 5) and cfg.robot.tcp_offset_mm == (0, 0, 12.5)


def test_dump_and_rebuild_round_trip():
    cfg = Config()
    cfg.executor.lead_s = 0.2
    d = dump_config(cfg)
    assert config_from_dict(d) == cfg


def test_template_round_trips_to_defaults(tmp_path):
    p = tmp_path / "t.toml"
    p.write_text(template_toml(), encoding="utf-8")
    assert load_config(str(p)) == Config()


def test_template_lists_every_field_of_every_section():
    txt = template_toml()

    def walk(obj, path):
        for f in dataclasses.fields(obj):
            v = getattr(obj, f.name)
            if dataclasses.is_dataclass(v):
                sec = f"{path}.{f.name}" if path else f.name
                assert f"[{sec}]" in txt, sec
                walk(v, sec)
            else:
                assert f"\n{f.name} = " in txt, (path, f.name)

    walk(Config(), "")


def test_template_with_modified_values_round_trips(tmp_path):
    cfg = Config()
    cfg.executor.lead_s = 0.123
    cfg.robot.home_q_deg = (0.0, -50.0, 50.0, 90.0, 0.0)
    cfg.belt.line_regex = "^C=(-?\\d+)"
    cfg.belt.cmd_speed = "SPD {steps_per_s:.1f}\n"
    cfg.perception.grasp.yaw_mode = "local"
    p = tmp_path / "t.toml"
    p.write_text(template_toml(cfg), encoding="utf-8")
    assert load_config(str(p)) == cfg


def test_repo_template_file_is_in_sync_with_the_code():
    with open(os.path.join(ROOT, "configs", "config_template.toml"), encoding="utf-8") as f:
        assert f.read() == template_toml(), "chạy: python -m cl0.config > configs/config_template.toml"


def test_repo_sim_config_loads():
    cfg = load_config(os.path.join(ROOT, "configs", "sim_test.toml"))
    assert cfg.belt.speed_mm_s == 50.0 and cfg.executor.lead_s == 0.0
