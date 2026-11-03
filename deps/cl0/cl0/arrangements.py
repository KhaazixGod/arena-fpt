"""Đọc tờ sắp xếp do ``make_arrangements.py`` sinh ra: arrangement_id,first_method,idx,object,x_mm,y_mm,yaw_deg.

x_mm: dọc băng so với vật đầu tiên (vật idx = 1 có x = 0); y_mm: ngang băng tính từ mép trái băng (nhìn theo chiều băng chạy);
yaw_deg: góc đặt của vật (độ), tham chiếu theo quy ước của người đặt (xem README_CL0.md §3 và §9).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Item:
    idx: int
    obj: str
    x_mm: float
    y_mm: float
    yaw_deg: float


@dataclass
class Arrangement:
    arrangement_id: str
    first_method: str
    items: List[Item]


def read_arrangements(path: str) -> Dict[str, Arrangement]:
    out: Dict[str, Arrangement] = {}
    with open(path, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    for r in csv.DictReader(lines):
        aid = r["arrangement_id"].strip()
        a = out.setdefault(aid, Arrangement(aid, (r.get("first_method") or "").strip(), []))
        a.items.append(Item(int(r["idx"]), r["object"].strip(), float(r["x_mm"]), float(r["y_mm"]), float(r["yaw_deg"])))
    for a in out.values():
        a.items.sort(key=lambda it: it.idx)
    return out
