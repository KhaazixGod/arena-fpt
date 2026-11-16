#!/bin/bash
# Overnight queue 17/11 (paper-dev, framing b), after the DP seed-1000 DEV check (16/20, works as intended, config unchanged):
#   1. ORACLE vs ORACLE_W on dev_C2 L0.5 n = 60 (completes the DEV speed table; two lanes, no rendering)
#   2. DP_W seeds 2000 and 3000: the seed-1000 recipe exactly (UNet 256-512-1024, batch 16, 82 000 steps), each followed by its DEV check
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
D="--cells dev_C2 --arrangements-dir arrangements/sim --speeds L0.5 --n 60"
( run_until p6_oracle_dev runs/p5_oracle_dev_c2_l05 60 --methods ORACLE $D ) > >(sed -u 's/^/A /') &
pa=$!; sleep 20
( run_until p6_oraclew_dev runs/p5_woracle_dev_c2_l05 60 --methods ORACLE_W $D ) > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
python3 scripts/p2_compare.py runs/p5_oracle_dev_c2_l05 runs/p5_woracle_dev_c2_l05 > "logs/$(date +%F_%H%M%S)_p6_oracle_dev_l05_compare.txt" 2>&1
need_no_isaac
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
DS=runs/p3_demos_w/lerobot_i2
port=7402
for SEED in 2000 3000; do
    OUT=runs/dp_w_s$SEED
    if [ ! -f $OUT/checkpoints/last/pretrained_model/model.safetensors ]; then
        echo "$(date +%T) train DP_W seed $SEED"
        env -u PYTHONPATH "$LR_PY" train_dp_i2.py --dataset.repo_id=local/arena_so101_oraclew_i2 --dataset.root=$DS --policy.type=diffusion --policy.down_dims=[256,512,1024] \
            --policy.device=cuda --policy.push_to_hub=false --batch_size=16 --log_freq=100 --wandb.enable=false --output_dir=$OUT --job_name=dp_w_s$SEED \
            --steps=82000 --save_freq=20000 --seed=$SEED > "logs/$(date +%F_%H%M%S)_train_dp_w_s$SEED.log" 2>&1 || { echo "DP training $SEED failed"; exit 1; }
        sha256sum $OUT/checkpoints/last/pretrained_model/model.safetensors
    fi
    need_no_training
    DP_CKPT=$OUT/checkpoints/last/pretrained_model env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.diffusion_i2:make_method --name DP_W_S$SEED \
        --port $port --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_$port.log" 2>&1 &
    SRV=$!; sleep 30
    run_until p6_dev_dp_w_s$SEED runs/p4_dev_dp_w_s${SEED}_dev_c2_l05 20 $(remote_args $port) --cells dev_C2 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim
    kill $SRV 2>/dev/null; port=$((port + 1))
    need_no_isaac
done
echo "$(date +%T) p6 queue done"
