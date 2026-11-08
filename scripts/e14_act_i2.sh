#!/bin/bash
# E14: ACT with interface I2 (belt-frame EE actions, relative to the EE at image time; KE_HOACH_HUONG_1.md §3.2), same demos and training budget as
# E11's ACT_J0 (100k steps, batch 8, seed 1000).  Waits for the relabel (to_lerobot_i2.py, PID $CONV_PID), trains, then two Isaac lanes (never Isaac in
# parallel with training), each with its own ACT_I2 server:
#   A: ACT_I2 on dev_C0, dev_C1 x L0, L0.25: paired with E11's ACT_J0 (runs/e11_act_dev), CL0 and ORACLE (runs/e8_real, runs/e9_clutter_real).
#   B: ACT_I2 on dev_C2 x L0, L0.25, L0.5 (L0.5 is outside the demos' speeds), then ACT_J0 on dev_C2 L0.5 for the interface contrast.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
CONV_PID=${CONV_PID:?set CONV_PID}
DS=runs/e6_demos_real/lerobot_i2
OUT=runs/act_i2_s1000
CKPT=$OUT/checkpoints/last/pretrained_model
while kill -0 "$CONV_PID" 2>/dev/null; do sleep 30; done
[ -f "$DS/meta/stats.json" ] && [ -f runs/e6_demos_real/dataset_i2_summary.json ] || { echo "$(date +%T) relabel did not finish"; exit 1; }
echo "$(date +%T) relabel done; training"
env -u PYTHONPATH "$HOME/venvs/lerobot_data/bin/python" train_act_i2.py --dataset.repo_id=local/arena_so101_oracle_i2 --dataset.root=$DS \
    --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=$OUT --job_name=act_i2_s1000 --steps=100000 --batch_size=8 \
    --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=1000 > logs/$(date +%F_%H%M%S)_e14_train_act_i2.log 2>&1
[ -f "$CKPT/model.safetensors" ] || { echo "$(date +%T) no checkpoint at $CKPT"; exit 1; }
echo "$(date +%T) training ended, checkpoint $CKPT"

run() {
    tag=$1; out=$2; shift 2
    mkdir -p "$out"
    for attempt in $(seq 1 10); do
        echo "$(date +%T) start $tag, attempt $attempt"
        env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --objects sim --n 20 --out "$out" --report "$@" > logs/$(date +%F_%H%M%S)_e14_$tag.log 2>&1 &
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
serve() {   # port module name ckpt -> ACT server in the LeRobot venv, serving again after each arena run
    ACT_CKPT=$4 env -u PYTHONPATH "$HOME/venvs/lerobot_data/bin/python" remote_server.py --factory "arena.methods.$2:make_method" \
        --name "$3" --port "$1" --path . --path ../cl0 --repeat > logs/$(date +%F_%H%M%S)_e14_server_$1.log 2>&1 &
    echo $!
}

lane_a() {
    s=$(serve 6001 act_i2 ACT_I2 $CKPT); sleep 20
    run i2_dev01 runs/e14_act_i2_dev --methods REMOTE --method-arg remote=localhost:6001 --cells dev_C0,dev_C1 --speeds L0,L0.25
    kill "$s"
}
lane_b() {
    s=$(serve 6002 act_i2 ACT_I2 $CKPT); sleep 20
    run i2_dev2 runs/e14_act_i2_dev2 --methods REMOTE --method-arg remote=localhost:6002 --cells dev_C2 --speeds L0,L0.25,L0.5
    kill "$s"
    s=$(serve 6003 act_lerobot ACT_J0 runs/act_j0_s1000/checkpoints/last/pretrained_model); sleep 20
    run j0_dev2 runs/e14_act_j0_dev2 --methods REMOTE --method-arg remote=localhost:6003 --cells dev_C2 --speeds L0.5
    kill "$s"
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
echo "$(date +%T) all done"
