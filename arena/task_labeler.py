"""E18 labels of a task trial (arena/tasks.py) from ground truth only.  Same output keys as arena/labeler.py (success, clean, fail_cause_auto, target, ...).

Rules [de xuat, KE_HOACH_TASKS.md §2], evaluated per control tick; success = the condition holds continuously for HOLD (pick: 2 s = M1, others 1 s):
    pick    target lifted >= 25 mm with the grasp centre within w/2 of it                      (M1, target only)
    place   target resting upright on the belt, centre <= 25 mm from the zone centre, released
    pull    target displaced >= 35 mm along the direction, |lateral| <= 20 mm, resting upright, released, never lifted > 10 mm before
    topple  target axis tilted >= 60 deg from vertical, centre displaced >= 10 mm along the direction
"released" = gripper measured >= 20 (open) and the grasp centre >= 10 mm above the object top or >= r + 15 mm away in the plane.
Failure cause (first rule that matches): wrong_object, no_contact, lifted (pull), knocked_over (place/pull), not_released, dropped (pick), short (pull),
missed_zone (place), not_toppled / wrong_direction (topple), other.
"""
from __future__ import annotations

import math
from typing import Dict, List

import numpy as np

from .tasks import A0, B0, PARAMS, ZONE_DA, ZONE_R_MM

LIFT_MM, HOLD_PICK_S, HOLD_S = 25.0, 2.0, 1.0
PULL_MIN_MM, PULL_LAT_MM, PULL_MAX_LIFT_MM = 35.0, 20.0, 10.0
TOPPLE_DEG, TOPPLE_MIN_MM = 60.0, 10.0
UPRIGHT_DEG, REST_TOL_MM = 20.0, 5.0
MOVED_MM = 10.0


def _held(t: np.ndarray, ok: np.ndarray, hold_s: float):
    dt = np.diff(t, prepend=t[0])
    run = 0.0
    for i in range(len(t)):
        run = run + (dt[i] if i > 0 and ok[i - 1] else 0.0) if ok[i] else 0.0
        if ok[i] and run >= hold_s - 1e-9:
            return float(t[i])
    return None


