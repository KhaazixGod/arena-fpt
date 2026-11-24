#!/bin/bash
# M1 (m4v2/kin_cv_ik.py) smoke / DEV run on dev_C2, L0.5: no parameters to tune (there are none); this only checks that the baseline runs end to end and what it does.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
N=${N:-10}
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-5} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
while systemctl --user is-active -q arena-m4v2dev-b; do sleep 20; done
run_until kin_dev runs/kin_dev_dev_c2_l05 $N --methods m4v2.kin_cv_ik:make_method --cells dev_C2 --speeds L0.5 --n $N --arrangements-dir arrangements/sim
python3 - <<'PY'
import csv, json
d = "runs/kin_dev_dev_c2_l05"
rows = [r for r in csv.DictReader(l for l in open(d + "/trials.csv") if not l.startswith("#")) if r["valid"] == "1"]
print("M1 DEV:", len(rows), "valid;", "success", sum(int(r["success"]) for r in rows), "; outcomes", [r["outcome"] for r in rows], "; causes", [r["fail_cause_auto"] for r in rows if r["success"] != "1"])
PY
