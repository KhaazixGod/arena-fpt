"""Đóng băng CL-0 trước lượt test đầu tiên (§3.4: quy tắc công bằng). Ghi băm mã + băm cấu hình + ghi chú vào ``frozen.json``.

    python -m cl0.freeze --config configs/cl0.toml --hours 14 --notes "dev: 4 vật, 12 sắp xếp; bật yaw_mode=local"

``run_g0 --require-frozen`` từ chối chạy nếu mã hoặc cấu hình khác bản đã đóng băng. Sau khi đóng băng KHÔNG sửa gì.
Nếu buộc phải sửa vì lỗi phần mềm/phần cứng: sửa, rồi ``freeze --force --notes "SỬA ĐỔI: <lý do>"``. ``--force`` bắt buộc có ghi chú
và KHÔNG xoá dấu vết: bản đóng băng cũ (băm mã, băm cấu hình, giờ tinh chỉnh, ghi chú) được chuyển vào mục ``amendments`` của
``frozen.json`` mới cùng lý do; phải công bố các sửa đổi đó.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import sys

from .system import code_sha256, file_sha256


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default=None, help="mặc định: frozen.json cạnh file cấu hình")
    ap.add_argument("--hours", type=float, default=None, help="số giờ làm việc đã dùng để tinh chỉnh (≤ 16 theo kế hoạch: 2 ngày)")
    ap.add_argument("--notes", default="")
    ap.add_argument("--force", action="store_true", help="đóng băng lại sau khi sửa (cần --notes lý do; bản cũ được giữ trong `amendments`)")
    a = ap.parse_args(argv)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.config)), "frozen.json")
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    amendments: list = []
    if os.path.exists(out):
        if not a.force:
            print(f"{out} đã tồn tại; đã đóng băng rồi. Dùng --force nếu thật sự muốn đóng băng lại (bắt buộc ghi lý do vào --notes).")
            return 1
        if not a.notes.strip():
            print("--force cần --notes nêu lý do sửa đổi (bản cũ được lưu vào `amendments` và phải công bố).")
            return 1
        try:
            with open(out, encoding="utf-8") as f:
                old = json.load(f)
        except (OSError, ValueError):
            old = {}
        amendments = list(old.get("amendments", [])) + [dict(
            superseded_at=now, reason=a.notes, created=old.get("created"), config_sha256=old.get("config_sha256"),
            code_sha256=old.get("code_sha256"), tuning_hours=old.get("tuning_hours"), notes=old.get("notes"))]
    d = dict(created=now, config=os.path.abspath(a.config),
             config_sha256=file_sha256(a.config), code_sha256=code_sha256(), tuning_hours=a.hours, notes=a.notes,
             python=sys.version.split()[0], platform=platform.platform(), amendments=amendments)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(f"đã ghi {out}\n  config_sha256 {d['config_sha256'][:16]}…\n  code_sha256   {d['code_sha256'][:16]}…")
    if a.hours is not None and a.hours > 16:
        print("CẢNH BÁO: vượt 2 ngày làm việc (16 giờ) so với quy tắc công bằng §3.4; ghi rõ trong bài.")
    return 0


def check_frozen(config_path: str, frozen_path: str | None = None) -> tuple[bool, str]:
    fp = frozen_path or os.path.join(os.path.dirname(os.path.abspath(config_path)), "frozen.json")
    if not os.path.exists(fp):
        return False, f"chưa có {fp}; chạy `python -m cl0.freeze --config {config_path}` trước"
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    bad = []
    if d.get("config_sha256") != file_sha256(config_path):
        bad.append("cấu hình đã đổi")
    if d.get("code_sha256") != code_sha256():
        bad.append("mã cl0 đã đổi")
    return (not bad), ("; ".join(bad) if bad else "khớp bản đóng băng")


if __name__ == "__main__":
    raise SystemExit(main())
