#!/bin/bash
# P4 Diffusion Policy (paper-dev, KE_HOACH_PAPER.md), after scripts/p4_after_training.sh (waits for unit arena-p4next).  One GPU/Isaac job at a time.
#   1. timing pilot: DP_W (LeRobot 0.6.1 defaults: n_obs 2, horizon 64, n_action_steps 32, resnet18, UNet 512-1024-2048, DDPM 100) on the ORACLE_W
#      demos, 1500 steps, batch 16 -> s/step
#   2. DP_W seed 1000, steps = what fits in ~4 h at the measured rate (capped 100 000), saved every 20 000 steps
#   3. DEV check of DP_W s1000 (dev_C2 L0.5 n = 20, the ACT DEV scenes), DP_REPLAN = n_action_steps
# Stops there: seeds 2000/3000 only after the DEV check was looked at.  Defaults, no tuning; DEV only.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
while systemctl --user is-active -q arena-p4next; do sleep 60; done
need_no_isaac
DS=runs/p3_demos_w/lerobot_i2
COMMON="--dataset.repo_id=local/arena_so101_oraclew_i2 --dataset.root=$DS --policy.type=diffusion --policy.device=cuda --policy.push_to_hub=false --batch_size=16 --log_freq=100 --wandb.enable=false"
if [ ! -f runs/dp_pilot/pilot_done ]; then
    echo "$(date +%T) DP timing pilot"
    env -u PYTHONPATH "$LR_PY" train_dp_i2.py $COMMON --output_dir=runs/dp_pilot/run --job_name=dp_pilot --steps=1500 --save_freq=100000 --seed=1 \
        > "logs/$(date +%F_%H%M%S)_dp_pilot.log" 2>&1 || { echo "DP pilot failed"; exit 1; }
    touch runs/dp_pilot/pilot_done
fi
PL=$(ls -t logs/*_dp_pilot.log | head -1)
SPS=$(python3 - "$PL" <<'PY'
import re, sys
v = [float(m.group(1)) for m in re.finditer(r"updt_s:([0-9.]+)", open(sys.argv[1]).read())]
d = [float(m.group(1)) for m in re.finditer(r"data_s:([0-9.]+)", open(sys.argv[1]).read())]
v, d = v[len(v) // 3:], d[len(d) // 3:]            # skip warm-up
print(f"{(sum(v) / len(v)) + (sum(d) / len(d)):.4f}")
PY
)
STEPS=$(python3 -c "print(min(100000, int(4 * 3600 / max($SPS, 1e-3)) // 1000 * 1000))")
echo "$(date +%T) DP pilot: $SPS s/step (update + data) -> DP_W s1000 with $STEPS steps"
if [ ! -f runs/dp_w_s1000/checkpoints/last/pretrained_model/model.safetensors ]; then
    env -u PYTHONPATH "$LR_PY" train_dp_i2.py $COMMON --output_dir=runs/dp_w_s1000 --job_name=dp_w_s1000 --steps=$STEPS --save_freq=20000 --seed=1000 \
        > "logs/$(date +%F_%H%M%S)_train_dp_w_s1000.log" 2>&1 || { echo "DP training failed"; exit 1; }
    sha256sum runs/dp_w_s1000/checkpoints/last/pretrained_model/model.safetensors
fi
need_no_training
CK=runs/dp_w_s1000/checkpoints/last/pretrained_model
DP_CKPT=$CK env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.diffusion_i2:make_method --name DP_W_S1000 --port 7401 --path . --path ../cl0 --repeat \
    > "logs/$(date +%F_%H%M%S)_server_7401.log" 2>&1 &
SRV=$!; sleep 30
run_until p4_dev_dp_w_s1000 runs/p4_dev_dp_w_s1000_dev_c2_l05 20 $(remote_args 7401) --cells dev_C2 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim
kill $SRV 2>/dev/null
echo "$(date +%T) DP chain done (seed 1000 only; review before seeds 2000/3000)"
