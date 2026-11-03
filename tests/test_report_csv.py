"""report.py numbers equal g0_analyze's; run_arena's CSV is read by g0_analyze.read_trials unchanged."""
import csv
import random

from g0_analyze import mcnemar_exact, read_trials, wilson

from arena.report import compute
from arena.run_arena import ARENA_COLUMNS


def _rows(seed=3):
    from cl0.run_g0 import CSV_COLUMNS
    rng = random.Random(seed)
    rows, tid = [], 0
    for i in range(40):
        for m, p in (("CL0", 0.6), ("ORACLE", 0.9), ("NOOP", 0.0)):
            s = int(rng.random() < p)
            rows.append({c: "" for c in CSV_COLUMNS + ARENA_COLUMNS} | dict(trial_id=str(tid), method=m, cell="dev_C0", arrangement_id=f"dev_C0_{i:03d}",
                        success=str(s), valid="1", fail_cause="" if s else rng.choice(["slip", "timing", "other"]), outcome="x", L="0.25", rep="0",
                        clean=str(s), wall_s="30", ms_step_p50="5", ms_step_p95="9", t_detect_s="0.2", t_lift_s="2.0"))
            tid += 1
    rows.append(dict(rows[0], trial_id=str(tid), valid="0", success="0", fail_cause=""))
    return rows


def test_report_matches_g0_analyze(tmp_path):
    rows = _rows()
    res = compute(rows, "CL0")
    g = {r["method"]: r for r in res["groups"]}
    for m in ("CL0", "ORACLE", "NOOP"):
        sel = [r for r in rows if r["method"] == m and r["valid"] == "1"]
        k = sum(int(r["success"]) for r in sel)
        assert g[m]["n"] == len(sel) and g[m]["k"] == k and list(g[m]["wilson"]) == list(wilson(k, len(sel)))
    base = {r["arrangement_id"]: int(r["success"]) for r in rows if r["method"] == "CL0" and r["valid"] == "1"}
    ch = {r["arrangement_id"]: int(r["success"]) for r in rows if r["method"] == "ORACLE"}
    b = sum(1 for a in ch if ch[a] == 1 and base[a] == 0); c = sum(1 for a in ch if ch[a] == 0 and base[a] == 1)
    pv = g["ORACLE"]["paired_vs_ref"]
    assert (pv["b_only_this_wins"], pv["c_only_ref_wins"]) == (b, c) and pv["mcnemar_p"] == mcnemar_exact(b, c)
    assert res["n_invalid"] == 1


def test_csv_readable_by_g0_analyze(tmp_path):
    from cl0.run_g0 import CSV_COLUMNS
    p = tmp_path / "trials.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, CSV_COLUMNS + ARENA_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(_rows())
    rows, warns = read_trials(str(p))
    assert len(rows) == 121 and warns == []


def test_within_run_repetitions():
    rows = _rows()
    extra = []
    for r in rows:
        if r["method"] == "CL0" and r["valid"] == "1":
            r2 = dict(r, rep="1", trial_id=str(int(r["trial_id"]) + 10000))
            if r["arrangement_id"] == "dev_C0_000":
                r2["success"] = "0" if r["success"] == "1" else "1"
                r2["outcome"] = "y"
            extra.append(r2)
    res = compute(rows + extra, "CL0")
    w = res["within_reps"]["CL0"]
    assert w["groups"] == 40 and w["all_same_success"] == 39


def test_repetitions_do_not_inflate_n():
    rows = [r for r in _rows() if r["valid"] == "1"]
    extra = [dict(r, rep="1", trial_id=str(int(r["trial_id"]) + 10000)) for r in rows]
    a, b = compute(rows, "CL0"), compute(rows + extra, "CL0")
    for ga, gb in zip(a["groups"], b["groups"]):
        assert (ga["n"], ga["k"], ga["wilson"]) == (gb["n"], gb["k"], gb["wilson"]) and gb["n_trials"] == 2 * ga["n_trials"]
        assert ga.get("paired_vs_ref") == gb.get("paired_vs_ref")
