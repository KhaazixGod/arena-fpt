#!/usr/bin/env python3
"""P7 (exploratory, NOT pre-registered): our methods vs the 30-paper benchmark on the benchmark's DEV grid.

Grid = the 40 (arrangement, speed) pairs the benchmark ran: dev_C0_001..010 and dev_C2_001..010 at L0 and L0.25.
Ours: runs/p7_bench_dev_<name>/trials.csv (scripts/p7_bench_dev.sh), this machine, HEAD of paper-dev.
Benchmark: <bench>/results/raw/*/trials.csv (read-only), arena-fpt 4963d40 on the Windows machine; same objects, scene and sheets, other machine and calibration.
Pairs between our runs are same-machine; pairs with a benchmark run are cross-machine (CL0/ORACLE agreement printed as the noise floor).
DEV, chosen after the benchmark numbers were known: descriptive only.  p values: exact McNemar, two-sided, raw and Holm-adjusted within each reference family.

    python3 scripts/p7_bench_compare.py [--bench ../../Benmark_Capstone] [--json runs/p7_bench_compare.json]
"""
import argparse, collections, csv, glob, json, os, statistics, sys
from math import comb

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = [(f"dev_C{c}_{i:03d}", L) for c in (0, 2) for i in range(1, 11) for L in ("0", "0.25")]
CELLS = [("dev_C0", "0"), ("dev_C0", "0.25"), ("dev_C2", "0"), ("dev_C2", "0.25")]
OURS = [  # (name, label, group)
    ("cl0", "CL0", "modular"), ("cl0_w", "CL0_W (W1)", "modular"), ("oracle", "ORACLE", "privileged"), ("oracle_w", "ORACLE_W (W1)", "privileged"),
    ("act_old_s1000", "ACT_old s1000", "ACT_old"), ("act_old_s2000", "ACT_old s2000", "ACT_old"),
    ("act_w_s1000", "ACT_W s1000", "ACT_W"), ("act_w_s2000", "ACT_W s2000", "ACT_W"), ("act_w_s3000", "ACT_W s3000", "ACT_W"),
    ("act_w_slow_s1000", "ACT_W_slow s1000", "ACT_W_slow"),
    ("dp_w_s1000", "DP_W s1000", "DP_W"), ("dp_w_s2000", "DP_W s2000", "DP_W"), ("dp_w_s3000", "DP_W s3000", "DP_W"),
]
BENCH = [  # (label, run dirs, method filter)
    ("bench CL0", ["v2_baselines_dev_20261108", "v2_baselines_dev_cont_20261108"], "CL0"),
    ("bench ORACLE", ["v2_baselines_dev_20261108", "v2_baselines_dev_cont_20261108"], "ORACLE"),
    ("bench NOOP", ["v2_baselines_dev_20261108", "v2_baselines_dev_cont_20261108"], "NOOP"),
    ("P05 CNS frontend", ["v2_p05_cns_frontend_dev"], None),
    ("P07 ViT-VS", ["v2_p07_vitvs_dev"], None),
    ("P17 ODIL stage1", ["v2_p17_odil_stage1_dev"], None),
    ("P18 FlowControl", ["v2_p18_flowcontrol_dev"], None),
    ("P19 ACT", ["v2_p19_act_dev"], None),
]
EXTRA = [("ACT_old s1000 (E14, older code)", ["runs/e14_act_i2_dev", "runs/e14_act_i2_dev2"])]   # reproducibility check of the re-run


def load(files, method=None):
    d = {}
    for f in files:
        if not os.path.exists(f):
            continue
        for r in csv.DictReader(open(f)):
            if r.get("valid") != "1" or (method and r["method"] != method):
                continue
            k = (r["arrangement_id"], r["L"])
            if k in KEYS and k not in d:                 # first valid row per pair, as run_arena resume keeps it
                d[k] = r
    return d


def wilson(s, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = s / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar2(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0.0] * len(ps); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i])); adj[i] = run
    return adj


def fnum(r, k):
    try:
        return float(r.get(k, ""))
    except ValueError:
        return None


def summary(d):
    s = sum(r["success"] == "1" for r in d.values()); n = len(d)
    cells = {f"{c[4:]}/L{L}": f"{sum(d[k]['success'] == '1' for k in d if k[0].startswith(c) and k[1] == L)}/{sum(1 for k in d if k[0].startswith(c) and k[1] == L)}"
             for c, L in CELLS}
    fails = collections.Counter((r.get("fail_cause") or r.get("outcome") or "?") for r in d.values() if r["success"] != "1")
    med = lambda xs: round(statistics.median(xs), 2) if xs else None
    return dict(n=n, s=s, sr=s / n if n else None, ci=wilson(s, n), cells=cells, fails=dict(fails.most_common()),
                t_lift=med([x for r in d.values() if r["success"] == "1" for x in [fnum(r, "t_lift_s")] if x is not None]),
                ms_p50=med([x for r in d.values() for x in [fnum(r, "ms_step_p50")] if x is not None]),
                wall=med([x for r in d.values() for x in [fnum(r, "wall_s")] if x is not None]))


