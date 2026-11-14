"""E18 (KE_HOACH_TASKS.md): success per task / family / split from task runs (trials.csv with task_id).

    python3 scripts/e18_summary.py gate runs/e18_pilot_a runs/e18_pilot_b                 # expert gate: >= 4/5 per task
    python3 scripts/e18_summary.py test runs/e18_test_*                                    # pre-registered E18 report (PREREGISTRATION_E18.md)
    python3 scripts/e18_summary.py table runs/...                                          # plain table
"""
import csv
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from arena.tasks import HELD_OUT, task_list  # noqa: E402

GATE_K, GATE_N = 4, 5


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def binom_sf(k, n, p):
    """P(X >= k), X ~ Bin(n, p)"""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def load(dirs):
    rows = []
    for d in dirs:
        p = os.path.join(d, "trials.csv")
        if not os.path.exists(p):
            print(f"missing {p}")
            continue
        for r in csv.DictReader(open(p)):
            if r.get("valid") == "1" and r.get("task_id"):
                r["run"] = os.path.basename(d.rstrip("/"))
                rows.append(r)
    return rows


def per_task(rows):
    S = defaultdict(lambda: [0, 0, defaultdict(int)])
    for r in rows:
        s = S[(r["method"], r["task_id"])]
        s[0] += int(r["success"]); s[1] += 1
        if r["success"] != "1":
            s[2][r.get("fail_cause_auto") or r.get("fail_cause") or "?"] += 1
    return S


def fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k:3d}/{n:<3d} = {100 * k / max(n, 1):5.1f}% [{100 * lo:4.0f}, {100 * hi:4.0f}]"


def table(rows):
    T = task_list()
    S = per_task(rows)
    methods = sorted({m for m, _ in S})
    for m in methods:
        print(f"\n== {m}")
        fam = defaultdict(lambda: [0, 0])
        for tid in T:
            if (m, tid) not in S:
                continue
            k, n, causes = S[(m, tid)]
            fam[(T[tid]["family"], "heldout" if tid in HELD_OUT else "train")][0] += k
            fam[(T[tid]["family"], "heldout" if tid in HELD_OUT else "train")][1] += n
            print(f"  {'H' if tid in HELD_OUT else ' '} {tid:18s} {k}/{n}  {dict(causes) if causes else ''}")
        for key in sorted(fam):
            print(f"  family {key[0]:7s} {key[1]:8s} {fmt(*fam[key])}")
    return S


def gate(rows):
    T = task_list()
    S = per_task(rows)
    ok, bad = [], []
    for tid in T:
        k, n, causes = S.get(("TASK_EXPERT", tid), (0, 0, {}))
        (ok if n >= GATE_N and k >= GATE_K else bad).append((tid, k, n, dict(causes)))
    print(f"E18 expert gate (TASK_EXPERT >= {GATE_K}/{GATE_N} per task): {len(ok)} pass, {len(bad)} fail")
    for tid, k, n, c in bad:
        print(f"  FAIL {tid:18s} {k}/{n} {c}")
    tot_k = sum(S[k][0] for k in S if k[0] == "TASK_EXPERT" and k[1] in T); tot_n = sum(S[k][1] for k in S if k[0] == "TASK_EXPERT" and k[1] in T)
    print(f"  overall {fmt(tot_k, tot_n)}")
    return ok, bad


def test(rows):
    """Pre-registered E18 report (PREREGISTRATION_E18.md section 3)."""
    T = task_list()
    S = table(rows)
    act = sorted({m for m, _ in S if m.startswith("REMOTE:")})
    for m in act:
        def agg(which, fam=None):
            k = n = 0
            for tid in T:
                if (m, tid) in S and (which == "all" or (tid in HELD_OUT) == (which == "heldout")) and (fam is None or T[tid]["family"] == fam):
                    k += S[(m, tid)][0]; n += S[(m, tid)][1]
            return k, n
        ks, ns = agg("train"); kh, nh = agg("heldout")
        nk, nn = 0, 0
        for tid in HELD_OUT:
            if ("NOOP", tid) in S:
                nk += S[("NOOP", tid)][0]; nn += S[("NOOP", tid)][1]
        p0 = max(nk / nn if nn else 0.0, 0.01)                   # NOOP held-out rate, floored at 1 % so the test is not trivially passed at p0 = 0
        p = binom_sf(kh, nh, p0) if nh else float("nan")
        fam_ok = all(agg("train", f)[0] >= 0.30 * agg("train", f)[1] for f in ("pick", "place", "pull", "topple") if agg("train", f)[1])
        print(f"\n== E18 decision for {m}")
        print(f"  trained tasks  {fmt(ks, ns)}   per family >= 30%: {fam_ok}")
        print(f"  held-out tasks {fmt(kh, nh)}   NOOP held-out {nk}/{nn}; one-sided binomial vs p0 = {p0:.3f}: p = {p:.4g}")
        print(f"  H-skills (trained >= 50% and every family >= 30%): {'SUPPORTED' if ns and ks >= 0.5 * ns and fam_ok else 'NOT SUPPORTED'}")
        print(f"  H-compose (held-out >= 30% and p <= 0.05):        {'SUPPORTED' if nh and kh >= 0.3 * nh and p <= 0.05 else 'NOT SUPPORTED'}")


if __name__ == "__main__":
    mode, dirs = sys.argv[1], sys.argv[2:]
    rows = load(dirs)
    {"gate": gate, "test": test, "table": table}[mode](rows)
