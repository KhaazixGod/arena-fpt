#!/bin/bash
# P1 (paper-dev): slip mechanism.  Paired with runs/p1_oracle_train_c2_l05 (baseline 41/60): same 60 scenes, ORACLE, L0.5, one change at a time.
# A: robot.pad_friction 1.5 -> 3.0 (scene-set)   B: z_grasp_above_belt_mm 10 -> 16   C: vmax_z 150 -> 60.   Unlocked sheet; nothing frozen is edited (configs are copies).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
COMMON="--methods ORACLE --cells train_C2 --n 60 --arrangements-dir arrangements/sim --speeds L0.5"
( run_until p1_A_fric3 runs/p1_slip_A_fric3 60 $COMMON --scene-set robot.pad_friction=3.0 ; run_until p1_C_vz60 runs/p1_slip_C_vz60 60 $COMMON --config configs/arena_p1_vz60.toml ) > >(sed -u 's/^/A /') &
pa=$!; sleep 20
( run_until p1_B_z16 runs/p1_slip_B_z16 60 $COMMON --config configs/arena_p1_z16.toml ) > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