def label_task(gt: np.ndarray, columns: List[str], placements: List[dict], task: dict, specs: Dict[str, object], belt_top_mm: float,
               w_mm: float, phi_deg: float = 90.0) -> dict:
    col = {c: i for i, c in enumerate(columns)}
    t = gt[:, col["t"]]
    u = np.array([math.cos(math.radians(phi_deg)), math.sin(math.radians(phi_deg))])
    v = np.array([-u[1], u[0]])
    txy = gt[:, [col["tcp_x"], col["tcp_y"]]]
    ta, tb, tz = txy @ u, txy @ v, gt[:, col["tcp_z"]]
    grip = gt[:, col["grip_pos"]]
    names = [p["name"] for p in placements]
    tg = [n for n in names if specs[n].category == task["cat"]]
    if len(tg) != 1:
        raise ValueError(f"task {task['id']}: {len(tg)} objects of category {task['cat']} in the scene")
    tg = tg[0]
    O = {}
    for n in names:
        sp = specs[n]
        a, b, z = gt[:, col[f"{n}.a"]], gt[:, col[f"{n}.b"]], gt[:, col[f"{n}.z"]]
        tilt = gt[:, col[f"{n}.tilt"]] if f"{n}.tilt" in col else np.zeros_like(a)
        upright = tilt <= UPRIGHT_DEG
        O[n] = dict(a=a, b=b, z=z, tilt=tilt, h=sp.height_mm, r=sp.footprint_radius_mm, upright=upright,
                    lift=np.where(upright, z - sp.height_mm / 2.0 - belt_top_mm, 0.0),
                    resting=upright & (np.abs(z - (belt_top_mm + sp.height_mm / 2.0)) <= REST_TOL_MM),
                    disp=np.hypot(a - a[0], b - b[0]))
    T = O[tg]
    released = (grip >= 20.0) & ((tz - (belt_top_mm + T["h"]) >= 10.0) | (np.hypot(ta - T["a"], tb - T["b"]) >= T["r"] + 15.0))
    fam = task["family"]
    pa, pb = PARAMS[task["param"]] if task["param"] else (0, 0)
    along = (T["a"] - T["a"][0]) * pa + (T["b"] - T["b"][0]) * pb
    lateral = np.abs((T["a"] - T["a"][0]) * pb - (T["b"] - T["b"][0]) * pa)
    out = dict(success=0, clean=0, fail_cause_auto="", target=tg, t_success_s=None, t_detect_s=None, t_lift_s=None, details={})
    det = out["details"]
    det.update(max_lift_mm=round(float(T["lift"].max()), 1), max_tilt_deg=round(float(T["tilt"].max()), 1), final_disp_mm=round(float(T["disp"][-1]), 1),
               final_along_mm=round(float(along[-1]), 1), final_lateral_mm=round(float(lateral[-1]), 1))

    if fam == "pick":
        ok = (T["lift"] >= LIFT_MM) & (np.hypot(ta - T["a"], tb - T["b"]) <= w_mm / 2.0)
        ts = _held(t, ok, HOLD_PICK_S)
    elif fam == "place":
        za, zb = A0 + ZONE_DA * pa, B0
        dz = np.hypot(T["a"] - za, T["b"] - zb)
        det["final_zone_err_mm"] = round(float(dz[-1]), 1)
        ok = T["resting"] & (dz <= ZONE_R_MM) & released
        ts = _held(t, ok, HOLD_S)
    elif fam == "pull":
        never_lifted = np.maximum.accumulate(T["lift"]) <= PULL_MAX_LIFT_MM
        ok = (along >= PULL_MIN_MM) & (lateral <= PULL_LAT_MM) & T["resting"] & released & never_lifted
        ts = _held(t, ok, HOLD_S)
    elif fam == "topple":
        ok = (T["tilt"] >= TOPPLE_DEG) & (along >= TOPPLE_MIN_MM)
        ts = _held(t, ok, HOLD_S)
    else:
        raise ValueError(fam)
    up = np.nonzero(T["lift"] >= 5.0)[0]
    out["t_lift_s"] = float(t[up[0]]) if len(up) else None
    others = [n for n in names if n != tg]
    t_end = ts if ts is not None else float(t[-1])
    moved_o = {n: float(np.max(np.where(t <= t_end, O[n]["disp"], 0.0))) for n in others}
    det["moved_others_mm"] = {k: round(x, 1) for k, x in moved_o.items()}
    if ts is not None:
        out.update(success=1, t_success_s=ts, clean=int(all(x <= MOVED_MM for x in moved_o.values())))
        return out

    def done(c):
        out["fail_cause_auto"] = c
        return out

    touched = T["disp"].max() > 5.0 or T["lift"].max() >= 5.0 or T["tilt"].max() > 10.0
    if not touched and any(x > MOVED_MM or O[n]["lift"].max() >= 5.0 for n, x in moved_o.items()):
        return done("wrong_object")
    if not touched:
        return done("no_contact")
    if fam == "pull" and T["lift"].max() > PULL_MAX_LIFT_MM:
        return done("lifted")
    if fam in ("place", "pull") and T["tilt"].max() > 45.0:
        return done("knocked_over")
    if fam == "pick":
        return done("dropped" if T["lift"].max() >= 5.0 else "other")
    if fam == "place":
        if T["resting"][-1] and det["final_zone_err_mm"] <= ZONE_R_MM:
            return done("not_released")
        return done("missed_zone")
    if fam == "pull":
        if along[-1] >= PULL_MIN_MM and lateral[-1] <= PULL_LAT_MM:
            return done("not_released")
        return done("short")
    if T["tilt"].max() >= TOPPLE_DEG:
        return done("wrong_direction")
    return done("not_toppled")
