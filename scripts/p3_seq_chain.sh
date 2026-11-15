#!/bin/bash
# P3 again with ONE Isaac at a time (15/11 21:xx): with two demo-recording lanes both Isaac processes stalled together again and again from 19:42 on
# (logs/2026-11-15_171351_p2p3_chain.log; trials normal at ~60 s, then a 310 s trial, then no progress at all after restarts) [suspected: shared VRAM
# exhausted by two rendering processes, not verified].  Resumes runs/p3_demos_w_{a,b} (nothing deleted), logs VRAM every 60 s, converts only a complete
# set, then trains ACT_W x3 (scripts/p2p3_chain.sh step 4).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
export RUN_UNTIL_ATTEMPTS=60                      # single-lane stalls recur (~every 30-60 min, CPU-side, GPU idle); keep resuming
export RUN_UNTIL_STALL_S=200                      # stall = omni.replicator orchestrator.step hang (SIGUSR1 stacks 22:04); trials take 40-65 s, longest legit ~40 s virtual x 5
VL="logs/$(date +%F_%H%M%S)_p3_vram.log"
( while true; do echo "$(date +%T) $(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader | tr -d '\n') | $(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr '\n' ' ')"; sleep 60; done ) > "$VL" 2>&1 &
VP=$!
trap 'kill $VP 2>/dev/null' EXIT
C="--methods ORACLE_W --arrangements-dir arrangements/sim_ext --speeds L0,L0.25,L0.5 --n 70"
run_until p3_demos_a runs/p3_demos_w_a 420 $C --cells train_C0,train_C1 --record-demos runs/p3_demos_w_a/episodes
run_until p3_demos_b runs/p3_demos_w_b 420 $C --cells train_C2,train_C3 --record-demos runs/p3_demos_w_b/episodes
echo "$(date +%T) episodes: a $(ls runs/p3_demos_w_a/episodes | grep -c npz), b $(ls runs/p3_demos_w_b/episodes | grep -c npz)"
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
for SEED in 1000 2000 3000; do
    OUT=runs/act_w_s$SEED
    [ -f $OUT/checkpoints/last/pretrained_model/model.safetensors ] && continue
    echo "$(date +%T) train ACT_W seed $SEED"
    env -u PYTHONPATH "$LR_PY" train_act_i2.py --dataset.repo_id=local/arena_so101_oraclew_i2 --dataset.root=$DS \
        --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=$OUT --job_name=act_w_s$SEED --steps=100000 --batch_size=8 \
        --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=$SEED > "logs/$(date +%F_%H%M%S)_train_act_w_s$SEED.log" 2>&1 || { echo "training $SEED failed"; exit 1; }
    sha256sum $OUT/checkpoints/last/pretrained_model/model.safetensors
done
echo "$(date +%T) chain done"
