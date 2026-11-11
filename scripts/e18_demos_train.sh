#!/bin/bash
# E18 steps D-E (KE_HOACH_TASKS.md §4): TASK_EXPERT demos on train_T (32 TRAIN tasks x 25 scenes; successes kept), I2 relabel + task code, then
# ACT_I2T training (100 000 steps, batch 8, seed 1000, same recipe as ACT_I2).  Isaac first, training after (rule 1).
#   bash scripts/e18_demos_train.sh [cell]      (default cell train_T; after the gate it may be train_T_gated)
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
CELL=${1:-train_T}
N=$("$CL0_PY" -c "import json;print(len(json.load(open('arrangements/tasks/$CELL.json'))['items']))")
H=$(( (N + 1) / 2 ))
T="--objects tasks --tasks --methods TASK_EXPERT --cells $CELL"
run_until e18_demos_a runs/e18_demos_a $H $T --first 0 --n $H --record-demos runs/e18_demos_a/episodes > >(sed -u 's/^/A /') &
pa=$!
sleep 40
run_until e18_demos_b runs/e18_demos_b $(( N - H )) $T --first $H --n $(( N - H )) --record-demos runs/e18_demos_b/episodes > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
python3 scripts/e18_summary.py table runs/e18_demos_a runs/e18_demos_b > "logs/$(date +%F_%H%M%S)_e18_demos_summary.txt"
echo "$(date +%T) episodes: $(ls runs/e18_demos_a/episodes runs/e18_demos_b/episodes | grep -c npz)"
need_no_isaac
DS=runs/e18_demos/lerobot_i2t
if [ ! -f "$DS/meta/stats.json" ]; then
    mkdir -p runs/e18_demos
    env -u PYTHONPATH "$LR_PY" to_lerobot_i2.py --episodes runs/e18_demos_a/episodes runs/e18_demos_b/episodes --root $DS --repo-id local/arena_so101_tasks_i2t \
        --task-vec --chunk 100 > "logs/$(date +%F_%H%M%S)_e18_to_lerobot.log" 2>&1 || { echo "convert failed"; exit 1; }
fi
if [ ! -f runs/act_i2t_s1000/checkpoints/last/pretrained_model/model.safetensors ]; then
    echo "$(date +%T) train ACT_I2T seed 1000"
    env -u PYTHONPATH "$LR_PY" train_act_i2.py --dataset.repo_id=local/arena_so101_tasks_i2t --dataset.root=$DS \
        --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=runs/act_i2t_s1000 --job_name=act_i2t_s1000 --steps=100000 --batch_size=8 \
        --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=1000 > "logs/$(date +%F_%H%M%S)_e18_train_act_i2t.log" 2>&1 || { echo "training failed"; exit 1; }
fi
echo "$(date +%T) done; sha256 for PREREGISTRATION_E18.md:"
sha256sum runs/act_i2t_s1000/checkpoints/last/pretrained_model/model.safetensors
