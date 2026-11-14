#!/bin/bash
# PREREGISTRATION_G2.md section 8, Sai lech 1: replacement G0 system check.
#   CL0 on seen_C0 (arrangements/sim_seen, NOT a locked sheet), L0.25, n = 20, must be >= 16/20.   bash scripts/g0_syscheck_l025.sh
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
run_until g0_syscheck_l025 runs/g0_syscheck_seen_c0_l025 20 --methods CL0 --cells seen_C0 --speeds L0.25 --n 20 --arrangements-dir arrangements/sim_seen || exit 1
python3 - <<'EOF' | tee "logs/$(date +%F_%H%M%S)_g0_syscheck_l025.txt"
import glob, json
n = s = bad = 0
for f in sorted(glob.glob("runs/g0_syscheck_seen_c0_l025/trial_*.json")):
    d = json.load(open(f))
    if d.get("valid", 1) == 0:
        bad += 1
        continue
    n += 1
    s += int(d["label"]["success"])
print(f"G0 system check (replacement) CL0 seen_C0 L0.25: {s}/{n} valid, invalid rows {bad}")
print("PASS (>= 16/20)" if n == 20 and s >= 16 else "FAIL or INCOMPLETE: technical fault, investigate calibration on DEV before G2")
EOF
