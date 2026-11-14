#!/bin/bash
# G2 (PREREGISTRATION_G2.md §3-§4): the claim-C test on the LOCKED novel-object sheets, L0.5.   CONFIRM_TEST=yes bash scripts/g2_test.sh
#   decision cell test_C2, n = 60: ACT_I2 seed 1000, ACT_I2 seed 2000, CL0, ORACLE
#   descriptive test_C0 / test_C3, n = 30: ACT_I2 seed 1000, CL0, ORACLE
# The simulation has no order effects (hard reset before every trial, M8), so the real-robot interleaving (first_method) is not needed here.
# Run it only after: G0 done, seed-2000 checkpoints and their sha256 written into PREREGISTRATION_G2.md and committed, H4/H4b finished.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_test_order
need_no_training
need_ckpt "$I2_S1000" "$I2_S2000"
grep -q 'act_i2_s2000: *[0-9a-f]\{64\}' PREREGISTRATION_G2.md || { echo "REFUSED: seed-2000 sha256 not written into PREREGISTRATION_G2.md section 2 (and committed)"; exit 2; }
LK="--arrangements-dir locked --allow-locked --speeds L0.5"

lane_a() {
    s=$(serve_i2 7201 ACT_I2_S1000 $I2_S1000); sleep 20
    run_until g2_c2_i2s1000 runs/g2_test_c2_i2s1000 60 $(remote_args 7201) --cells test_C2 --n 60 $LK
    run_until g2_c0_i2s1000 runs/g2_test_c0_i2s1000 30 $(remote_args 7201) --cells test_C0 --n 30 $LK
    run_until g2_c3_i2s1000 runs/g2_test_c3_i2s1000 30 $(remote_args 7201) --cells test_C3 --n 30 $LK
    kill $s
    run_until g2_c2_cl0 runs/g2_test_c2_cl0 60 --methods CL0 --cells test_C2 --n 60 $LK
    run_until g2_c0_cl0 runs/g2_test_c0_cl0 30 --methods CL0 --cells test_C0 --n 30 $LK
    run_until g2_c3_cl0 runs/g2_test_c3_cl0 30 --methods CL0 --cells test_C3 --n 30 $LK
}
lane_b() {
    s=$(serve_i2 7202 ACT_I2_S2000 $I2_S2000); sleep 20
    run_until g2_c2_i2s2000 runs/g2_test_c2_i2s2000 60 $(remote_args 7202) --cells test_C2 --n 60 $LK; kill $s
    run_until g2_c2_oracle runs/g2_test_c2_oracle 60 --methods ORACLE --cells test_C2 --n 60 $LK
    run_until g2_c0_oracle runs/g2_test_c0_oracle 30 --methods ORACLE --cells test_C0 --n 30 $LK
    run_until g2_c3_oracle runs/g2_test_c3_oracle 30 --methods ORACLE --cells test_C3 --n 30 $LK
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
"$CL0_PY" scripts/g2_pair.py g2 | tee "logs/$(date +%F_%H%M%S)_g2_decision.txt"
env -u PYTHONPATH "$CL0_PY" scripts/e16_failure_modes.py \
    G2_I2=runs/g2_test_c2_i2s1000:REMOTE:ACT_I2_S1000 G2_CL0=runs/g2_test_c2_cl0:CL0 G2_ORACLE=runs/g2_test_c2_oracle:ORACLE > "logs/$(date +%F_%H%M%S)_g2_failure_modes.txt" 2>&1
