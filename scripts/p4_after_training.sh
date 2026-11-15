#!/bin/bash
# Follow-up of scripts/p3_seq_chain.sh (paper-dev, KE_HOACH_PAPER.md P4); waits for it, then keeps the GPU busy, one job at a time (rule 1):
#   1. DEV check of ACT_old s1000 and ACT_W s1000/2000/3000 (scripts/p4_dev_act.sh, dev_C2 L0.5 n = 20)
#   2. ablation ACT_W_slow s1000: the ACT_W recipe on the L0/L0.25 episodes only (462 of 677, runs/p3_demos_w/ablation_slow_episodes.json), same
#      100 000 steps, same dataset stats (only the training episodes differ)
#   3. DEV check of ACT_W_slow
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
while systemctl --user is-active -q arena-p3seq; do sleep 60; done
[ -f runs/act_w_s3000/checkpoints/last/pretrained_model/model.safetensors ] || { echo "$(date +%T) ACT_W trainings incomplete; stop"; exit 4; }
bash scripts/p4_dev_act.sh || { echo "$(date +%T) DEV check failed"; exit 1; }
need_no_isaac
EPS=$(python3 -c "import json; print(json.load(open('runs/p3_demos_w/ablation_slow_episodes.json'))['episodes'])" | tr -d ' ')
if [ ! -f runs/act_w_slow_s1000/checkpoints/last/pretrained_model/model.safetensors ]; then
    echo "$(date +%T) train ACT_W_slow seed 1000 ($(python3 -c "import json; print(len(json.load(open('runs/p3_demos_w/ablation_slow_episodes.json'))['episodes']))") episodes)"
    env -u PYTHONPATH "$LR_PY" train_act_i2.py --dataset.repo_id=local/arena_so101_oraclew_i2 --dataset.root=runs/p3_demos_w/lerobot_i2 --dataset.episodes="$EPS" \
        --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=runs/act_w_slow_s1000 --job_name=act_w_slow_s1000 --steps=100000 --batch_size=8 \
        --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=1000 > "logs/$(date +%F_%H%M%S)_train_act_w_slow_s1000.log" 2>&1 || { echo "ablation training failed"; exit 1; }
    sha256sum runs/act_w_slow_s1000/checkpoints/last/pretrained_model/model.safetensors
fi
P4_MODELS="act_w_slow_s1000:runs/act_w_slow_s1000" bash scripts/p4_dev_act.sh
echo "$(date +%T) p4_after_training done"
