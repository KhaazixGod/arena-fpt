#!/bin/bash
# PREREGISTRATION_G2.md section 8, Sai lech 3: investigate the failed G0 system check (CL0 seen_C0 L0.25 = 14/20, L0.5 = 6/20).
# ORACLE (same executor, privileged perception) on the same seen_C0 sheet at L0.25 and L0.5, n = 20.  seen_C0 is NOT a locked sheet.   bash scripts/g0_investigate.sh
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
run_until g0inv_l025 runs/g0inv_oracle_seen_c0_l025 20 --methods ORACLE --cells seen_C0 --speeds L0.25 --n 20 --arrangements-dir arrangements/sim_seen > >(sed -u 's/^/A /') &
pa=$!
sleep 60
run_until g0inv_l05 runs/g0inv_oracle_seen_c0_l05 20 --methods ORACLE --cells seen_C0 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim_seen > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