def pair(a, b):
    ks = [k for k in KEYS if k in a and k in b]
    only_a = sum(a[k]["success"] == "1" and b[k]["success"] != "1" for k in ks)
    only_b = sum(a[k]["success"] != "1" and b[k]["success"] == "1" for k in ks)
    agree = sum(a[k]["success"] == b[k]["success"] for k in ks)
    return dict(n=len(ks), only_a=only_a, only_b=only_b, agree=agree, p=mcnemar2(only_a, only_b))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench", default=os.path.join(HERE, "..", "..", "Benmark_Capstone"))
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    raw = os.path.join(a.bench, "results", "raw")
    M = collections.OrderedDict(); kind = {}
    for name, label, group in OURS:
        M[label] = load([os.path.join(HERE, "runs", f"p7_bench_dev_{name}", "trials.csv")]); kind[label] = ("ours", group)
    for label, dirs, meth in BENCH:
        M[label] = load([os.path.join(raw, d, "trials.csv") for d in dirs], meth); kind[label] = ("bench", "bench")
    for label, dirs in EXTRA:
        M[label] = load([os.path.join(HERE, d, "trials.csv") for d in dirs]); kind[label] = ("extra", "extra")
    for p in sorted(glob.glob(os.path.join(HERE, "runs", "p7_bench_dev_p*", "trials.csv"))):   # paper ports re-run here later, if any
        label = os.path.basename(os.path.dirname(p))[len("p7_bench_dev_"):].upper() + " (here)"
        M[label] = load([p]); kind[label] = ("ours", "paper port")

    print("P7 benchmark-DEV comparison (exploratory, DEV, not pre-registered; engine=isaac)")
    print(f"grid: {len(KEYS)} pairs = dev_C0/dev_C2 001..010 x L0/L0.25; ours = this machine, bench = {os.path.normpath(a.bench)} (other machine)\n")
    S = {k: summary(v) for k, v in M.items()}
    print(f"{'method':34s} {'src':5s} {'succ':>7s} {'SR':>6s} {'Wilson 95%':>13s}  {'C0/L0':>6s} {'C0/L.25':>7s} {'C2/L0':>6s} {'C2/L.25':>7s}  {'t_lift':>6s} {'ms_p50':>7s}  failures")
    for k, s in S.items():
        if s["n"] == 0:
            print(f"{k:34s} {kind[k][0]:5s} {'(no valid trials yet)':>7s}"); continue
        inc = "" if s["n"] == len(KEYS) else f"  INCOMPLETE {s['n']}/{len(KEYS)}"
        c = s["cells"]
        print(f"{k:34s} {kind[k][0]:5s} {s['s']:>3d}/{s['n']:<3d} {100 * s['sr']:5.1f}% [{100 * s['ci'][0]:4.1f},{100 * s['ci'][1]:5.1f}]  "
              f"{c['C0/L0']:>6s} {c['C0/L0.25']:>7s} {c['C2/L0']:>6s} {c['C2/L0.25']:>7s}  {s['t_lift'] if s['t_lift'] is not None else '':>6} "
              f"{s['ms_p50'] if s['ms_p50'] is not None else '':>7}  {s['fails']}{inc}")

    print("\nseed groups (mean over seeds, complete runs only):")
    groups = collections.defaultdict(list)
    for name, label, group in OURS:
        if S[label]["n"] == len(KEYS):
            groups[group].append(S[label]["s"])
    for g, v in groups.items():
        if len(v) > 1:
            print(f"  {g:12s} seeds {len(v)}: {v} -> mean {statistics.mean(v):.1f}/40 = {100 * statistics.mean(v) / 40:.1f}%")

    out = dict(grid=KEYS, summary=S, pairs={})
    for ref in ("CL0_W (W1)", "CL0", "bench CL0"):
        if S[ref]["n"] == 0:
            continue
        rows = [(k, pair(M[k], M[ref])) for k in M if k != ref and S[k]["n"] > 0 and kind[k][0] != "extra" and k != "bench NOOP"]
        rows = [(k, p) for k, p in rows if p["n"] > 0]
        if not rows:
            continue
        adj = holm([p["p"] for _, p in rows])
        print(f"\npaired vs {ref} (exact McNemar two-sided; Holm within this table):")
        for (k, p), pa in zip(rows, adj):
            xm = "x-machine" if (kind[k][0] == "bench") != (kind[ref][0] == "bench") else "same machine"
            print(f"  {k:34s} n={p['n']:2d}  only {k.split(' (')[0][:14]:14s} {p['only_a']:2d}  only ref {p['only_b']:2d}  p={p['p']:.4f}  Holm {pa:.4f}  ({xm})")
            out["pairs"][f"{k} | {ref}"] = dict(p, holm=pa, cross_machine=xm == "x-machine")

    print("\nreproducibility (same method: this machine vs benchmark machine; and the E14 run of ACT_old s1000 on older code):")
    for ours, theirs in (("CL0", "bench CL0"), ("ORACLE", "bench ORACLE"), ("ACT_old s1000", "ACT_old s1000 (E14, older code)")):
        if S[ours]["n"] and S[theirs]["n"]:
            p = pair(M[ours], M[theirs])
            print(f"  {ours} vs {theirs}: {S[ours]['s']}/{S[ours]['n']} vs {S[theirs]['s']}/{S[theirs]['n']}, same outcome on {p['agree']}/{p['n']} pairs")
        else:
            print(f"  {ours} vs {theirs}: not available yet")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
