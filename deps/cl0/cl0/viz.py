"""Vẽ lớp phủ lên ảnh rectified (để chỉnh nhận thức và để xem lại video lượt thử)."""
from __future__ import annotations

import math
from typing import Optional, Sequence

import cv2
import numpy as np

from .perception import DetectResult, Detection

_COL = {"": (0, 220, 0), "wide": (0, 165, 255), "thin": (0, 165, 255), "edge": (160, 160, 160), "area": (160, 160, 160),
        "arm": (160, 160, 160)}


def draw_detections(res: DetectResult, rect, selected_ab: Optional[Sequence[float]] = None, scale: float = 1.0) -> np.ndarray:
    """Ảnh rectified + đường viền mặt nạ + điểm kẹp (chữ thập), trục khép (đoạn), bề rộng (chữ)."""
    img = res.plane.copy()
    cnts, _ = cv2.findContours(res.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, cnts, -1, (255, 200, 0), 1)
    r = rect.win.res_mm
    for d in res.dets:
        col, row = rect.px_from_ab(d.a_mm, d.b_mm)
        c = _COL.get(d.reject, (0, 0, 255))
        cx, cy = int(round(col)), int(round(row))
        cv2.drawMarker(img, (cx, cy), c, cv2.MARKER_CROSS, 14, 2)
        if d.reject == "" or d.reject in ("wide", "thin"):
            th = math.radians(d.theta_deg)
            L = max(d.width_mm / 2.0 / r, 6)
            dx, dy = L * math.cos(th), L * math.sin(th)
            cv2.line(img, (int(cx - dx), int(cy - dy)), (int(cx + dx), int(cy + dy)), c, 2)
        label = f"{d.reject or 'ok'} w={d.width_mm:.0f}" if d.reject in ("", "wide", "thin") else d.reject
        cv2.putText(img, label, (cx + 8, cy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1, cv2.LINE_AA)
    if selected_ab is not None:
        col, row = rect.px_from_ab(float(selected_ab[0]), float(selected_ab[1]))
        cv2.circle(img, (int(round(col)), int(round(row))), 18, (255, 0, 255), 2)
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return img
