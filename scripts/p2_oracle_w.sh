#!/bin/bash
# P2 (paper-dev, KE_HOACH_PAPER.md): ORACLE_W = ORACLE + W1 (wrist-roll-aware grasp-yaw branch, arena/wrist_branch.py) on the unlocked train_C2 sheet.
# Paired with the ORACLE baselines on the same 60 scenes: runs/p1_oracle_train_c2_l05 (L0.5, 41/60) and runs/p1_slip_D_l0 (L0, 50/60).  One change (W1).
# Nothing frozen is edited (cl0/ untouched; new method name).
# v1 (runs/p2_oraclew_train_c2_l0{5,}, stopped at 19/20 trials, kept): planner used the measured belt speed at selection (belt still ramping up, ~25 of
# 75 mm/s), so it under-predicted the travel and switched 1 trial instead of 16.  v2 adds the commanded speed + firmware ramp (wrist_branch.belt_travel).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
COMMON="--methods ORACLE_W --cells train_C2 --n 60 --arrangements-dir arrangements/sim"
( run_until p2_W1v2_l05 runs/p2_oraclew2_train_c2_l05 60 $COMMON --speeds L0.5 ) > >(sed -u 's/^/A /') &
pa=$!; sleep 20
( run_until p2_W1v2_l0 runs/p2_oraclew2_train_c2_l0 60 $COMMON --speeds L0 ) > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
