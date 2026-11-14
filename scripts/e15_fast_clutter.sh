#!/bin/bash
# E15: ACT_I2 on fast belt x clutter (user, 6/11: "tốc độ cao và nhiều vật").  DEV cells only; TEST (arrangements/locked) untouched.
# Phase 1, two Isaac lanes:
#   A: ORACLE demos on train_C2, train_C3 at L0.5 (60 arrangements each, successes kept) -> relabel ALL demos (E6 + these) in the background;
#      CL0 + ORACLE on dev_C3 L0.5 (missing baseline); ACT_I2 (runs/act_i2_s1000, replan 100) on dev_C3 x L0.25, L0.5.
#   B: ACT_I2 with replan every 10 frames (ACT_REPLAN=10) on dev_C2, dev_C3 x L0.25, L0.5.
# Phase 2: train runs/act_i2f_s1000 on all demos, same budget as act_i2_s1000 (100k steps, batch 8, seed 1000): only the data differ.
# Phase 3: replan chosen BEFORE seeing phase 3 (rule fixed here): 10 if ACT_I2 replan 10 >= replan 100 summed over dev_C2 L0.5, dev_C3 L0.25,
#          dev_C3 L0.5, else 100.  Then the new policy on dev_C2, dev_C3 x L0.25, L0.5.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
OLD=runs/act_i2_s1000/checkpoints/last/pretrained_model
NEW_OUT=runs/act_i2f_s1000
NEW=$NEW_OUT/checkpoints/last/pretrained_model
DS=runs/e15_demos_fast/lerobot_i2_all
ISAAC_PY="$HOME/env_isaac/bin/python"
LR_PY="$HOME/venvs/lerobot_data/bin/python"

run() {
    tag=$1; out=$2; shift 2
    mkdir -p "$out"
    for attempt in $(seq 1 10); do
        echo "$(date +%T) start $tag, attempt $attempt"
        env -u PYTHONPATH -u VIRTUAL_ENV "$ISAAC_PY" -m arena.run_arena --objects sim --n 20 --out "$out" --report "$@" > logs/$(date +%F_%H%M%S)_e15_$tag.log 2>&1 &
        pid=$!
        touch "$out/.watchdog"
        while kill -0 $pid 2>/dev/null; do
            sleep 30
            new=$(ls -t "$out/trials.csv" "$out/.watchdog" 2>/dev/null | head -1)
            age=$(( $(date +%s) - $(stat -c %Y "$new") ))
            if [ "$age" -gt 300 ]; then
                echo "$(date +%T) stalled ${age}s, killing $pid"
                kill "$pid"; sleep 20; kill -9 "$pid" 2>/dev/null
            fi
        done
        wait $pid; rc=$?
        echo "$(date +%T) end $tag, exit $rc"
        [ $rc -eq 0 ] && return 0
    done
    echo "$(date +%T) gave up on $tag"; return 1
}
serve() {   # port name ckpt replan -> ACT_I2 server in the LeRobot venv, serving again after each arena run
    ACT_CKPT=$3 ACT_REPLAN=$4 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.act_i2:make_method \
        --name "$2" --port "$1" --path . --path ../cl0 --repeat > logs/$(date +%F_%H%M%S)_e15_server_$1.log 2>&1 &
    echo $!
}

# ---------------------------------------------------------------- phase 1
lane_a() {
    run rec_fast runs/e15_demos_fast --methods ORACLE --cells train_C2,train_C3 --speeds L0.5 --n 60 --record-demos runs/e15_demos_fast/episodes
    echo "$(date +%T) demos: $(ls runs/e15_demos_fast/episodes | wc -l); relabel in background"
    env -u PYTHONPATH "$LR_PY" to_lerobot_i2.py --episodes runs/e6_demos_real/episodes runs/e15_demos_fast/episodes --root $DS --chunk 100 \
        > logs/$(date +%F_%H%M%S)_e15_to_lerobot_i2.log 2>&1 &
    echo $! > runs/e15_demos_fast/.relabel_pid
    run base_c3_fast runs/e15_base_c3_l05 --methods CL0,ORACLE --cells dev_C3 --speeds L0.5
    s=$(serve 6101 ACT_I2 $OLD 0); sleep 20
    run i2_r100_c3 runs/e15_i2_r100 --methods REMOTE --method-arg remote=localhost:6101 --cells dev_C3 --speeds L0.25,L0.5
    kill "$s"
}
lane_b() {
    s=$(serve 6102 ACT_I2_R10 $OLD 10); sleep 20
    run i2_r10 runs/e15_i2_r10 --methods REMOTE --method-arg remote=localhost:6102 --cells dev_C2,dev_C3 --speeds L0.25,L0.5
    kill "$s"
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
RP=$(cat runs/e15_demos_fast/.relabel_pid 2>/dev/null)
[ -n "$RP" ] && while kill -0 "$RP" 2>/dev/null; do sleep 30; done
[ -f "$DS/meta/stats.json" ] && [ -f runs/e15_demos_fast/dataset_i2_summary.json ] || { echo "$(date +%T) relabel did not finish"; exit 1; }
echo "$(date +%T) phase 1 done; relabel done"

# ---------------------------------------------------------------- phase 2 (no Isaac while training)
env -u PYTHONPATH "$LR_PY" train_act_i2.py --dataset.repo_id=local/arena_so101_oracle_i2_all --dataset.root=$DS \
    --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=$NEW_OUT --job_name=act_i2f_s1000 --steps=100000 --batch_size=8 \
    --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=1000 > logs/$(date +%F_%H%M%S)_e15_train_act_i2f.log 2>&1
[ -f "$NEW/model.safetensors" ] || { echo "$(date +%T) no checkpoint at $NEW"; exit 1; }
echo "$(date +%T) training ended, checkpoint $NEW"

# ---------------------------------------------------------------- phase 3
REPLAN=$(python3 - <<'EOF'
import csv
def tot(paths, method, cells):
    n = 0
    for p in paths:
        for r in csv.DictReader(open(p)):
            if r['method'] == method and r['valid'] == '1' and (r['cell'], r['L']) in cells:
                n += r['success'] == '1'
    return n
cells = {('dev_C2', '0.5'), ('dev_C3', '0.25'), ('dev_C3', '0.5')}
r10 = tot(['runs/e15_i2_r10/trials.csv'], 'REMOTE:ACT_I2_R10', cells)
r100 = tot(['runs/e14_act_i2_dev2/trials.csv', 'runs/e15_i2_r100/trials.csv'], 'REMOTE:ACT_I2', cells)
print(10 if r10 >= r100 else 100)
EOF
)
echo "$(date +%T) replan for the new policy: $REPLAN"
lane_c() {
    s=$(serve 6103 ACT_I2F $NEW $REPLAN); sleep 20
    run i2f_c2 runs/e15_i2f --methods REMOTE --method-arg remote=localhost:6103 --cells dev_C2 --speeds L0.25,L0.5
    kill "$s"
}
lane_d() {
    s=$(serve 6104 ACT_I2F $NEW $REPLAN); sleep 20
    run i2f_c3 runs/e15_i2f_c3 --methods REMOTE --method-arg remote=localhost:6104 --cells dev_C3 --speeds L0.25,L0.5
    kill "$s"
}
lane_c > >(sed -u 's/^/C /') &
pc=$!
sleep 60
lane_d > >(sed -u 's/^/D /') &
pd=$!
wait $pc $pd
echo "$(date +%T) all done"
