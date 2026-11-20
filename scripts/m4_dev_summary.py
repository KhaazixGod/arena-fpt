"""Summary of the M4 DEV configurations against DP_W seed 1000 on the same 20 dev scenes (runs/p4_dev_dp_w_s1000_dev_c2_l05)."""
import csv, glob, json, math, os, sys
from collections import Counter

def rows(d):
    p = os.path.join(d, "trials.csv")
    return {r["arrangement_id"]: r for r in csv.DictReader(open(p)) if r["valid"] == "1"} if os.path.exists(p) else {}

def mcnemar(b, c):                       # exact two-sided
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

base = rows("runs/p4_dev_dp_w_s1000_dev_c2_l05")
print(f"baseline DP_W s1000: {sum(int(r['success']) for r in base.values())}/{len(base)}")
print(f"{'config':14s} {'n':>3s} {'succ':>4s} {'gained':>6s} {'lost':>4s} {'p':>6s}  causes")
for d in sorted(glob.glob("runs/m4_dev_*_dev_c2_l05")):
    r = rows(d)
    ids = sorted(set(r) & set(base))
    s = sum(int(r[i]["success"]) for i in ids)
    g = sum(1 for i in ids if r[i]["success"] == "1" and base[i]["success"] == "0")
    l = sum(1 for i in ids if r[i]["success"] == "0" and base[i]["success"] == "1")
    causes = Counter(r[i]["fail_cause_auto"] for i in ids if r[i]["success"] == "0")
    print(f"{os.path.basename(d)[7:-11]:14s} {len(ids):3d} {s:4d} {g:6d} {l:4d} {mcnemar(g, l):6.3f}  {dict(causes)}")
