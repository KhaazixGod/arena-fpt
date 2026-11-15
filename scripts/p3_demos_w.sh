#!/bin/bash
# P3 (paper-dev, KE_HOACH_PAPER.md): demos from the fixed teacher ORACLE_W on the E6 sheets (arrangements/sim_ext, train_C0..C3, first 70 each) at L0, L0.25
# and L0.5 (E6 had L0 and L0.25 only): 4 x 3 x 70 = 840 attempts, successes kept as raw episodes, then the I2 LeRobot dataset (to_lerobot_i2.py, chunk 100,
# the ACT_I2 recipe).  Two Isaac lanes (E18 ran two demo lanes at ~5.6 GB total).  Run only after the P2 gate.  Unlocked sheets; nothing frozen is edited.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
C="--methods ORACLE_W --arrangements-dir arrangements/sim_ext --speeds L0,L0.25,L0.5 --n 70"
run_until p3_demos_a runs/p3_demos_w_a 420 $C --cells train_C0,train_C1 --record-demos runs/p3_demos_w_a/episodes > >(sed -u 's/^/A /') &
pa=$!
sleep 40
run_until p3_demos_b runs/p3_demos_w_b 420 $C --cells train_C2,train_C3 --record-demos runs/p3_demos_w_b/episodes > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
echo "$(date +%T) episodes: a $(ls runs/p3_demos_w_a/episodes | grep -c npz), b $(ls runs/p3_demos_w_b/episodes | grep -c npz)"
# never convert (and never train) on an incomplete demo set: run_until gives up after 6 attempts and returns without an error code
[ "$(valid_rows runs/p3_demos_w_a/trials.csv)" -ge 420 ] && [ "$(valid_rows runs/p3_demos_w_b/trials.csv)" -ge 420 ] \
    || { echo "$(date +%T) P3 INCOMPLETE: a $(valid_rows runs/p3_demos_w_a/trials.csv)/420, b $(valid_rows runs/p3_demos_w_b/trials.csv)/420; not converting"; exit 4; }
need_no_isaac
DS=runs/p3_demos_w/lerobot_i2
if [ ! -f "$DS/meta/stats.json" ]; then
    mkdir -p runs/p3_demos_w
    env -u PYTHONPATH "$LR_PY" to_lerobot_i2.py --episodes runs/p3_demos_w_a/episodes runs/p3_demos_w_b/episodes --root $DS --repo-id local/arena_so101_oraclew_i2 \
        --chunk 100 > "logs/$(date +%F_%H%M%S)_p3_to_lerobot_i2.log" 2>&1 || { echo "convert failed"; exit 1; }
fi
echo "$(date +%T) dataset: $DS"
