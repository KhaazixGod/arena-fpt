"""Metrics of an arena run (KE_HOACH_DAU_TRUONG.md §6): metrics.json + metrics_report.md (Vietnamese table, template §6.3).

    python -m arena.report runs/<id>/trials.csv [--ref CL0] [--repeat runs/<id2>/trials.csv] [--out runs/<id>/metrics_report.md]
Statistics come from dir1/g0_analyze.py (wilson, mcnemar_exact, boot_ci) and are NOT re-implemented here.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dir1"))
from g0_analyze import CAUSES, boot_ci, mcnemar_exact, wilson  # noqa: E402

CAUSE_ORDER = ["merge", "seg_miss", "grasp_point", "timing", "calib", "slip", "collision", "other"]
assert set(CAUSE_ORDER) | {"", "none"} == set(CAUSES), "cause list drifted from g0_analyze.CAUSES"


def _f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _pct(vals, q):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    k = (len(v) - 1) * q / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(ln for ln in f if ln.strip() and not ln.lstrip().startswith("#"))]


def key_group(r):
    return (r["method"], r["cell"], r.get("L") or "")


def key_pair(r):
    return (r["cell"], r["arrangement_id"], r.get("L") or "", r.get("rep") or "0")


def compute(rows, ref="CL0", repeat_rows=None) -> dict:
    valid = [r for r in rows if r.get("valid") == "1"]
    groups = defaultdict(list)
    for r in valid:
        groups[key_group(r)].append(r)
    res = {"groups": [], "causes": [], "bounds": {}, "repeat": None, "n_rows": len(rows), "n_invalid": len(rows) - len(valid)}
    ref_by = {key_pair(r): r for r in valid if r["method"] == ref}
    for (m, c, L), rs in sorted(groups.items()):
        n = len(rs); k = sum(int(r["success"]) for r in rs); kc = sum(int(r.get("clean") or 0) for r in rs)
        lo, hi = wilson(k, n); clo, chi = wilson(kc, n)
        g = {"method": m, "cell": c, "L": L, "n": n, "k": k, "sr": k / n if n else None, "wilson": [lo, hi], "k_clean": kc, "sr_clean": kc / n if n else None,
             "wilson_clean": [clo, chi]}
        if m != ref and ref_by:
            pairs = [(int(ref_by[key_pair(r)]["success"]), int(r["success"]), r["arrangement_id"]) for r in rs if key_pair(r) in ref_by]
            if pairs:
                b = sum(1 for s0, s1, _ in pairs if s1 == 1 and s0 == 0); cc = sum(1 for s0, s1, _ in pairs if s1 == 0 and s0 == 1)
                per = defaultdict(list)
                for s0, s1, aid in pairs:
                    per[aid].append(s1 - s0)
                d_arr = [sum(v) / len(v) for v in per.values()]
                blo, bhi = boot_ci(d_arr) if len(d_arr) >= 2 else (None, None)
                g["paired_vs_ref"] = {"ref": ref, "N": len(pairs), "b_only_this_wins": b, "c_only_ref_wins": cc, "diff": (b - cc) / len(pairs),
                                      "mcnemar_p": mcnemar_exact(b, cc), "boot95": [blo, bhi]}
        dl = [(_f(r.get("t_lift_s")), _f(r.get("t_detect_s"))) for r in rs]
        dl = [a - b for a, b in dl if a is not None and b is not None]
        g["t_detect_to_lift_s"] = {"p50": _pct(dl, 50), "p95": _pct(dl, 95), "n": len(dl)}
        g["ms_step"] = {"p50": _pct([_f(r.get("ms_step_p50")) for r in rs], 50), "p95": _pct([_f(r.get("ms_step_p95")) for r in rs], 95)}
        g["wall_s_mean"] = sum(_f(r.get("wall_s")) or 0.0 for r in rs) / n
        g["outcomes"] = dict(Counter(r.get("outcome", "") for r in rs))
        res["groups"].append(g)
        cnt = Counter(r.get("fail_cause") or "other" for r in rs if r["success"] == "0")
        res["causes"].append({"method": m, "cell": c, "L": L, **{cz: cnt.get(cz, 0) for cz in CAUSE_ORDER}})
    for g in res["groups"]:
        if g["method"] in ("NOOP", "ORACLE"):
            res["bounds"][f"{g['method']}|{g['cell']}|L{g['L']}"] = {"sr": g["sr"], "n": g["n"], "wilson": g["wilson"]}
    # M8 inside one run: repetitions (--reps) of the same (method, cell, arrangement, L) should agree; pixel-based methods see the RTX render noise
    reps = defaultdict(list)
    for r in valid:
        reps[(r["method"], r["cell"], r["arrangement_id"], r.get("L") or "")].append(r)
    within = {}
    for (m, c, aid, L), rs in reps.items():
        if len(rs) < 2:
            continue
        w = within.setdefault(m, {"groups": 0, "all_same_success": 0, "all_same_outcome": 0})
        w["groups"] += 1
        w["all_same_success"] += int(len({r["success"] for r in rs}) == 1)
        w["all_same_outcome"] += int(len({r.get("outcome") for r in rs}) == 1)
    res["within_reps"] = within
    if repeat_rows is not None:
        other = {(r["method"],) + key_pair(r): r for r in repeat_rows if r.get("valid") == "1"}
        same_s = same_o = tot = 0
        diffs = []
        for r in valid:
            o = other.get((r["method"],) + key_pair(r))
            if o is None:
                continue
            tot += 1
            same_s += int(o["success"] == r["success"]); same_o += int(o.get("outcome") == r.get("outcome"))
            if o["success"] != r["success"]:
                diffs.append({"method": r["method"], "arrangement_id": r["arrangement_id"], "L": r.get("L"), "a": r["success"], "b": o["success"]})
        res["repeat"] = {"pairs": tot, "same_success": same_s, "same_outcome": same_o, "differing": diffs}
    return res


def gates(res, ref="CL0") -> list:
    """S0a / S0b / S0c of plan §7 ([de xuat] thresholds) from what is present in the run."""
    out = []
    by = {(g["method"], g["cell"], g["L"]): g for g in res["groups"]}
    for (m, c, L), g in by.items():
        if m == "ORACLE" and c.endswith("C0"):
            out.append(f"S0a ORACLE {c} L{L}: {g['k']}/{g['n']} = {g['sr']:.0%} (cần ≥ 95%) -> {'ĐẠT' if g['sr'] >= 0.95 else 'CHƯA ĐẠT'}")
        if m == "NOOP":
            out.append(f"S0a NOOP {c} L{L}: {g['k']}/{g['n']} = {g['sr']:.0%} (cần ≈ 0%) -> {'ĐẠT' if g['k'] == 0 else 'CHƯA ĐẠT (có thành công giả)'}")
        if m == ref and c == "dev_C0":
            out.append(f"S0b {ref} dev_C0 L{L}: {g['k']}/{g['n']} = {g['sr']:.0%} (cần ≥ 80%) -> {'ĐẠT' if g['sr'] >= 0.80 else 'CHƯA ĐẠT'}")
    rp = res.get("repeat")
    if rp:
        out.append(f"S0c tái lập: {rp['same_success']}/{rp['pairs']} lượt cùng kết quả thành công/thất bại, {rp['same_outcome']}/{rp['pairs']} cùng outcome")
    return out


def fmt(x, p=0):
    return "—" if x is None else f"{x:.{p}f}"


def render_md(res, manifest, run_id, ref="CL0") -> str:
    L = []
    L.append(f"Lần chạy {run_id} · engine=isaac · {manifest.get('date', '?')} · hash arena {manifest.get('arena_sha256', '?')[:8]} · Isaac {manifest.get('isaacsim', '?')} · "
             f"cl0 {manifest.get('cl0_code_sha256', '?')[:8]} · vật: {manifest.get('objects', '?')}")
    L.append("")
    L.append(f"| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so {ref} (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for g in res["groups"]:
        pv = g.get("paired_vs_ref")
        d = (f"{pv['diff']:+.0%} (p={pv['mcnemar_p']:.3f}; [{fmt(pv['boot95'][0] * 100 if pv['boot95'][0] is not None else None)}, "
             f"{fmt(pv['boot95'][1] * 100 if pv['boot95'][1] is not None else None)}]%, N={pv['N']})") if pv else "—"
        L.append(f"| {g['method']} | {g['cell']} | {g['L']} | {g['n']} | {g['k']} | {g['sr']:.0%} [{g['wilson'][0]:.0%}, {g['wilson'][1]:.0%}] | {g['sr_clean']:.0%} | {d} | "
                 f"{fmt(g['t_detect_to_lift_s']['p50'], 2)}/{fmt(g['t_detect_to_lift_s']['p95'], 2)} | {fmt(g['ms_step']['p50'], 1)}/{fmt(g['ms_step']['p95'], 1)} |")
    L.append("")
    L.append("Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):")
    L.append("| Phương pháp | Ô | L | " + " | ".join(CAUSE_ORDER) + " |")
    L.append("|---|---|---|" + "---|" * len(CAUSE_ORDER))
    for c in res["causes"]:
        L.append(f"| {c['method']} | {c['cell']} | {c['L']} | " + " | ".join(str(c[k]) for k in CAUSE_ORDER) + " |")
    L.append("")
    b = res["bounds"]
    L.append("Chặn dưới/trên: " + (", ".join(f"{k.replace('|', ' ')} = {v['sr']:.0%} (n={v['n']})" for k, v in b.items()) if b else "chưa chạy NOOP/ORACLE"))
    rp = res.get("repeat")
    wr = res.get("within_reps") or {}
    L.append("Độ lặp lại: " + (f"{rp['same_success']}/{rp['pairs']} lượt cùng kết quả, {rp['same_outcome']}/{rp['pairs']} cùng outcome (so với lần chạy --repeat)" if rp
                                else ("; ".join(f"{m}: {v['all_same_success']}/{v['groups']} nhóm lặp cùng kết quả" for m, v in wr.items()) if wr
                                      else "chưa đo (dùng --repeat hoặc --reps ≥ 2)")))
    walls = [g["wall_s_mean"] for g in res["groups"]]
    L.append(f"Tốc độ: {sum(walls) / len(walls):.0f} giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: {res['n_invalid']}/{res['n_rows']}" if walls else "Tốc độ: —")
    gs = gates(res, ref)
    if gs:
        L.append("")
        L.append("Cổng sim (§7, ngưỡng [đề xuất]):")
        L += [f"- {x}" for x in gs]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--ref", default="CL0")
    ap.add_argument("--repeat", default="", help="trials.csv of a second run with the same plan (metric M8)")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    rows = read_rows(a.csv)
    rep = read_rows(a.repeat) if a.repeat else None
    res = compute(rows, a.ref, rep)
    run_dir = os.path.dirname(os.path.abspath(a.csv))
    mpath = os.path.join(run_dir, "manifest.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    md = render_md(res, manifest, os.path.basename(run_dir), a.ref)
    out = a.out or os.path.join(run_dir, "metrics_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(os.path.dirname(out), "metrics.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
