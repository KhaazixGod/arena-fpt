#!/bin/bash
# P1 (paper-dev): slip mechanism, round 2.  Paired with runs/p1_oracle_train_c2_l05 (baseline 41/60 at L0.5).
# D: same 60 scenes, belt STOPPED (L0).   E: L0.5 with robot.torsional_patch_radius_mm 5 -> 12 (pivot about the pad axis).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
COMMON="--methods ORACLE --cells train_C2 --n 60 --arrangements-dir arrangements/sim"
( run_until p1_D_l0 runs/p1_slip_D_l0 60 $COMMON --speeds L0 ) > >(sed -u 's/^/D /') &
pa=$!; sleep 20
( run_until p1_E_tors12 runs/p1_slip_E_tors12 60 $COMMON --speeds L0.5 --scene-set robot.torsional_patch_radius_mm=12 ) > >(sed -u 's/^/E /') &
pb=$!
wait $pa $pb
