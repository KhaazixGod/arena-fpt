"""Automatic labels of a trial from ground truth: success (M1), clean success (M2), failure cause (M4, closed list), detection/lift times (M5).

The rules are written in arena/LABEL_RULES.md BEFORE use; this file implements them in the same order.  Thresholds marked [de xuat] there.
Input layout = arena.trial.GTRecorder columns: t, belt_s_gt, tcp_x, tcp_y, tcp_z (grasp centre = gripper_frame_link + R @ tcp_offset), jaw_yaw, grip_pos,
then <name>.a, <name>.b, <name>.z, <name>.yaw for every placed object.
"""
from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Sequence

import numpy as np

CAUSES = ["merge", "seg_miss", "grasp_point", "timing", "calib", "slip", "collision", "other"]
LIFT_MM, HOLD_S = 25.0, 2.0
ON_BELT_TOL_MM = 5.0
PUSH_MM = 10.0                # collision / clean: displacement in the belt frame [de xuat]
SLIP_LIFT_MM = 5.0            # "was lifted" for slip
MERGE_PAD_MM = 5.0
OFFSET_MM = 8.0               # calib (selection error) and timing / grasp_point (TCP vs target at CLOSE) [de xuat]
ISOLATED_GAP_MM = 30.0


def _parse_est(est) -> Optional[tuple]:
    """CL-0's freeze event stores est = (a_b, b, theta), possibly stringified by the trial JSON."""
    if est is None:
        return None
    if isinstance(est, (list, tuple)):
        return float(est[0]), float(est[1])
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(est))
    return (float(nums[0]), float(nums[1])) if len(nums) >= 2 else None


def _first_phase(phases: Sequence, name: str) -> Optional[float]:
    for t, n in phases:
        if n == name:
            return float(t)
    return None


def _first_event(events: Sequence[dict], name: str) -> Optional[dict]:
    for e in events:
        if e["name"] == name:
            return e
    return None


