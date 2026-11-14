#!/bin/bash
# Shared helpers for the pre-registered chains (PREREGISTRATION_G2.md): g0_cl0.sh, train_seed2000.sh, h4_dev.sh, g2_test.sh.  Source it, do not run it.
# Same watchdog/retry pattern as e16_commit.sh and e16_resume_c01.sh; plus the E16 lesson: run_arena can exit 0 without running a trial when its ACT server
# is down, so a run is only done when trials.csv has the EXPECTED number of valid rows.
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." || exit 1
ISAAC_PY="$HOME/env_isaac/bin/python"
LR_PY="$HOME/venvs/lerobot_data/bin/python"
CL0_PY="$HOME/venvs/cl0/bin/python"
mkdir -p logs

# rule 5 (arena/CLAUDE.md): test_* cells run only on the user's explicit order
need_test_order() {
    [ "${CONFIRM_TEST:-}" = "yes" ] || { echo "REFUSED: this chain runs locked test_* cells. Re-run with CONFIRM_TEST=yes only on the user's explicit order."; exit 2; }
    git diff --quiet HEAD -- PREREGISTRATION_G2.md && git ls-files --error-unmatch PREREGISTRATION_G2.md >/dev/null 2>&1 \
        || { echo "REFUSED: PREREGISTRATION_G2.md is not committed (or has local changes)"; exit 2; }
}

# rule 1: never Isaac in parallel with training (8 GB VRAM)
need_no_training() {
    if pgrep -f 'lerobot_train|train_act_i2' >/dev/null; then echo "REFUSED: a training is running (rule 1: no Isaac in parallel with training)"; exit 2; fi
}
need_no_isaac() {
    if pgrep -f 'arena.run_arena' >/dev/null; then echo "REFUSED: Isaac is running (rule 1: no training in parallel with Isaac)"; exit 2; fi
}

valid_rows() {   # trials.csv -> number of rows with valid=1
    python3 - "$1" <<'EOF'
import csv, os, sys
p = sys.argv[1]
print(sum(1 for r in csv.DictReader(open(p)) if r['valid'] == '1') if os.path.exists(p) else 0)
EOF
}

# run_until TAG OUT EXPECTED run_arena-args...   (re-runs resume; nothing is deleted)
run_until() {
    local tag=$1 out=$2 expected=$3; shift 3
    mkdir -p "$out"
    local attempt pid new age have
    for attempt in 1 2 3 4 5 6; do
        have=$(valid_rows "$out/trials.csv")
        [ "$have" -ge "$expected" ] && { echo "$(date +%T) $tag complete ($have/$expected valid)"; return 0; }
        echo "$(date +%T) $tag attempt $attempt, have $have/$expected"
        env -u PYTHONPATH -u VIRTUAL_ENV "$ISAAC_PY" -m arena.run_arena --objects sim --out "$out" --report "$@" > "logs/$(date +%F_%H%M%S)_${tag}.log" 2>&1 &
        pid=$!
        touch "$out/.watchdog"
        while kill -0 $pid 2>/dev/null; do
            sleep 30
            new=$(ls -t "$out/trials.csv" "$out/.watchdog" 2>/dev/null | head -1)
            age=$(( $(date +%s) - $(stat -c %Y "$new") ))
            if [ "$age" -gt 300 ]; then
                echo "$(date +%T) $tag stalled ${age}s, killing $pid"
                kill $pid; sleep 20; kill -9 $pid 2>/dev/null
            fi
        done
        wait $pid; echo "$(date +%T) $tag run_arena exit $? now $(valid_rows "$out/trials.csv")/$expected"
        sleep 5
    done
    echo "$(date +%T) $tag STILL INCOMPLETE: $(valid_rows "$out/trials.csv")/$expected (invalid or crashed trials: decide by hand, rule 7)"
    return 1
}

# serve_i2 PORT NAME CKPT  /  serve_j0 PORT NAME CKPT : ACT server in the LeRobot venv, serving again after every arena run.  Prints the PID.
# I2 is the pre-registered /100 mode: ACT_REPLAN=0 (= the checkpoint's n_action_steps = 100), ACT_COMMIT=0.
serve_i2() {
    ACT_CKPT=$3 ACT_REPLAN=0 ACT_COMMIT=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.act_i2:make_method \
        --name "$2" --port "$1" --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_$1.log" 2>&1 &
    echo $!
}
serve_j0() {
    ACT_CKPT=$3 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.act_lerobot:make_method \
        --name "$2" --port "$1" --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_$1.log" 2>&1 &
    echo $!
}
remote_args() { echo "--methods REMOTE --method-arg remote=localhost:$1"; }

I2_S1000=runs/act_i2_s1000/checkpoints/last/pretrained_model
I2_S2000=runs/act_i2_s2000/checkpoints/last/pretrained_model
J0_S1000=runs/act_j0_s1000/checkpoints/last/pretrained_model
J0_S2000=runs/act_j0_s2000/checkpoints/last/pretrained_model
need_ckpt() { for c in "$@"; do [ -f "$c/model.safetensors" ] || { echo "missing checkpoint $c"; exit 1; }; done; }
