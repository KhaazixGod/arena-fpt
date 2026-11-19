#!/usr/bin/env python3
"""P8 decision (PREREGISTRATION_P8.md section 5): the re-implemented paper ports and P19 on the P6 TEST sheet.

    python3 scripts/p8_decide.py [--json runs/p8_test_decision.json]

F1 (Holm over 4, L0.5): ACT_W (3 seeds) vs P05_CNS_W, P07_VITVS_W, P17_ODIL_W, P19 (3 seeds); per-scene mean difference, two-sided sign-flip permutation.
F2 (Holm over 3, L0.5): CL0_W vs P05_CNS_W, P07_VITVS_W, P17_ODIL_W; exact McNemar, two-sided.
Everything else descriptive.  Statistics = scripts/p6_decide.py's (same code, imported).  A decision is printed only when every needed run is complete
(60 valid rows on the sheet's 60 arrangements, the right method/cell/speed); otherwise NO DECISION and the missing pieces.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("p6d", os.path.join(HERE, "scripts", "p6_decide.py"))
D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)        # chdir(HERE), statistics, loader
SHEET = "locked/paper/test_C2.csv"

PORTS = {"p05_cns": "P05_CNS", "p07_vitvs": "P07_VITVS", "p17_odil": "P17_ODIL"}
P19 = ["p19_s1000", "p19_s2000", "p19_s3000"]
ACT_W = ["act_w_s1000", "act_w_s2000", "act_w_s3000"]


def method_of(name: str) -> str:
    if name.startswith("p19_"):
        return "REMOTE:P19_ACT_TE_S" + name.split("_s")[-1]
    if name.startswith("act_w_"):
        return "REMOTE:" + name.upper()
    base = name[:-2] if name.endswith("_t") else name
    w = base.endswith("_w")
    return PORTS[base[:-2] if w else base] + ("_W" if w else "")


def run_dir(sp: str, name: str) -> str:
    """P6 runs for CL0_W (both speeds) and ACT_W at L0.5; P8 runs otherwise."""
    if name == "cl0_w" or (name in ACT_W and sp == "l05"):
        return f"runs/p6_test_c2_{sp}_{name}"
    return f"runs/p8_test_c2_{sp}_{name}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    ids = D.sheet_ids(SHEET)
    L = {"l05": 0.5, "l025": 0.25}
    names = {"l05": ["cl0_w"] + ACT_W + P19 + [f"{p}{w}" for p in PORTS for w in ("_w", "")] + [f"{p}_w_t" for p in PORTS],
             "l025": ["cl0_w"] + ACT_W + P19 + [f"{p}{w}" for p in PORTS for w in ("_w", "")]}
    R, problems = {}, []
    for sp, ns in names.items():
        for n in ns:
            meth = "CL0_W" if n == "cl0_w" else method_of(n)
            r = D.load(run_dir(sp, n), meth, "test_C2", L[sp], ids)
            R[(sp, n)] = r
            if r["errors"] or r["missing"]:
                problems.append(f"{sp} {n}: {len(r['ok'])}/60 valid" + (f", errors: {r['errors'][:2]}" if r["errors"] else ""))
    print("P8 TEST (PREREGISTRATION_P8.md), sheet", SHEET, "n =", len(ids), "engine=isaac\n")
    for sp in names:
        print(f"success at {sp} (Wilson 95 %):")
        for n in names[sp]:
            if R[(sp, n)]["ok"]:
                print(D.sr_line(n, R[(sp, n)], 60))
        print()
    need = [("l05", n) for n in ["cl0_w"] + ACT_W + P19 + [f"{p}_w" for p in PORTS]]
    if any(R[k]["errors"] or R[k]["missing"] for k in need):
        print("NO DECISION: incomplete runs:\n  " + "\n  ".join(problems))
        return 1
    ok = lambda sp, n: R[(sp, n)]["ok"]
    out = {"n": len(ids), "success": {f"{sp}/{n}": sum(R[(sp, n)]["ok"].values()) for (sp, n) in R if not R[(sp, n)]["missing"]}, "F1": {}, "F2": {}, "desc": {}}
    # F1
    ps, rows = {}, {}
    A = [ok("l05", s) for s in ACT_W]
    for k, B in (("P05_CNS_W", [ok("l05", "p05_cns_w")]), ("P07_VITVS_W", [ok("l05", "p07_vitvs_w")]), ("P17_ODIL_W", [ok("l05", "p17_odil_w")]),
                 ("P19 (3 seeds)", [ok("l05", s) for s in P19])):
        Dd, lc = D.seed_mean_diff(A, B, ids)
        p = D.signflip_two_sided(Dd)
        ps[k] = p; rows[k] = dict(d_pts=100.0 * Dd.sum() / (lc * len(ids)), a_better=int((Dd > 0).sum()), b_better=int((Dd < 0).sum()), tie=int((Dd == 0).sum()), p=p)
    H = D.holm(ps)
    print("F1 (Holm over 4, L0.5): ACT_W (3 seeds) vs each paper; per-scene mean difference, two-sided sign-flip permutation")
    for k, r in rows.items():
        thr, adj, rej = H[k]
        verdict = ("ACT_W better" if r["d_pts"] > 0 else "paper better") if rej else "no difference shown"
        print(f"  ACT_W vs {k:14s} d = {r['d_pts']:+6.1f} pts  (ACT_W better {r['a_better']}, paper better {r['b_better']}, tie {r['tie']})  p = {r['p']:.3g}  Holm {adj:.3g}  -> {verdict}")
        out["F1"][k] = dict(r, holm=adj, rejected=rej, verdict=verdict)
    # F2
    ps2, rows2 = {}, {}
    for k, n in (("P05_CNS_W", "p05_cns_w"), ("P07_VITVS_W", "p07_vitvs_w"), ("P17_ODIL_W", "p17_odil_w")):
        q = D.pair_single(ok("l05", "cl0_w"), ok("l05", n), ids)
        q["p"] = D.mcnemar_two_sided(q["gained"], q["lost"]); ps2[k] = q["p"]; rows2[k] = q
    H2 = D.holm(ps2)
    print("\nF2 (Holm over 3, L0.5): CL0_W vs each port with W1 (same executor, perception only); exact McNemar two-sided")
    for k, q in rows2.items():
        thr, adj, rej = H2[k]
        verdict = ("CL0_W better" if q["gap"] > 0 else "port better") if rej else "no difference shown"
        print(f"  CL0_W vs {k:12s} {q['kx']}/60 vs {q['ky']}/60  gap {q['gap']:+.1f} pts  (only CL0_W {q['gained']}, only port {q['lost']})  p = {q['p']:.3g}  Holm {adj:.3g}  -> {verdict}")
        out["F2"][k] = dict(q, holm=adj, rejected=rej, verdict=verdict)
    # descriptive
    print("\ndescriptive (no claims):")
    for sp in names:
        for p in PORTS:
            if not R[(sp, p + "_w")]["missing"] and not R[(sp, p)]["missing"]:
                q = D.pair_single(ok(sp, p + "_w"), ok(sp, p), ids); q["p"] = D.mcnemar_two_sided(q["gained"], q["lost"])
                print(f"  {sp} W1 effect {p:10s} {q['kx']} vs {q['ky']}  gap {q['gap']:+.1f}  (gained {q['gained']}, lost {q['lost']})  McNemar p = {q['p']:.3g}")
                out["desc"][f"{sp} W1 {p}"] = q
        for p in PORTS:
            if sp == "l05" and not R[(sp, p + "_w_t")]["missing"]:
                q = D.pair_single(ok(sp, p + "_w_t"), ok(sp, p + "_w"), ids); q["p"] = D.mcnemar_two_sided(q["gained"], q["lost"])
                print(f"  {sp} +test refs {p:10s} {q['kx']} vs {q['ky']}  gap {q['gap']:+.1f}  McNemar p = {q['p']:.3g}  (knows the TEST objects: labelled)")
                out["desc"][f"{sp} testrefs {p}"] = q
        if all(not R[(sp, s)]["missing"] for s in ACT_W):
            line = D.describe_pooled(f"{sp} ACT_W (3) vs CL0_W", [ok(sp, s) for s in ACT_W], [ok(sp, "cl0_w")], ids)
            print(line); out["desc"][f"{sp} ACT_W vs CL0_W"] = line.strip()
        if all(not R[(sp, s)]["missing"] for s in ACT_W + P19):
            line = D.describe_pooled(f"{sp} ACT_W (3) vs P19 (3)", [ok(sp, s) for s in ACT_W], [ok(sp, s) for s in P19], ids)
            print(line); out["desc"][f"{sp} ACT_W vs P19"] = line.strip()
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=float)
        print("\nwrote", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
