"""P2 gate (KE_HOACH_PAPER.md): a W1 run paired with its ORACLE baseline on the same scenes.

    python3 scripts/p2_compare.py BASE_RUN W1_RUN [BASE_RUN W1_RUN ...]

Per pair: success (trials.csv, valid rows, the GT labeler's verdict), lost/gained on the same arrangement, exact McNemar p (two-sided), outcomes, and
the executor's held commands: consecutive identical joint commands in APPROACH..LIFT (with a moving belt the command changes every tick unless the IK
holds it, cl0/executor.py _ik_cmd).  "roll-held" counts the held ticks whose wrist roll sits at its margin (|q5 - (limit -/+ margin)| < 1 deg).
At L0 the command is constant once the arm has settled, so held ticks are not a freeze signal there (printed for completeness).
W1 rows also report how many attempts W1 moved to another branch (w1_branch events) and how they ended.
"""
import ast
import csv
import json
import math
import os
import sys
from collections import Counter

LO5, HI5, MARGIN = -157.2, 162.8, 3.0          # wrist roll limits of the SO-101 URDF (cl0/kinematics.py) and robot.joint_margin_deg (arena.toml)


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def load(run: str):
    rows = {}
    for r in csv.DictReader(open(os.path.join(run, "trials.csv"))):
        if r["valid"] != "1":
            continue
        key = (r["arrangement_id"], r["speed_mm_s"])
        rows[key] = r
    return rows


def trial_info(run: str, r: dict) -> dict:
    """held ticks, roll-held ticks and the w1_branch event of one trial (files trial_NNNN.json / _log.csv next to trials.csv)."""
    tid = r["trial_id"]
    base = os.path.join(run, f"trial_{int(tid):04d}") if tid.isdigit() else None
    if base is None or not os.path.exists(base + ".json"):
        cand = [f for f in os.listdir(run) if f.startswith("trial_") and f.endswith(".json") and not f.endswith("_gt.json")]
        base = None
        for f in cand:
            j = json.load(open(os.path.join(run, f)))
            if j.get("arrangement_id") == r["arrangement_id"] and str(j.get("speed_mm_s")) == r["speed_mm_s"]:
                base = os.path.join(run, f[:-5])
                break
    info = dict(held=0, roll_held=0, w1=None)
    if base is None:
        return info
    j = json.load(open(base + ".json"))
    info["w1"] = next((e["data"] for e in j.get("events", []) if e["name"] == "w1_branch"), None)
    prev = None
    if os.path.exists(base + "_log.csv"):
        for x in csv.DictReader(open(base + "_log.csv")):
            if x["phase"] in ("APPROACH", "DESCEND", "CLOSE", "LIFT") and x["qc"]:
                qc = tuple(ast.literal_eval(x["qc"]))
                if prev is not None and qc == prev:
                    info["held"] += 1
                    if min(abs(qc[4] - (LO5 + MARGIN)), abs(qc[4] - (HI5 - MARGIN))) < 1.0:
                        info["roll_held"] += 1
                prev = qc
            else:
                prev = None
    return info


def compare(base_run: str, w_run: str) -> None:
    B, W = load(base_run), load(w_run)
    keys = sorted(set(B) & set(W))
    sb = sum(B[k]["success"] == "1" for k in keys)
    sw = sum(W[k]["success"] == "1" for k in keys)
    lost = [k for k in keys if B[k]["success"] == "1" and W[k]["success"] != "1"]
    gained = [k for k in keys if B[k]["success"] != "1" and W[k]["success"] == "1"]
    speed = keys[0][1] if keys else "?"
    print(f"\n== {w_run}  vs  {base_run}   (speed {speed} mm/s, paired n = {len(keys)}; valid rows base {len(B)}, W1 {len(W)})")
    print(f"  success  base {sb}/{len(keys)} = {100 * sb / max(len(keys), 1):.1f}%   W1 {sw}/{len(keys)} = {100 * sw / max(len(keys), 1):.1f}%")
    print(f"  paired   W1 lost {len(lost)}, gained {len(gained)}; exact McNemar p = {mcnemar_exact(len(lost), len(gained)):.4f}")
    print(f"  lost:   {[k[0] for k in lost]}")
    print(f"  gained: {[k[0] for k in gained]}")
    for name, run, R in (("base", base_run, B), ("W1", w_run, W)):
        oc = Counter(R[k]["outcome"] for k in keys)
        fc = Counter((R[k].get("fail_cause_auto") or R[k].get("fail_cause") or "-") for k in keys if R[k]["success"] != "1")
        info = {k: trial_info(run, R[k]) for k in keys}
        n_freeze = sum(1 for k in keys if info[k]["held"] >= 10)
        n_roll = sum(1 for k in keys if info[k]["roll_held"] >= 1)
        print(f"  {name:4s} outcomes {dict(oc)}")
        print(f"       fail causes {dict(fc)}")
        print(f"       trials with >= 10 held ticks: {n_freeze}; with a held tick at the wrist-roll margin: {n_roll}; "
              f"held ticks total {sum(i['held'] for i in info.values())}")
        if name == "W1":
            sw_keys = [k for k in keys if info[k]["w1"] and info[k]["w1"].get("switched")]
            if any(info[k]["w1"] is not None for k in keys):
                tab = Counter((B[k]["success"], W[k]["success"]) for k in sw_keys)
                print(f"       W1 switched branch in {len(sw_keys)} trials: base->W1 success "
                      f"1->1 {tab[('1', '1')]}, 0->1 {tab[('0', '1')]}, 1->0 {tab[('1', '0')]}, 0->0 {tab[('0', '0')]}")
                print(f"       switched: {[k[0] for k in sw_keys]}")
                same = [k for k in keys if k not in sw_keys]
                tab2 = Counter((B[k]["success"], W[k]["success"]) for k in same)
                print(f"       not switched ({len(same)}): 1->1 {tab2[('1', '1')]}, 0->1 {tab2[('0', '1')]}, 1->0 {tab2[('1', '0')]}, 0->0 {tab2[('0', '0')]}"
                      "  (same code path as the base: changes here are run-to-run noise)")
                ms = [info[k]["w1"]["ms"] for k in keys if info[k]["w1"]]
                print(f"       planner wall time per attempt: median {sorted(ms)[len(ms) // 2]:.0f} ms, max {max(ms):.0f} ms")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or len(a) % 2:
        sys.exit(__doc__)
    for i in range(0, len(a), 2):
        compare(a[i], a[i + 1])
