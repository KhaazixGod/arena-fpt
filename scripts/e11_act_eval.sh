#!/bin/bash
# E11: ACT trained on the sim demos (runs/act_j0_s1000, joint-space actions: a pipeline check, not the thesis policy), served from ~/venvs/lerobot_data.
# Waits for the training to end (never Isaac in parallel with training).  Two Isaac lanes in parallel, each with its own ACT server:
#   A: ACT on dev_C0, dev_C1 (novel objects), paired with runs/e8_real and runs/e9_clutter_real.
#   B: ORACLE dev_C1 L0.25 n=10 first, under A's load: must equal runs/e9_clutter_real bit for bit (ORACLE is deterministic) -> parallel lanes are safe;
#      then ACT and ORACLE on seen_C0, seen_C1 (train objects, new arrangements; sim analogue of G1a).
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
TRAIN_PID=${TRAIN_PID:-342647}
CKPT=runs/act_j0_s1000/checkpoints/last/pretrained_model
while kill -0 "$TRAIN_PID" 2>/dev/null; do sleep 30; done
[ -f "$CKPT/model.safetensors" ] || { echo "$(date +%T) no checkpoint at $CKPT"; exit 1; }
echo "$(date +%T) training ended, checkpoint $CKPT"

run() {
    tag=$1; out=$2; shift 2
    mkdir -p "$out"
    for attempt in $(seq 1 10); do
        echo "$(date +%T) start $tag, attempt $attempt"
        env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --objects sim --n 20 --out "$out" --report "$@" > logs/$(date +%F_%H%M%S)_e11_$tag.log 2>&1 &
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
serve() {   # port -> ACT server in the LeRobot venv, serving again after each arena run
    ACT_CKPT=$CKPT env -u PYTHONPATH "$HOME/venvs/lerobot_data/bin/python" remote_server.py --factory arena.methods.act_lerobot:make_method \
        --name ACT_J0 --port "$1" --path . --path ../cl0 --repeat > logs/$(date +%F_%H%M%S)_e11_server_$1.log 2>&1 &
    echo $!
}

lane_a() {
    s=$(serve 6001); sleep 20
    run act_dev runs/e11_act_dev --methods REMOTE --method-arg remote=localhost:6001 --cells dev_C0,dev_C1 --speeds L0,L0.25
    kill "$s"
}
lane_b() {
    s=$(serve 6002); sleep 20
    run parallel_check runs/e11_parallel_check --methods ORACLE --cells dev_C1 --speeds L0.25 --n 10
    run act_seen runs/e11_act_seen --methods REMOTE --method-arg remote=localhost:6002 --cells seen_C0,seen_C1 --speeds L0,L0.25 --arrangements-dir arrangements/sim_seen
    run oracle_seen runs/e11_act_seen --methods ORACLE --cells seen_C0,seen_C1 --speeds L0,L0.25 --arrangements-dir arrangements/sim_seen
    kill "$s"
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
echo "$(date +%T) all done"
