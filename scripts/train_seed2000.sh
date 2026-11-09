#!/bin/bash
# PREREGISTRATION_G2.md §2/§7 step 1: second training seed (2000) for ACT_I2 and ACT_J0, same recipe as the seed-1000 models
# (E6 demos only, 100 000 steps, batch 8).  ~2.5 h each; never in parallel with Isaac (rule 1).  Prints the sha256 to paste into the pre-registration.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_isaac

DS_I2=runs/e6_demos_real/lerobot_i2
DS_J0=runs/e6_demos_real/lerobot
[ -f "$DS_I2/meta/stats.json" ] && [ -f "$DS_J0/meta/stats.json" ] || { echo "missing E6 datasets"; exit 1; }

if [ ! -f "$I2_S2000/model.safetensors" ]; then
    echo "$(date +%T) train ACT_I2 seed 2000"
    env -u PYTHONPATH "$LR_PY" train_act_i2.py --dataset.repo_id=local/arena_so101_oracle_i2 --dataset.root=$DS_I2 \
        --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=runs/act_i2_s2000 --job_name=act_i2_s2000 --steps=100000 --batch_size=8 \
        --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=2000 > "logs/$(date +%F_%H%M%S)_train_act_i2_s2000.log" 2>&1
fi
if [ ! -f "$J0_S2000/model.safetensors" ]; then
    echo "$(date +%T) train ACT_J0 seed 2000"
    env -u PYTHONPATH "$LR_PY" -m lerobot.scripts.lerobot_train --dataset.repo_id=local/e6_demos_real --dataset.root=$DS_J0 \
        --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=runs/act_j0_s2000 --job_name=act_j0_s2000 --steps=100000 --batch_size=8 \
        --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=2000 > "logs/$(date +%F_%H%M%S)_train_act_j0_s2000.log" 2>&1
fi
need_ckpt "$I2_S2000" "$J0_S2000"
echo "$(date +%T) done; paste into PREREGISTRATION_G2.md section 2:"
sha256sum "$I2_S2000/model.safetensors" "$J0_S2000/model.safetensors"
