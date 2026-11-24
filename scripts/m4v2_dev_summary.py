"""M4 v2 DEV summary: success, collision failures, median maximum descent speed in successful trials and v2 diagnostics for each DEV run, next to the DP_W (M3) and M4 v1 runs on the same 20 scenes."""
import csv, json, os, sys
import numpy as np
RUNS = [("M3 DP_W s1000", "runs/p4_dev_dp_w_s1000_dev_c2_l05"), ("M4 v1 c1_default", "runs/m4_dev_c1_default_dev_c2_l05"),
        ("M4 v2 vd150", "runs/m4v2_dev_v2a_vd150_dev_c2_l05"), ("M4 v2 vd250", "runs/m4v2_dev_v2b_vd250_dev_c2_l05")] + [(a.split("=")[0], a.split("=")[1]) for a in sys.argv[1:]]
ref = {}
for name, d in RUNS:
    p = d + "/trials.csv"
    if not os.path.exists(p): print(name, "missing"); continue
    rows = [r for r in csv.DictReader(l for l in open(p) if not l.startswith("#")) if r["valid"] == "1"]
    succ = sum(int(r["success"]) for r in rows); col = sum(r["fail_cause_auto"] == "collision" for r in rows if r["success"] != "1")
    vd, push, diag = [], [], {}
    for r in rows:
        tid = int(r["trial_id"]); fj = f"{d}/trial_{tid:04d}.json"; fg = f"{d}/trial_{tid:04d}_gt.npz"
        if os.path.exists(fj):
            j = json.load(open(fj))
            for k, v in (j.get("diag") or {}).items():
                if k.startswith("v2_") or k in ("vs_hold_ticks", "vs_desc_timeout", "vs_auth_timeout", "ik_fail_ticks"): diag[k] = diag.get(k, 0) + v
            mv = (j.get("label", {}).get("details") or {}).get("moved_before_close_mm") or {}
            if r["fail_cause_auto"] == "collision" and mv: push.append(max(mv.values()))
        if r["success"] == "1" and os.path.exists(fg):
            z = np.load(fg, allow_pickle=True); cols = [str(c) for c in z["columns"]]; tz = z["gt"][:, cols.index("tcp_z")]
            i = np.where(tz < 45)[0]
            if len(i): vd.append(float((-np.diff(tz[max(0, i[0] - 25):i[0] + 25]) / 0.02).max()))
    ref[name] = {r["arrangement_id"]: int(r["success"]) for r in rows}
    print(f"{name:20s} n={len(rows):2d} success={succ:2d} collision_fails={col:2d} median_max_descent_speed={np.median(vd) if vd else float('nan'):6.0f} mm/s  median_push={np.median(push) if push else float('nan'):5.1f} mm  diag={diag}")
