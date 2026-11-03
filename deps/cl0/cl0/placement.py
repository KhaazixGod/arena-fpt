"""Tờ đặt vật cho người thử: bảng chữ + ảnh nhìn từ trên (băng chạy từ trái sang phải)."""
from __future__ import annotations

import math
from typing import Dict, Optional

import cv2
import numpy as np

from .arrangements import Arrangement


def placement_text(arr: Arrangement) -> str:
    lines = [f"Sắp xếp #{arr.arrangement_id} (first_method={arr.first_method or '-'}), {len(arr.items)} vật. "
             "x: dọc băng so với vật 1 (+ = về phía hạ lưu); y: từ mép TRÁI băng nhìn theo chiều băng chạy; yaw: ngược chiều kim đồng hồ từ trên nhìn xuống, so với hướng băng chạy",
             f"{'#':>2} {'vật':<18}{'x (mm)':>9}{'y (mm)':>9}{'yaw (°)':>9}"]
    for it in arr.items:
        lines.append(f"{it.idx:>2} {it.obj:<18}{it.x_mm:>9.1f}{it.y_mm:>9.1f}{it.yaw_deg:>9.0f}")
    return "\n".join(lines)


def draw_placement(arr: Arrangement, belt_width_mm: float, diam_mm: Optional[Dict[str, float]] = None, px_per_mm: float = 3.0,
                   path: Optional[str] = None) -> np.ndarray:
    xs = [it.x_mm for it in arr.items]
    x0, x1 = min(xs) - 60.0, max(xs) + 60.0
    W, H = int((x1 - x0) * px_per_mm), int(belt_width_mm * px_per_mm)
    img = np.full((H + 40, W + 20, 3), 245, np.uint8)
    cv2.rectangle(img, (10, 20), (10 + W, 20 + H), (200, 200, 200), -1)
    cv2.putText(img, "MEP TRAI (y=0)", (14, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1, cv2.LINE_AA)
    cv2.arrowedLine(img, (W - 120, H + 34), (W - 10, H + 34), (60, 60, 60), 2, tipLength=0.15)
    cv2.putText(img, "bang chay", (W - 230, H + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (60, 60, 60), 1, cv2.LINE_AA)
    for it in arr.items:
        cx, cy = 10 + (it.x_mm - x0) * px_per_mm, 20 + it.y_mm * px_per_mm
        d = (diam_mm or {}).get(it.obj, 40.0)
        cv2.circle(img, (int(cx), int(cy)), int(d / 2 * px_per_mm), (120, 160, 230), 2)
        th = math.radians(it.yaw_deg)
        L = d / 2 * px_per_mm
        # ảnh: băng chạy sang PHẢI, mép trái ở TRÊN => yaw dương (ngược chiều kim đồng hồ nhìn từ trên xuống) hướng LÊN (y ảnh giảm)
        cv2.line(img, (int(cx), int(cy)), (int(cx + L * math.cos(th)), int(cy - L * math.sin(th))), (0, 0, 200), 2)
        cv2.putText(img, f"{it.idx}:{it.obj}", (int(cx) - 20, int(cy) - int(L) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1,
                    cv2.LINE_AA)
    if path:
        cv2.imwrite(path, img)
    return img
