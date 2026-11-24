"""FINAL TEST decision script (PREREGISTRATION_FINAL.md section 5).  Reads runs/final_c2_<speed>_<block>_<kind>_s<seed>, writes runs/final_test_decision.json.
H1 (primary): at L0.5, on the scenes of the sheet for which all six DP runs (M3 and M4 v2, seeds 1000/2000/3000) are complete (120 scenes when blocks a and b are complete; if only
block a is complete the analysis is run on its 60 scenes and flagged UNDERPOWERED), the mean over the seeds of the per-scene success difference (M4 v2 - M3) is >= GAIN points and the
one-sided sign-permutation p (100,000 draws, numpy seed 0) is <= 0.05.  Everything else is descriptive."""
import argparse, csv, json, math, os, sys
import numpy as np

GAIN = 5.0
GAIN_STRONG = 10.0
SEEDS = (1000, 2000, 3000)
SPEEDS = (("l05", "L0.5 (75 mm/s)"), ("l025", "L0.25 (37.5 mm/s)"), ("l0", "L0 (0 mm/s)"))
BLOCKS = {"l05": ("a", "b"), "l025": ("a",), "l0": ("a",)}
ELONG = ("box35", "plate30", "plate31", "t34", "u27")
LOWC = ("box32", "cyl33")
RUNS = "runs"

def load(sp, blk, kind, seed):
    d = os.path.join(RUNS, f"final_c2_{sp}_{blk}_{kind}_s{seed}")
    p = os.path.join(d, "trials.csv")
    if not os.path.exists(p): return d, {}
    return d, {r["arrangement_id"]: r for r in csv.DictReader(l for l in open(p) if not l.startswith("#")) if r["valid"] == "1"}

def wilson(k, n, z=1.959964):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)

def sign_perm(d, one_sided=True, draws=100000):
    rng = np.random.default_rng(0)
    signs = rng.choice([-1, 1], size=(draws, len(d)))
    obs = d.mean(); perm = (signs * d).mean(axis=1)
    if one_sided: return float((np.sum(perm >= obs - 1e-12) + 1) / (draws + 1))
    return float((np.sum(np.abs(perm) >= abs(obs) - 1e-12) + 1) / (draws + 1))

def boot_ci(d, n=20000):
    rng = np.random.default_rng(0)
    m = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)])
    return round(float(np.percentile(m, 2.5)), 1), round(float(np.percentile(m, 97.5)), 1)

def merged(sp, kind, seed):
    """{arrangement_id: row} over the complete blocks of this speed; also the list of complete block names."""
    out, done = {}, []
    for blk in BLOCKS[sp]:
        d, rs = load(sp, blk, kind, seed)
        if len(rs) >= 60: out.update(rs); done.append(blk)
    return out, done

