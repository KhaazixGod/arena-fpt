"""Fixture dùng chung. Chạy:  pytest -m "not slow"  (nhanh, ~1 phút)   |   pytest  (đầy đủ, ~10 phút)."""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from cl0.config import Config                                  # noqa: E402
from cl0.kinematics import SO101Kinematics                     # noqa: E402
from cl0.sim.harness import SimSetup, build_system             # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _isolated_home(tmp_path_factory):
    """Các lệnh ghi cache vào ~/.cache/cl0 (bản đồ với tới); test dùng thư mục tạm để không đụng máy người dùng."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = str(tmp_path_factory.mktemp("home"))
    yield
    if old is None:
        os.environ.pop("HOME", None)
    else:
        os.environ["HOME"] = old


@pytest.fixture(scope="session")
def kin():
    return SO101Kinematics(tcp_offset_mm=(0.0, 0.0, 0.0), margin_deg=3.0)


@pytest.fixture(scope="session")
def sim_sys():
    """Hệ mô phỏng đầy đủ (hiệu chuẩn giả có nhiễu, nền, bộ phát hiện, bộ điều khiển). Dùng chung; các test KHÔNG được sửa nó."""
    return build_system(SimSetup(seed=1), Config())


def run_cases(fn, cases):
    """Tiện ích: chạy fn(case) cho từng case, gom lỗi để báo một lần."""
    bad = []
    for c in cases:
        try:
            fn(c)
        except AssertionError as e:
            bad.append((c, str(e)))
    assert not bad, "\n".join(f"{c}: {m}" for c, m in bad)
