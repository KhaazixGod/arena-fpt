"""M4 decision script (PREREGISTRATION_M4.md section 5).  Reads runs/m4_test_c2_l05_{dp_w,dpvs}_s{1000,2000,3000}; writes runs/m4_test_decision.json.
H1 (primary): the mean over the three seeds of the per-scene difference of success (M4 - M3) is >= GAIN points and the one-sided sign-permutation p (100,000 draws,
numpy seed 0) is <= 0.05.  Everything else is descriptive (per-seed exact McNemar, failure causes, terminal offset, yaw misalignment, corrector diagnostics)."""
import argparse, csv, json, math, os, sys
import numpy as np

GAIN = 10.0
SEEDS = (1000, 2000, 3000)
ELONG = ("box35", "plate30", "plate31", "t34", "u27")          # elongated test objects: reference closing axis perpendicular to the long axis
R = "runs/m4_test_c2_l05_"

def rows(kind, seed):
    d = f"{R}{kind}_s{seed}"
    p = os.path.join(d, "trials.csv")
    return d, {r["arrangement_id"]: r for r in csv.DictReader(open(p)) if r["valid"] == "1"} if os.path.exists(p) else {}

def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)

def mcnemar(b, c, one_sided=False):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p if one_sided else 2 * p)

def close_idx(gp):
    idx = np.where(gp < 30)[0]
    if len(idx) == 0: return None
    k = idx[0]; j = np.where(gp[:k] >= 38)[0]
    return int(j[-1]) if len(j) else max(k - 1, 0)

def offsets(d, rs):
    out = []
    for aid, r in rs.items():
        tid = int(r["trial_id"])
        f = os.path.join(d, f"trial_{tid:04d}_gt.npz")
        if not os.path.exists(f): continue
        g = np.load(f, allow_pickle=True); cols = [str(c) for c in g["columns"]]; G = g["gt"]
        names = sorted({c.split(".")[0] for c in cols if c.endswith(".a")})
        k = close_idx(G[:, cols.index("grip_pos")])
        if k is None: continue
        x, y = G[k, cols.index("tcp_x")], G[k, cols.index("tcp_y")]
        dist = {n: float(np.hypot(y - G[k, cols.index(n + ".a")], x + G[k, cols.index(n + ".b")])) for n in names}
        n = min(dist, key=dist.get)
        rel = float((G[k, cols.index("jaw_yaw")] - G[k, cols.index(n + ".yaw")]) % 180)
        dev = abs((rel - 90 + 90) % 180 - 90)
        out.append(dict(succ=int(r["success"]), off=dist[n], obj=n, yaw_dev=dev))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default="runs/m4_test_decision.json"); a = ap.parse_args()
    res = {"gain_required_points": GAIN}
    data = {}
    for kind in ("dp_w", "dpvs"):
        for s in SEEDS:
            d, rs = rows(kind, s)
            data[(kind, s)] = (d, rs)
            if len(rs) < 60: print(f"INCOMPLETE: {d} has {len(rs)}/60 valid rows"); res["incomplete"] = True
    if res.get("incomplete"):
        print("no decision: a run is incomplete"); json.dump(res, open(a.json, "w"), indent=1); return 1
    ids = sorted(data[("dp_w", SEEDS[0])][1])
    per_seed = {}
    diffs = np.zeros(len(ids))
    for s in SEEDS:
        m3, m4 = data[("dp_w", s)][1], data[("dpvs", s)][1]
        k3 = sum(int(m3[i]["success"]) for i in ids); k4 = sum(int(m4[i]["success"]) for i in ids)
        g = sum(1 for i in ids if m4[i]["success"] == "1" and m3[i]["success"] == "0"); l = sum(1 for i in ids if m4[i]["success"] == "0" and m3[i]["success"] == "1")
        per_seed[s] = dict(m3=k3, m4=k4, gained=g, lost=l, p_two_sided=mcnemar(g, l), p_one_sided=mcnemar(g, l, True))
        diffs += np.array([int(m4[i]["success"]) - int(m3[i]["success"]) for i in ids]) / len(SEEDS)
    d = diffs * 100
    rng = np.random.default_rng(0); signs = rng.choice([-1, 1], size=(100000, len(d)))
    obs = d.mean(); perm = (signs * d).mean(axis=1)
    p_one = (np.sum(perm >= obs - 1e-12) + 1) / 100001
    tot3 = sum(per_seed[s]["m3"] for s in SEEDS); tot4 = sum(per_seed[s]["m4"] for s in SEEDS); n = 60 * len(SEEDS)
    res.update(per_seed=per_seed, pooled=dict(m3=tot3, m4=tot4, n=n, m3_ci=wilson(tot3, n), m4_ci=wilson(tot4, n)),
               H1=dict(mean_gain_points=round(float(obs), 2), better=int((d > 0).sum()), worse=int((d < 0).sum()), ties=int((d == 0).sum()), p_one_sided=float(p_one),
                       supported=bool(obs >= GAIN and p_one <= 0.05)))
    # descriptive
    desc = {}
    for kind in ("dp_w", "dpvs"):
        off_s, off_f, yd_s, yd_f, causes = [], [], [], [], {}
        for s in SEEDS:
            dd, rs = data[(kind, s)]
            for r in rs.values():
                if r["success"] != "1": causes[r["fail_cause_auto"]] = causes.get(r["fail_cause_auto"], 0) + 1
            for o in offsets(dd, rs):
                (off_s if o["succ"] else off_f).append(o["off"])
                if o["obj"] in ELONG: (yd_s if o["succ"] else yd_f).append(o["yaw_dev"])
        med = lambda v: round(float(np.median(v)), 2) if v else None
        desc[kind] = dict(failures=causes, offset_med_success=med(off_s), offset_med_failed=med(off_f), n_success=len(off_s), n_failed=len(off_f),
                          yaw_dev_med_success=med(yd_s), yaw_dev_med_failed=med(yd_f), yaw_n_success=len(yd_s), yaw_n_failed=len(yd_f))
    diag = {}
    for s in SEEDS:
        dd, rs = data[("dpvs", s)]
        agg = {"vs_align_ticks": 0, "vs_blind_ticks": 0, "vs_wait_ticks": 0, "vs_auth_timeout": 0, "vs_fallback": 0}
        for r in rs.values():
            f = os.path.join(dd, f"trial_{int(r['trial_id']):04d}.json")
            if os.path.exists(f):
                dg = json.load(open(f)).get("diag", {})
                for k in agg: agg[k] += dg.get(k, 0)
        diag[s] = agg
    res.update(descriptive=desc, corrector_diag=diag)
    json.dump(res, open(a.json, "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
