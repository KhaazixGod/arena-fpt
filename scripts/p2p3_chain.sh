#!/bin/bash
# Overnight chain (paper-dev, KE_HOACH_PAPER.md), started only after the P2 gate on train_C2 passed:
#   1. scripts/p2_confirm.sh   ORACLE vs ORACLE_W on train_C3 L0.5; CL0 vs CL0_W on dev_C2 L0.5 (paired, 60 each)
#   2. guard                   ORACLE_W on train_C3 not worse than ORACLE by more than 2 successes, else stop before the demos
#   3. scripts/p3_demos_w.sh   ORACLE_W demos (840 attempts) -> runs/p3_demos_w/lerobot_i2
#   4. ACT_W seeds 1000, 2000, 3000: the ACT_I2 recipe (train_act_i2.py, 100 000 steps, batch 8), only the data differ
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
bash scripts/p2_confirm.sh || { echo "$(date +%T) p2_confirm failed"; exit 1; }
python3 - <<'PY' || { echo "$(date +%T) GUARD: ORACLE_W worse than ORACLE on train_C3; stop before the demos"; exit 3; }
import csv, sys
def ok(run):
    return {r["arrangement_id"]: r["success"] == "1" for r in csv.DictReader(open(run + "/trials.csv")) if r["valid"] == "1"}
b, w = ok("runs/p2_oracle_train_c3_l05"), ok("runs/p2_oraclew_train_c3_l05")
k = sorted(set(b) & set(w)); sb, sw = sum(b[x] for x in k), sum(w[x] for x in k)
print(f"guard train_C3 L0.5: ORACLE {sb}/{len(k)}, ORACLE_W {sw}/{len(k)}")
sys.exit(0 if len(k) >= 55 and sw >= sb - 2 else 1)
PY
bash scripts/p3_demos_w.sh || { echo "$(date +%T) p3 failed"; exit 1; }
need_no_isaac
DS=runs/p3_demos_w/lerobot_i2
[ -f $DS/meta/stats.json ] || { echo "$(date +%T) no complete dataset $DS; not training"; exit 4; }
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