def label(gt: np.ndarray, columns: List[str], events: List[dict], phases: Sequence, outcome: str, diag: Dict, placements: List[dict],
          speed_mm_s: float, specs: Dict[str, object], belt_top_mm: float, belt_end_a_mm: float, w_mm: float, phi_deg: float = 90.0) -> dict:
    col = {c: i for i, c in enumerate(columns)}
    t = gt[:, col["t"]]
    s = gt[:, col["belt_s_gt"]]
    u = np.array([math.cos(math.radians(phi_deg)), math.sin(math.radians(phi_deg))])
    v = np.array([-u[1], u[0]])
    tcp_xy = gt[:, [col["tcp_x"], col["tcp_y"]]]
    tcp_a, tcp_b = tcp_xy @ u, tcp_xy @ v
    names = [p["name"] for p in placements]
    O = {}
    for n in names:
        sp = specs[n]
        a, b, z = gt[:, col[f"{n}.a"]], gt[:, col[f"{n}.b"]], gt[:, col[f"{n}.z"]]
        r = sp.footprint_radius_mm
        O[n] = dict(a=a, b=b, z=z, r=r, lift=z - sp.height_mm / 2.0 - belt_top_mm,
                    on_belt=(np.abs(z - (belt_top_mm + sp.height_mm / 2.0)) <= ON_BELT_TOL_MM) & (a <= belt_end_a_mm - r),
                    ab=a - s, dist_tcp=np.hypot(tcp_a - a, tcp_b - b))
    dt = np.diff(t, prepend=t[0])
    out = dict(success=0, clean=0, fail_cause_auto="", target="", t_success_s=None, t_detect_s=None, t_lift_s=None, details={})

    # ---- 1. success (M1)
    best = None
    for n in names:
        ok = (O[n]["lift"] >= LIFT_MM) & (O[n]["dist_tcp"] <= w_mm / 2.0)
        run = 0.0
        for i in range(len(t)):
            run = run + (dt[i] if i > 0 and ok[i - 1] else 0.0) if ok[i] else 0.0
            if ok[i] and run >= HOLD_S - 1e-9:
                if best is None or t[i] < best[1]:
                    best = (n, float(t[i]))
                break
    if best is not None:
        out.update(success=1, target=best[0], t_success_s=best[1])

    # ---- 2. clean (M2)
    def moved(n, t_until):
        sel = (t <= t_until) & O[n]["on_belt"]
        if not sel.any():
            return 0.0
        d = np.hypot(O[n]["ab"][sel] - O[n]["ab"][0], O[n]["b"][sel] - O[n]["b"][0])
        return float(d.max())

    if out["success"]:
        others = {n: moved(n, out["t_success_s"]) for n in names if n != out["target"]}
        out["details"]["moved_others_mm"] = {k: round(x, 1) for k, x in others.items()}
        out["clean"] = int(all(x <= PUSH_MM for x in others.values()))

    # ---- 5. times (M5)
    sel_ev = _first_event(events, "select")
    out["t_detect_s"] = float(sel_ev["t"]) if sel_ev else None
    t_close = _first_phase(phases, "CLOSE")
    t_lift = _first_phase(phases, "LIFT")
    i_sel = int(np.argmin(np.abs(t - sel_ev["t"]))) if sel_ev else None

    # ---- 3. target when failed
    if not out["success"]:
        if t_close is not None:
            i = int(np.argmin(np.abs(t - t_close)))
            out["target"] = min(names, key=lambda n: O[n]["dist_tcp"][i]) if names else ""
        elif sel_ev is not None and names:
            pa, pb = float(sel_ev["data"].get("a_b", np.nan)), float(sel_ev["data"].get("b", np.nan))
            out["target"] = min(names, key=lambda n: math.hypot(O[n]["ab"][i_sel] - pa, O[n]["b"][i_sel] - pb))
    tg = out["target"]
    if t_lift is None and tg:
        up = np.nonzero(O[tg]["lift"] >= SLIP_LIFT_MM)[0]
        t_lift = float(t[up[0]]) if len(up) else None
    out["t_lift_s"] = t_lift
    if out["success"]:
        return out

    # ---- 4. failure cause, first matching rule
    det = out["details"]
    t_until = t_close if t_close is not None else float(t[-1])
    pushed = {n: moved(n, t_until) for n in names}
    det["moved_before_close_mm"] = {k: round(x, 1) for k, x in pushed.items()}
    if tg:
        det["max_lift_target_mm"] = round(float(O[tg]["lift"].max()), 1)

    def done(cause):
        out["fail_cause_auto"] = cause
        return out

    if any(x > PUSH_MM for x in pushed.values()):
        return done("collision")
    if tg and O[tg]["lift"].max() >= SLIP_LIFT_MM:
        return done("slip")
    if sel_ev is not None and names:
        pa, pb = float(sel_ev["data"].get("a_b", np.nan)), float(sel_ev["data"].get("b", np.nan))
        d = {n: math.hypot(O[n]["ab"][i_sel] - pa, O[n]["b"][i_sel] - pb) for n in names}
        det["select_err_mm"] = round(min(d.values()), 1)
        if sum(1 for n in names if d[n] <= O[n]["r"] + MERGE_PAD_MM) >= 2:
            return done("merge")
        # rule 4 (changed 29/10, LABEL_RULES.md log): the LAST target estimate before CLOSE ("freeze" if any), compared with GT at that instant
        fz = [e for e in events if e["name"] == "freeze" and (t_close is None or e["t"] <= t_close + 1e-9)]
        est = _parse_est(fz[-1]["data"].get("est")) if fz else None
        if est is not None:
            ie = int(np.argmin(np.abs(t - fz[-1]["t"])))
            ea, eb = est
        else:
            ie, ea, eb = i_sel, pa, pb
        de = {n: math.hypot(O[n]["ab"][ie] - ea, O[n]["b"][ie] - eb) for n in names}
        near = min(de, key=de.get)
        det["estimate_err_mm"] = round(de[near], 1)
        isolated = all(math.hypot(O[near]["ab"][ie] - O[m]["ab"][ie], O[near]["b"][ie] - O[m]["b"][ie]) - O[near]["r"] - O[m]["r"] > ISOLATED_GAP_MM
                       for m in names if m != near)
        if de[near] > OFFSET_MM and isolated:
            return done("calib")
    if t_close is not None and tg:
        i = int(np.argmin(np.abs(t - t_close)))
        da, db = float(tcp_a[i] - O[tg]["a"][i]), float(tcp_b[i] - O[tg]["b"][i])
        det.update(delta_close_mm=round(math.hypot(da, db), 1), delta_a_mm=round(da, 1), delta_b_mm=round(db, 1))
        if speed_mm_s > 0 and math.hypot(da, db) > OFFSET_MM and abs(da) >= abs(db):
            return done("timing")
        return done("grasp_point")
    if outcome == "no_target":
        return done("seg_miss" if float((diag or {}).get("n_ok_dets", 0) or 0) == 0 else "other")
    if outcome in ("late", "timeout", "hard_timeout"):
        return done("timing")
    return done("other")
