#!/bin/bash
# P2 confirmation (paper-dev, KE_HOACH_PAPER.md), run only after the train_C2 gate (scripts/p2_oracle_w.sh) passed:
#   1. ORACLE vs ORACLE_W on train_C3 L0.5 (a sheet W1 was not designed on), 60 scenes, paired.
#   2. CL0 vs CL0_W on dev_C2 L0.5 (CL-0 changes are judged on DEV only, arena/CLAUDE.md rule 4; CL0_W approved by the user 15/11), 60 scenes, paired.
# Unlocked sheets only; nothing frozen is edited.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
A="--cells train_C3 --n 60 --arrangements-dir arrangements/sim --speeds L0.5"
( run_until p2_oracle_c3 runs/p2_oracle_train_c3_l05 60 --methods ORACLE $A ;
  run_until p2_cl0_dev runs/p2_cl0_dev_c2_l05 60 --methods CL0 --cells dev_C2 --n 60 --arrangements-dir arrangements/sim --speeds L0.5 ) > >(sed -u 's/^/A /') &
pa=$!; sleep 20
( run_until p2_oraclew_c3 runs/p2_oraclew_train_c3_l05 60 --methods ORACLE_W $A ;
  run_until p2_cl0w_dev runs/p2_cl0w_dev_c2_l05 60 --methods CL0_W --cells dev_C2 --n 60 --arrangements-dir arrangements/sim --speeds L0.5 ) > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
python3 scripts/p2_compare.py runs/p2_oracle_train_c3_l05 runs/p2_oraclew_train_c3_l05 runs/p2_cl0_dev_c2_l05 runs/p2_cl0w_dev_c2_l05 > "logs/$(date +%F_%H%M%S)_p2_confirm_compare.txt" 2>&1
