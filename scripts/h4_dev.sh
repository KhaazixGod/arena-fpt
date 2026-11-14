#!/bin/bash
# H4 (PREREGISTRATION_G2.md §5): interface I2 vs I0 (ACT_J0) at L = 1.0 (150 mm/s) on dev_C0, n = 30 (dev_C0_001..030).  DEV only: no locked cell.
# Two Isaac lanes (each with its own ACT server), CL0 and ORACLE for context.   bash scripts/h4_dev.sh
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
need_ckpt "$I2_S1000" "$I2_S2000" "$J0_S1000" "$J0_S2000"
COMMON="--cells dev_C0 --speeds L1.0 --n 30"

lane_a() {
    s=$(serve_i2 7101 ACT_I2_S1000 $I2_S1000); sleep 20
    run_until h4_i2s1000 runs/h4_i2s1000 30 $(remote_args 7101) $COMMON; kill $s
    s=$(serve_i2 7102 ACT_I2_S2000 $I2_S2000); sleep 20
    run_until h4_i2s2000 runs/h4_i2s2000 30 $(remote_args 7102) $COMMON; kill $s
    run_until h4_cl0 runs/h4_cl0 30 --methods CL0 $COMMON
}
lane_b() {
    s=$(serve_j0 7103 ACT_J0_S1000 $J0_S1000); sleep 20
    run_until h4_j0s1000 runs/h4_j0s1000 30 $(remote_args 7103) $COMMON; kill $s
    s=$(serve_j0 7104 ACT_J0_S2000 $J0_S2000); sleep 20
    run_until h4_j0s2000 runs/h4_j0s2000 30 $(remote_args 7104) $COMMON; kill $s
    run_until h4_oracle runs/h4_oracle 30 --methods ORACLE $COMMON
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
"$CL0_PY" scripts/g2_pair.py h4 | tee "logs/$(date +%F_%H%M%S)_h4_decision.txt"
