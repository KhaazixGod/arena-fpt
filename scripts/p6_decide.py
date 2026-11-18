"""Decision rules of PREREGISTRATION_PAPER.md section 4, evaluated mechanically.  Committed together with the pre-registration, BEFORE the first TEST trial.

    cd arena && env -u PYTHONPATH ~/venvs/cl0/bin/python scripts/p6_decide.py status|test|selftest [--json OUT]

status    TEST progress: valid / invalid rows per run, nothing about success (safe to look at while the TEST runs)
test      the TEST runs runs/p6_test_c2_<l05|l025>_<name> of scripts/p6_test.sh on locked/paper/test_C2.csv: H1, H1b, H2 with Holm, then the descriptive rows
selftest  the same code on DEV runs whose numbers are already in PAPER_NOTES.md (checks loading, pairing and the tests; decides nothing)

Rules (pre-registration sections 4 and 5), fixed here before the TEST:
- Only valid=1 rows count.  One row per arrangement: the first valid row (a second valid row is reported as a warning).  A run that does not have a valid row
  for each of the 60 arrangements of the sheet is INCOMPLETE; a run with rows of another method, cell or speed, or whose manifest does not show the locked
  sheet and the frozen code and assets of section 7 (arena_sha256 also for every earlier attempt in previous_runs), is INVALID.  Then no decision is printed
  (exit 1).
- H1  CL0_W > CL0 at L0.5: exact McNemar, one-sided, p = P[X >= gained | n = gained + lost, 1/2] (gained: CL0_W succeeds where CL0 fails).
      Supported iff Holm rejects AND SR(CL0_W) - SR(CL0) >= +15 points.
- H1b ORACLE_W > ORACLE at L0.5: the same test; supported iff Holm rejects AND the gap >= +5 points.
- H2  ACT_W vs ACT_old at L0.5: d_i = (mean success of the 3 ACT_W seeds) - (mean of the 2 ACT_old seeds) on arrangement i.  Two-sided sign-flip permutation
      test on T = mean(d): 100 000 sign vectors, numpy.random.default_rng(0).integers(0, 2, (100000, 60)) * 2 - 1; p = (1 + #{|T*| >= |T|}) / (1 + 100 000),
      computed exactly on 6 d_i (integers).  Supported (ACT_W better) iff Holm rejects AND mean(d) > 0.
- Holm-Bonferroni over {H1, H1b, H2} at alpha = 0.05 (step-down; ties in p ordered by name).
Everything else is descriptive and decides nothing: SR with Wilson 95 % CI for every run, seeds pooled, paired comparisons (two-sided exact McNemar for
single runs, the same sign-flip test for pooled seeds), failure causes (fail_cause_auto, else fail_cause), the L0.25 cell (H3).
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from math import comb

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
PREREG = "PREREGISTRATION_PAPER.md"
SHEET = "locked/paper/test_C2.csv"
ALPHA = 0.05
N_PERM, PERM_SEED = 100_000, 0
H1_MIN_PTS, H1B_MIN_PTS = 15.0, 5.0

# run name -> method label in trials.csv (scripts/p6_test.sh: remote methods are REMOTE:<server name>, server name = run name in capitals)
L05_RUNS = ["cl0", "cl0_w", "oracle", "oracle_w", "act_old_s1000", "act_old_s2000", "act_w_s1000", "act_w_s2000", "act_w_s3000",
            "dp_w_s1000", "dp_w_s2000", "dp_w_s3000", "act_w_slow_s1000"]
L025_RUNS = ["cl0", "cl0_w", "oracle", "oracle_w"]
LOCAL = {"cl0": "CL0", "cl0_w": "CL0_W", "oracle": "ORACLE", "oracle_w": "ORACLE_W"}
SPEEDS = {"l05": 0.5, "l025": 0.25}
ACT_W = ["act_w_s1000", "act_w_s2000", "act_w_s3000"]
ACT_OLD = ["act_old_s1000", "act_old_s2000"]
DP_W = ["dp_w_s1000", "dp_w_s2000", "dp_w_s3000"]


def label(name):
    return LOCAL.get(name, "REMOTE:" + name.upper())


def test_dir(speed, name):
    return f"runs/p6_test_c2_{speed}_{name}"


# ---------------------------------------------------------------- statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def mcnemar_one_sided(gained, lost):
    n = gained + lost
    return 1.0 if n == 0 else sum(comb(n, i) for i in range(gained, n + 1)) / 2 ** n


def mcnemar_two_sided(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def seed_mean_diff(A, B, ids):
    """A, B: lists of {arrangement_id: ok}.  -> integer D_i = lcm * (mean_A - mean_B) per arrangement, and lcm (d_i = D_i / lcm)."""
    L = math.lcm(len(A), len(B))
    D = [(L // len(A)) * sum(a[i] for a in A) - (L // len(B)) * sum(b[i] for b in B) for i in ids]
    return np.asarray(D, dtype=np.int64), L


def signflip_two_sided(D, n_perm=N_PERM, seed=PERM_SEED):
    """Two-sided sign-flip permutation p for mean(d) (exact integer arithmetic on D)."""
    rng = np.random.default_rng(seed)
    S = rng.integers(0, 2, size=(n_perm, len(D)), dtype=np.int8).astype(np.int64) * 2 - 1
    T = abs(int(D.sum()))
    Ts = np.abs(S @ D)
    return (1 + int((Ts >= T).sum())) / (1 + n_perm)


def holm(ps, alpha=ALPHA):
    """ps: {name: p}.  -> {name: (threshold, adjusted p, rejected)} (step-down)."""
    order = sorted(ps, key=lambda k: (ps[k], k))
    m, out, adj_run, going = len(order), {}, 0.0, True
    for j, k in enumerate(order):
        thr = alpha / (m - j)
        adj_run = max(adj_run, min(1.0, (m - j) * ps[k]))
        going = going and ps[k] <= thr
        out[k] = (thr, adj_run, going)
    return out


# ---------------------------------------------------------------- data
def sheet_ids(path):
    lines = [ln for ln in open(path, newline="", encoding="utf-8") if not ln.lstrip().startswith("#")]
    ids = []
    for r in csv.DictReader(lines):
        if r["arrangement_id"] not in ids:
            ids.append(r["arrangement_id"])
    return ids


def load(run, method, cell, L, ids):
    """-> dict(ok={id: bool}, cause={id: str}, invalid=int, rows=int, missing=[ids], errors=[str], warnings=[str])"""
    R = dict(ok={}, cause={}, invalid=0, rows=0, missing=list(ids), errors=[], warnings=[])
    p = os.path.join(run, "trials.csv")
    if not os.path.exists(p):
        R["errors"].append(f"{run}: no trials.csv")
        return R
    for r in csv.DictReader(open(p)):
        R["rows"] += 1
        if r["method"] != method or r["cell"] != cell or abs(float(r["L"]) - L) > 1e-6:
            R["errors"].append(f"{run}: trial {r['trial_id']} is ({r['method']}, {r['cell']}, L={r['L']}), expected ({method}, {cell}, L={L})")
            continue
        if r["valid"] != "1":
            R["invalid"] += 1
            continue
        a = r["arrangement_id"]
        if a not in ids:
            R["errors"].append(f"{run}: trial {r['trial_id']} arrangement {a} is not on the sheet")
            continue
        if a in R["ok"]:
            R["warnings"].append(f"{run}: second valid row for {a} (trial {r['trial_id']}); the first is kept")
            continue
        R["ok"][a] = r["success"] == "1"
        R["cause"][a] = "ok" if R["ok"][a] else (r.get("fail_cause_auto") or r.get("fail_cause") or "?")
    R["missing"] = [a for a in ids if a not in R["ok"]]
    return R


def prereg_hashes():
    """section 7 of the pre-registration: 'key: <64 hex>' lines -> {key: hex}; 'commit paper-dev: <40 hex>' too."""
    H = {}
    for ln in open(PREREG, encoding="utf-8"):
        m = re.match(r"^([A-Za-z0-9_./-]+(?: paper-dev)?): ([0-9a-f]{40}|[0-9a-f]{64})\s*$", ln.strip())
        if m:
            H[m.group(1)] = m.group(2)
    return H


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check_manifest(run, H):
    errs = []
    p = os.path.join(run, "manifest.json")
    if not os.path.exists(p):
        return [f"{run}: no manifest.json"]
    m = json.load(open(p))
    want = {"engine": "isaac", "cl0_code_sha256": H.get("cl0_code_sha256"), "usd_sha256": H.get("usd_sha256"), "calib_sha256": H.get("calib_sha256"),
            "background_sha256": H.get("background_sha256")}
    for k, v in want.items():
        if m.get(k) != v:
            errs.append(f"{run}: manifest {k} = {m.get(k)}, expected {v}")
    if (m.get("sheets_sha256") or {}).get("test_C2") != H.get("locked/paper/test_C2.csv"):
        errs.append(f"{run}: manifest sheet hash {(m.get('sheets_sha256') or {}).get('test_C2')} is not the locked sheet")
    for e in [m] + list(m.get("previous_runs") or []):
        if e.get("arena_sha256") != H.get("arena_sha256"):
            errs.append(f"{run}: an attempt of {e.get('date')} ran arena code {str(e.get('arena_sha256'))[:12]}, expected {str(H.get('arena_sha256'))[:12]}")
    return errs


# ---------------------------------------------------------------- report helpers
def sr_line(name, R, n):
    k = sum(R["ok"].values()); m = len(R["ok"]); lo, hi = wilson(k, m)
    causes = Counter(c for c in R["cause"].values() if c != "ok")
    return f"  {name:18s} {k:2d}/{m:<2d} = {100 * k / m:5.1f}%  [{100 * lo:4.1f}, {100 * hi:4.1f}]  valid=0: {R['invalid']}  fails: {dict(causes.most_common())}" if m else f"  {name}: -"


def pair_single(X, Y, ids):
    """X = new, Y = base (each {id: ok}) -> dict with SR gap in points, gained (X ok, Y not), lost."""
    g = sum(X[i] and not Y[i] for i in ids); l = sum(Y[i] and not X[i] for i in ids)
    return dict(kx=sum(X[i] for i in ids), ky=sum(Y[i] for i in ids), n=len(ids), gained=g, lost=l, gap=100.0 * (sum(X[i] for i in ids) - sum(Y[i] for i in ids)) / len(ids))


def describe_pooled(tag, A, B, ids):
    D, L = seed_mean_diff(A, B, ids)
    p = signflip_two_sided(D)
    return f"  {tag:34s} mean d = {100 * D.sum() / (L * len(ids)):+6.1f} pts  (scenes A better {int((D > 0).sum())}, B better {int((D < 0).sum())}, tie {int((D == 0).sum())})  sign-flip p = {p:.3g}"


# ---------------------------------------------------------------- modes
def status():
    ids = sheet_ids(SHEET)
    for sp, names in (("l05", L05_RUNS), ("l025", L025_RUNS)):
        for name in names:
            R = load(test_dir(sp, name), label(name), "test_C2", SPEEDS[sp], ids)
            print(f"  {test_dir(sp, name):40s} valid {len(R['ok']):2d}/60  valid=0 rows {R['invalid']}" + (f"  ERRORS {len(R['errors'])}" if R["errors"] else ""))


def decide(runs, ids, L025, check, out_json=None):
    """runs: {name: R} at L0.5 (all of L05_RUNS), L025: {name: R}.  check: list of blocking problems found by the caller."""
    problems = list(check)
    for name, R in list(runs.items()) + [(f"{k} (L0.25)", v) for k, v in L025.items()]:
        problems += R["errors"]
        if R["missing"]:
            problems.append(f"{name}: INCOMPLETE, {len(ids) - len(R['missing'])}/{len(ids)} arrangements valid")
        for w in R["warnings"]:
            print("WARNING", w)
    if problems:
        print("NO DECISION (incomplete or invalid input):\n  " + "\n  ".join(problems))
        return 1
    ok = {k: v["ok"] for k, v in runs.items()}
    h1 = pair_single(ok["cl0_w"], ok["cl0"], ids); h1["p"] = mcnemar_one_sided(h1["gained"], h1["lost"])
    h1b = pair_single(ok["oracle_w"], ok["oracle"], ids); h1b["p"] = mcnemar_one_sided(h1b["gained"], h1b["lost"])
    D, Lc = seed_mean_diff([ok[k] for k in ACT_W], [ok[k] for k in ACT_OLD], ids)
    h2 = dict(mean_d_pts=100.0 * D.sum() / (Lc * len(ids)), p=signflip_two_sided(D), better_w=int((D > 0).sum()), better_old=int((D < 0).sum()), ties=int((D == 0).sum()))
    hm = holm({"H1": h1["p"], "H1b": h1b["p"], "H2": h2["p"]})
    sup = {"H1": hm["H1"][2] and h1["gap"] >= H1_MIN_PTS, "H1b": hm["H1b"][2] and h1b["gap"] >= H1B_MIN_PTS, "H2": hm["H2"][2] and h2["mean_d_pts"] > 0}
    print(f"DECISION (PREREGISTRATION_PAPER.md section 4), test_C2 L0.5, n = {len(ids)} paired arrangements, Holm over 3 tests at alpha = {ALPHA}")
    for k, h, need in (("H1", h1, H1_MIN_PTS), ("H1b", h1b, H1B_MIN_PTS)):
        thr, adj, rej = hm[k]
        base, new = ("CL0", "CL0_W") if k == "H1" else ("ORACLE", "ORACLE_W")
        print(f"  {k:3s} {new} > {base}: {h['kx']}/{h['n']} vs {h['ky']}/{h['n']}, gap {h['gap']:+.1f} pts (needs >= +{need:.0f}), gained {h['gained']}, lost {h['lost']}, "
              f"one-sided exact McNemar p = {h['p']:.3g} (Holm threshold {thr:.4f}, adjusted p {adj:.3g}) -> {'SUPPORTED' if sup[k] else 'NOT SUPPORTED'}")
    thr, adj, rej = hm["H2"]
    verdict = "SUPPORTED (ACT_W better)" if sup["H2"] else ("DIFFERENT, ACT_old better (H2 not supported)" if rej else "NOT SUPPORTED (no difference shown)")
    print(f"  H2  ACT_W (3 seeds) vs ACT_old (2 seeds): mean d = {h2['mean_d_pts']:+.1f} pts (scenes W better {h2['better_w']}, old better {h2['better_old']}, tie {h2['ties']}), "
          f"two-sided sign-flip p = {h2['p']:.3g} (Holm threshold {thr:.4f}, adjusted p {adj:.3g}) -> {verdict}")
    print("\nDESCRIPTIVE (decides nothing)\n test_C2 L0.5, success rate, Wilson 95 % CI:")
    for name in L05_RUNS:
        print(sr_line(name, runs[name], len(ids)))
    for tag, group in (("ACT_old pooled", ACT_OLD), ("ACT_W pooled", ACT_W), ("DP_W pooled", DP_W)):
        k = sum(sum(ok[g].values()) for g in group); n = len(ids) * len(group); lo, hi = wilson(k, n)
        print(f"  {tag:18s} {k}/{n} = {100 * k / n:5.1f}%  [{100 * lo:4.1f}, {100 * hi:4.1f}]  per seed {[sum(ok[g].values()) for g in group]}")
    print(" paired, pooled seeds (A - B):")
    for tag, A, B in (("CL0_W - ACT_W", ["cl0_w"], ACT_W), ("CL0_W - DP_W", ["cl0_w"], DP_W), ("ORACLE_W - ACT_W", ["oracle_w"], ACT_W),
                      ("ACT_W - DP_W", ACT_W, DP_W), ("CL0 - ACT_old", ["cl0"], ACT_OLD), ("ACT_W_slow - ACT_W", ["act_w_slow_s1000"], ACT_W)):
        print(describe_pooled(tag, [ok[a] for a in A], [ok[b] for b in B], ids))
    p = pair_single(ok["act_w_slow_s1000"], ok["act_w_s1000"], ids)
    print(f"  ACT_W_slow s1000 vs ACT_W s1000 (same seed): {p['kx']} vs {p['ky']}, gained {p['gained']}, lost {p['lost']}, two-sided McNemar p = {mcnemar_two_sided(p['gained'], p['lost']):.3g}")
    print(" test_C2 L0.25 (H3, modular methods only):")
    for name in L025_RUNS:
        print(sr_line(name, L025[name], len(ids)))
    l025 = {}
    for new, base in (("cl0_w", "cl0"), ("oracle_w", "oracle")):
        p = pair_single(L025[new]["ok"], L025[base]["ok"], ids); p["p_two_sided"] = mcnemar_two_sided(p["gained"], p["lost"]); l025[f"{new}_vs_{base}"] = p
        print(f"  {new} vs {base}: {p['kx']} vs {p['ky']}, gap {p['gap']:+.1f} pts, gained {p['gained']}, lost {p['lost']}, two-sided McNemar p = {p['p_two_sided']:.3g}")
    if out_json:
        res = dict(H1=dict(h1, holm=hm["H1"], supported=sup["H1"]), H1b=dict(h1b, holm=hm["H1b"], supported=sup["H1b"]), H2=dict(h2, holm=hm["H2"], supported=sup["H2"]),
                   success={n: sum(ok[n].values()) for n in L05_RUNS}, success_l025={n: sum(L025[n]["ok"].values()) for n in L025_RUNS}, l025_pairs=l025,
                   invalid_rows={n: runs[n]["invalid"] for n in L05_RUNS}, n=len(ids), engine="isaac", script_sha256=sha256_file(os.path.abspath(__file__)))
        json.dump(res, open(out_json, "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
        print(f"\nwritten {out_json}")
    return 0


def test(out_json):
    if not os.path.exists(PREREG):
        sys.exit(f"{PREREG} missing")
    H = prereg_hashes()
    need = ["locked/paper/test_C2.csv", "arena_sha256", "cl0_code_sha256", "usd_sha256", "calib_sha256", "background_sha256"]
    check = [f"{PREREG} section 7 has no '{k}: <sha256>' line" for k in need if k not in H]
    if H.get("locked/paper/test_C2.csv") and sha256_file(SHEET) != H["locked/paper/test_C2.csv"]:
        check.append(f"{SHEET} hash differs from {PREREG}")
    ids = sheet_ids(SHEET)
    if len(ids) != 60:
        check.append(f"{SHEET} has {len(ids)} arrangements, expected 60")
    runs, L025 = {}, {}
    for name in L05_RUNS:
        runs[name] = load(test_dir("l05", name), label(name), "test_C2", 0.5, ids)
        check += check_manifest(test_dir("l05", name), H) if os.path.exists(test_dir("l05", name)) else []
    for name in L025_RUNS:
        L025[name] = load(test_dir("l025", name), label(name), "test_C2", 0.25, ids)
        check += check_manifest(test_dir("l025", name), H) if os.path.exists(test_dir("l025", name)) else []
    return decide(runs, ids, L025, check, out_json)


def selftest():
    """Re-derive DEV numbers of PAPER_NOTES.md with this code: dev_C2 L0.5, CL0 25 -> CL0_W 52 (lost 2, gained 29), ORACLE 45 -> ORACLE_W 58 (lost 0,
    gained 13, two-sided p = 0.0002); first 20 scenes: ACT_W 15/15/13, ACT_old s1000 15 (only one ACT_old seed exists on DEV)."""
    ids60 = [f"dev_C2_{i:03d}" for i in range(1, 61)]
    ids20 = ids60[:20]
    c0 = load("runs/p2_cl0_dev_c2_l05", "CL0", "dev_C2", 0.5, ids60); cw = load("runs/p2_cl0w_dev_c2_l05", "CL0_W", "dev_C2", 0.5, ids60)
    o0 = load("runs/p5_oracle_dev_c2_l05", "ORACLE", "dev_C2", 0.5, ids60); ow = load("runs/p5_woracle_dev_c2_l05", "ORACLE_W", "dev_C2", 0.5, ids60)
    for R in (c0, cw, o0, ow):
        assert not R["missing"] and not R["errors"], (R["missing"], R["errors"])
    h1 = pair_single(cw["ok"], c0["ok"], ids60); h1b = pair_single(ow["ok"], o0["ok"], ids60)
    assert (h1["kx"], h1["ky"], h1["gained"], h1["lost"]) == (52, 25, 29, 2), h1
    assert (h1b["kx"], h1b["ky"], h1b["gained"], h1b["lost"]) == (58, 45, 13, 0), h1b
    assert abs(mcnemar_two_sided(13, 0) - 0.000244) < 1e-6 and abs(mcnemar_one_sided(13, 0) - 0.000122) < 1e-6
    assert mcnemar_one_sided(0, 0) == 1.0 and abs(mcnemar_one_sided(1, 1) - 0.75) < 1e-12 and abs(mcnemar_one_sided(2, 0) - 0.25) < 1e-12
    act = {k: load(f"runs/p4_dev_{k}_dev_c2_l05", "REMOTE:" + k.upper(), "dev_C2", 0.5, ids20) for k in ACT_W + ["act_old_s1000"]}
    for R in act.values():
        assert not R["missing"] and not R["errors"], (R["missing"], R["errors"])
    assert [sum(act[k]["ok"].values()) for k in ACT_W + ["act_old_s1000"]] == [15, 15, 13, 15]
    D, L = seed_mean_diff([act[k]["ok"] for k in ACT_W], [act["act_old_s1000"]["ok"]], ids20)
    p2 = signflip_two_sided(D)
    # permutation sanity: all-zero d -> p = 1; a constant positive d on 20 scenes -> only the all-+ and all-- vectors reach |T| (p ~ 1/100001 + 2^-19)
    assert signflip_two_sided(np.zeros(20, dtype=np.int64)) == 1.0
    p_const = signflip_two_sided(np.ones(20, dtype=np.int64))
    assert p_const < 1e-3, p_const
    hm = holm({"H1": mcnemar_one_sided(29, 2), "H1b": mcnemar_one_sided(13, 0), "H2": p2})
    hx = holm({"a": 0.01, "b": 0.04, "c": 0.03})                  # textbook: 0.01 <= 0.05/3 rejected, 0.03 > 0.05/2 stops -> b, c not rejected
    assert hx["a"][2] and not hx["c"][2] and not hx["b"][2] and abs(hx["c"][1] - 0.06) < 1e-12 and abs(hx["b"][1] - 0.06) < 1e-12
    hy = holm({"a": 0.001, "b": 0.02, "c": 0.04})                 # 0.001 <= 0.0167, 0.02 <= 0.025, 0.04 <= 0.05 -> all rejected
    assert all(v[2] for v in hy.values())
    print("selftest OK (DEV numbers re-derived; this decides nothing)")
    print(f"  dev_C2 L0.5 n=60: CL0_W {h1['kx']} vs CL0 {h1['ky']}, gained {h1['gained']}, lost {h1['lost']}, one-sided p = {mcnemar_one_sided(29, 2):.3g}")
    print(f"  dev_C2 L0.5 n=60: ORACLE_W {h1b['kx']} vs ORACLE {h1b['ky']}, gained 13, lost 0, one-sided p = {mcnemar_one_sided(13, 0):.3g} (two-sided {mcnemar_two_sided(13, 0):.4f})")
    print(f"  dev_C2 L0.5 first 20: ACT_W 15/15/13 vs ACT_old s1000 15: mean d = {100 * D.sum() / (L * 20):+.1f} pts, sign-flip p = {p2:.4f}; constant-d check p = {p_const:.2e}")
    print(f"  Holm on these three: {{{', '.join(f'{k}: thr {v[0]:.4f}, adj {v[1]:.3g}, rejected {v[2]}' for k, v in hm.items())}}}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["status", "test", "selftest"])
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    if a.mode == "status":
        status(); sys.exit(0)
    sys.exit(test(a.json or None) if a.mode == "test" else selftest())
