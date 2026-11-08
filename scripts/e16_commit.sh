#!/bin/bash
# E16: closed-loop inference for ACT_I2, NO retraining (runs/act_i2_s1000, the model of E14/E15 /100 and /10).
# Diagnosis (scripts/e16_failure_modes.py, ARENA_SETUP_REPORT.md E16): replan every 100 frames -> across-belt bias -9 mm at the close, 60 % of failures close on nothing;
# replan every 10 frames -> bias 0 but the arm lifts before the jaws have closed (dwell 0.20 s vs 0.72 s) .  COMMIT = replan every 10 frames while the policy's OWN
# gripper command is open; once it commands close, follow that chunk to its end (n_action_steps frames).  Open 40 / close 0 in the demos, threshold 20.
# Cells (dev only; TEST untouched), n = 20 each, same arrangements as the /100 and /10 runs:
#   A: dev_C2, dev_C3 x L0.25, L0.5     B: dev_C0, dev_C1 x L0 (where ACT_I2 /100 is worse than J0 and CL0), then a REPEAT of /100 on dev_C2 L0.5 = noise floor of ACT
# PRE-REGISTERED adoption rule (before the first trial): COMMIT is the default ACT-I2 inference mode iff pooled successes over the four dev_C2/dev_C3 cells >= /100 + 5
# (/100 = 48 -> 53 of 80) AND >= /10 (39); otherwise /100 stays.  scripts/e16_pair.py evaluates it.  Two Isaac lanes in parallel (checked safe in E11); no training running.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
CKPT=runs/act_i2_s1000/checkpoints/last/pretrained_model
ISAAC_PY="$HOME/env_isaac/bin/python"
LR_PY="$HOME/venvs/lerobot_data/bin/python"

run() {
    tag=$1; out=$2; shift 2
    mkdir -p "$out"
    for attempt in $(seq 1 10); do
        echo "$(date +%T) start $tag, attempt $attempt"
        env -u PYTHONPATH -u VIRTUAL_ENV "$ISAAC_PY" -m arena.run_arena --objects sim --n 20 --out "$out" --report "$@" > logs/$(date +%F_%H%M%S)_e16_$tag.log 2>&1 &
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
serve() {   # port name replan commit -> ACT_I2 server in the LeRobot venv, serving again after each arena run
    ACT_CKPT=$CKPT ACT_REPLAN=$3 ACT_COMMIT=$4 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.act_i2:make_method \
        --name "$2" --port "$1" --path . --path ../cl0 --repeat > logs/$(date +%F_%H%M%S)_e16_server_$1.log 2>&1 &
    echo $!
}

lane_a() {
    s=$(serve 6201 ACT_I2_COMMIT 10 1); sleep 20
    run commit_c23 runs/e16_commit_c23 --methods REMOTE --method-arg remote=localhost:6201 --cells dev_C2,dev_C3 --speeds L0.25,L0.5
    kill "$s"
}
lane_b() {
    s=$(serve 6202 ACT_I2_COMMIT 10 1); sleep 20
    run commit_c01 runs/e16_commit_c01 --methods REMOTE --method-arg remote=localhost:6202 --cells dev_C0,dev_C1 --speeds L0
    kill "$s"
    s=$(serve 6203 ACT_I2_REP 0 0); sleep 20
    run repeat_r100 runs/e16_repeat_r100 --methods REMOTE --method-arg remote=localhost:6203 --cells dev_C2 --speeds L0.5
    kill "$s"
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
echo "$(date +%T) all done"
env -u PYTHONPATH "$HOME/venvs/cl0/bin/python" scripts/e16_pair.py > logs/$(date +%F_%H%M%S)_e16_pair.txt 2>&1
env -u PYTHONPATH "$HOME/venvs/cl0/bin/python" scripts/e16_failure_modes.py COMMIT=runs/e16_commit_c23:REMOTE:ACT_I2_COMMIT COMMIT=runs/e16_commit_c01:REMOTE:ACT_I2_COMMIT > logs/$(date +%F_%H%M%S)_e16_failure_modes_after.txt 2>&1
echo "$(date +%T) summaries written"
