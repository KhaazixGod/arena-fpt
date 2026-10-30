"""E2 summary table from <run>/trials.csv (+ trial_XXXX.json): success rate with Wilson 95 % CI (dir1/g0_analyze.wilson, not re-implemented), outcomes, x position of the object.
    python3 arena/scripts/e2_summary.py arena/runs/e2/cl0_dev
"""
import csv, json, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dir1"))
from g0_analyze import wilson
run = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "runs/e2/cl0_dev")
rows = list(csv.DictReader(open(os.path.join(run, "trials.csv"))))
print(f"{run}: {len(rows)} trials, valid=0: {sum(1 for r in rows if r['valid'] == '0')}")
def line(name, rs):
    v = [r for r in rs if r["valid"] == "1"]; k = sum(int(r["success_gt"]) for r in v); n = len(v)
    lo, hi = wilson(k, n)
    oc = Counter(r["outcome"] for r in v)
    print(f"{name:28s} SR {k:2d}/{n:2d} = {100 * k / max(n, 1):5.1f} %  Wilson95 [{100 * lo:4.1f}, {100 * hi:4.1f}]  outcomes {dict(oc)}")
for kind in ("static", "belt"):
    line(kind, [r for r in rows if r["kind"] == kind])
line("all", rows)
print("by object:")
for name in sorted({r["object"] for r in rows}):
    line("  " + name, [r for r in rows if r["object"] == name])
print("by object x (= -b0) band:")
for lo_, hi_ in ((130, 160), (160, 190), (190, 230)):
    line(f"  x in [{lo_},{hi_})", [r for r in rows if lo_ <= -float(r["b0_mm"]) < hi_])
print("wall s per trial: mean %.0f, total %.0f min" % (sum(float(r["wall_s"] or 0) for r in rows) / max(len(rows), 1), sum(float(r["wall_s"] or 0) for r in rows) / 60))
print("trials not succeeding:")
for r in rows:
    if r["valid"] == "1" and r["success_gt"] == "0":
        print(f"  #{int(r['trial']):03d} {r['kind']:6s} {r['object']:10s} a0={r['a0_mm']:>6} x={-float(r['b0_mm']):6.1f} outcome={r['outcome']} t_end={r['t_end_s']}")