def main():
    global RUNS
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default="runs/final_test_decision.json"); ap.add_argument("--runs", default="runs"); a = ap.parse_args()
    RUNS = a.runs
    res = {"gain_required_points": GAIN, "gain_strong_points": GAIN_STRONG, "speeds": {}}
    for sp, label in SPEEDS:
        S = {}
        kin, kdone = merged(sp, "kin", 0)
        S["kin"] = dict(blocks=kdone, k=sum(int(r["success"]) for r in kin.values()), n=len(kin))
        for kind in ("dp_w", "dpvs2"):
            per = {}
            for s in SEEDS:
                rs, done = merged(sp, kind, s)
                per[s] = dict(blocks=done, k=sum(int(r["success"]) for r in rs.values()), n=len(rs))
            S[kind] = per
        # scenes for which every DP run is complete
        common = None
        for kind in ("dp_w", "dpvs2"):
            for s in SEEDS:
                rs, _ = merged(sp, kind, s)
                common = set(rs) if common is None else common & set(rs)
        ids = sorted(common or [])
        S["scenes_common"] = len(ids)
        if ids:
            M = {(k_, s): merged(sp, k_, s)[0] for k_ in ("dp_w", "dpvs2") for s in SEEDS}
            m3 = np.array([[int(M[("dp_w", s)][i]["success"]) for s in SEEDS] for i in ids], float)
            m4 = np.array([[int(M[("dpvs2", s)][i]["success"]) for s in SEEDS] for i in ids], float)
            d = (m4.mean(1) - m3.mean(1)) * 100
            S["m4v2_minus_m3"] = dict(mean_gain_points=round(float(d.mean()), 2), better=int((d > 0).sum()), worse=int((d < 0).sum()), ties=int((d == 0).sum()),
                                      p_one_sided=sign_perm(d), p_two_sided=sign_perm(d, False), boot95=boot_ci(d),
                                      pooled_m3=int(m3.sum()), pooled_m4v2=int(m4.sum()), n_runs=int(m3.size),
                                      wilson_m3=wilson(int(m3.sum()), m3.size), wilson_m4v2=wilson(int(m4.sum()), m4.size))
            kin_ids = [i for i in ids if i in kin]
            if len(kin_ids) == len(ids):
                kk = np.array([int(kin[i]["success"]) for i in ids], float)
                for name, arr in (("m3_minus_m1", m3.mean(1)), ("m4v2_minus_m1", m4.mean(1))):
                    dd = (arr - kk) * 100
                    S[name] = dict(mean_points=round(float(dd.mean()), 2), p_two_sided=sign_perm(dd, False), boot95=boot_ci(dd))
        res["speeds"][sp] = S
    # optional descriptive comparator: M4 v1 on L0.5 block a (scenes 1-60), seeds 1000-3000
    v1 = {}
    for s in SEEDS:
        d, rs = load("l05", "a", "dpvs", s)
        if len(rs) >= 60: v1[s] = rs
    if len(v1) == 3:
        a_ids = sorted(set.intersection(*[set(v1[s]) for s in SEEDS], *[set(load("l05", "a", k, s)[1]) for k in ("dp_w", "dpvs2") for s in SEEDS]))
        g1 = lambda rows_by_seed: np.array([[int(rows_by_seed[s][i]["success"]) for s in SEEDS] for i in a_ids], float).mean(1)
        mm = {k: g1({s: load("l05", "a", k, s)[1] for s in SEEDS}) for k in ("dp_w", "dpvs2")}
        mm["dpvs"] = g1(v1)
        out = {"scenes": len(a_ids), "pooled_v1": int(round(mm["dpvs"].sum() * 3)), "pooled_m3": int(round(mm["dp_w"].sum() * 3)), "pooled_v2": int(round(mm["dpvs2"].sum() * 3))}
        for name, (x, y) in {"v1_minus_m3": ("dpvs", "dp_w"), "v2_minus_v1": ("dpvs2", "dpvs"), "v2_minus_m3": ("dpvs2", "dp_w")}.items():
            dd = (mm[x] - mm[y]) * 100
            out[name] = dict(mean_points=round(float(dd.mean()), 2), p_two_sided=sign_perm(dd, False), boot95=boot_ci(dd))
        res["m4_v1_comparator_l05_block_a"] = out
    # H1
    S5 = res["speeds"]["l05"]; g = S5.get("m4v2_minus_m3")
    both = all(len(S5[k][s]["blocks"]) == 2 for k in ("dp_w", "dpvs2") for s in SEEDS)
    one_blk = all(len(S5[k][s]["blocks"]) >= 1 for k in ("dp_w", "dpvs2") for s in SEEDS)
    if g and one_blk:
        res["H1"] = dict(scenes=S5["scenes_common"], underpowered=not both, mean_gain_points=g["mean_gain_points"], p_one_sided=g["p_one_sided"], boot95=g["boot95"],
                         supported=bool(g["mean_gain_points"] >= GAIN and g["p_one_sided"] <= 0.05), strong=bool(g["mean_gain_points"] >= GAIN_STRONG))
    else:
        res["H1"] = dict(decision="none: the L0.5 DP runs are incomplete")
    # descriptive: failure causes, picks per object, descent speed and pushes (L0.5, all complete blocks)
    desc = {}
    for kind in ("kin", "dp_w", "dpvs2"):
        causes, picks, appear, vdown, push = {}, {}, {}, [], []
        for seed in ((0,) if kind == "kin" else SEEDS):
            for blk in BLOCKS["l05"]:
                d, rs = load("l05", blk, kind, seed)
                if len(rs) < 60: continue
                for r in rs.values():
                    if r["success"] != "1": causes[r["fail_cause_auto"]] = causes.get(r["fail_cause_auto"], 0) + 1
                    else: picks[r["target"]] = picks.get(r["target"], 0) + 1
                    tid = int(r["trial_id"])
                    fj, fg = os.path.join(d, f"trial_{tid:04d}.json"), os.path.join(d, f"trial_{tid:04d}_gt.npz")
                    if os.path.exists(fj):
                        j = json.load(open(fj))
                        for p in j.get("placements", []): appear[p["name"]] = appear.get(p["name"], 0) + 1
                        mv = (j.get("label", {}).get("details") or {}).get("moved_before_close_mm") or {}
                        if r["fail_cause_auto"] == "collision" and mv: push.append(max(mv.values()))
                    if r["success"] == "1" and kind != "kin" and os.path.exists(fg):
                        z = np.load(fg, allow_pickle=True); cols = [str(c) for c in z["columns"]]; tz = z["gt"][:, cols.index("tcp_z")]
                        i = np.where(tz < 45)[0]
                        if len(i): vdown.append(float((-np.diff(tz[max(0, i[0] - 25):i[0] + 25]) / 0.02).max()))
        med = lambda v: round(float(np.median(v)), 1) if v else None
        desc[kind] = dict(failure_causes=causes, picks_by_object=picks, appearances_by_object=appear, median_max_descent_speed_mm_s=med(vdown), n_collision=len(push),
                          median_max_displacement_collision_mm=med(push))
    res["descriptive_l05"] = desc
    json.dump(res, open(a.json, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "descriptive_l05"}, indent=1))
    print(json.dumps(res["descriptive_l05"], indent=1))
    return 0 if res["H1"].get("supported") is not None else 1

if __name__ == "__main__":
    sys.exit(main())
