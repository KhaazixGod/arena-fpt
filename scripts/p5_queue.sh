#!/bin/bash
# Paper framing (b), chosen by the user on 16/11: the executor failure mode on a moving belt (wrist-roll branch under joint limits) and its fix W1 are
# the main result; ACT/DP are learned baselines, H2 (does the fixed teacher help the student) is secondary.  GPU/Isaac queue after the ACT_W trainings
# (unit arena-p3seq); replaces arena-p4next / arena-p4dp (stopped before they ran anything).  One GPU job at a time except step 1 (two Isaac lanes without
# demo recording ran in parallel without stalls on 15/11).
#   1. W1 speed sweep on DEV (dev_C2, first n arrangements, paired with the L0.5 runs runs/p2_cl0*_dev_c2_l05): CL0 vs CL0_W and ORACLE vs ORACLE_W at
#      L1.0 (n = 60) and L0.25 (n = 30)
#   2. DEV check ACT_old s1000 + ACT_W x3 at L0.5 (scripts/p4_dev_act.sh, one lane)
#   3. Diffusion Policy: pilot, DP_W s1000, DEV (scripts/p4_dp_chain.sh)
#   4. ACT_W_slow ablation + DEV (scripts/p4_after_training.sh; its DEV re-check of step 2 is skipped as complete)
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
while systemctl --user is-active -q arena-p3seq; do sleep 60; done
[ -f runs/act_w_s3000/checkpoints/last/pretrained_model/model.safetensors ] || { echo "$(date +%T) ACT_W trainings incomplete; stop"; exit 4; }
need_no_training
D="--cells dev_C2 --arrangements-dir arrangements/sim"
lane() {   # lane ORACLE_METHOD CL0_METHOD TAGSUFFIX
    run_until p5_$3_o_l10 runs/p5_$3oracle_dev_c2_l10 60 --methods $1 $D --speeds L1.0 --n 60
    run_until p5_$3_o_l025 runs/p5_$3oracle_dev_c2_l025 30 --methods $1 $D --speeds L0.25 --n 30
    run_until p5_$3_c_l10 runs/p5_$3cl0_dev_c2_l10 60 --methods $2 $D --speeds L1.0 --n 60
    run_until p5_$3_c_l025 runs/p5_$3cl0_dev_c2_l025 30 --methods $2 $D --speeds L0.25 --n 30
}
lane ORACLE CL0 "" > >(sed -u 's/^/A /') &
pa=$!; sleep 20
lane ORACLE_W CL0_W "w" > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
python3 scripts/p2_compare.py runs/p5_oracle_dev_c2_l10 runs/p5_woracle_dev_c2_l10 runs/p5_oracle_dev_c2_l025 runs/p5_woracle_dev_c2_l025 \
    runs/p5_cl0_dev_c2_l10 runs/p5_wcl0_dev_c2_l10 runs/p5_cl0_dev_c2_l025 runs/p5_wcl0_dev_c2_l025 > "logs/$(date +%F_%H%M%S)_p5_sweep_compare.txt" 2>&1
echo "$(date +%T) speed sweep done"
bash scripts/p4_dev_act.sh || echo "$(date +%T) ACT DEV check failed (continuing)"
bash scripts/p4_dp_chain.sh || echo "$(date +%T) DP chain failed (continuing)"
bash scripts/p4_after_training.sh || echo "$(date +%T) ablation chain failed"
echo "$(date +%T) p5 queue done"
