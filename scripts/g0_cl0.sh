#!/bin/bash
# G0 (PREREGISTRATION_G2.md §0): CL0 alone.  The learned policy does not take part, so nothing leaks.
#   system check: CL0 on seen_C0 (n = 20) at L0.5, must be >= 80 %
#   decision cell: CL0 on test_C2_001..030 at L0.5 (n = 30)  [LOCKED sheet -> needs the user's explicit order]
#   CONFIRM_TEST=yes bash scripts/g0_cl0.sh
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_test_order
need_no_training

run_until g0_seen_c0 runs/g0_seen_c0 20 --methods CL0 --cells seen_C0 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim_seen || exit 1
run_until g0_test_c2 runs/g0_test_c2 30 --methods CL0 --cells test_C2 --speeds L0.5 --n 30 --arrangements-dir locked --allow-locked || exit 1
"$CL0_PY" scripts/g2_pair.py g0 | tee "logs/$(date +%F_%H%M%S)_g0_decision.txt"
