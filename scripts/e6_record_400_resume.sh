#!/bin/bash
# E6, resumes runs/e6_demos_real after the 31/10 23:17 stall (renders went from 0.07 s to 50 s each; a process restart is the fix being tested).
# 70 arrangements per cell instead of 60 (arrangements/sim_ext: same seeds, first 60 identical) because ORACLE keeps about 76% of the train trials and 480 trials give < 400.
# Watchdog: no finished trial for 5 min = stalled -> kill and resume (run_arena skips finished keys).
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
OUT=runs/e6_demos_real
for attempt in $(seq 1 20); do
    echo "$(date +%T) start record, attempt $attempt"
    env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --methods ORACLE --objects sim --cells train_C0,train_C1,train_C2,train_C3 --speeds L0,L0.25 --n 70 \
        --arrangements-dir arrangements/sim_ext --out $OUT --record-demos $OUT/episodes --report > logs/$(date +%F_%H%M%S)_e6_record_real.log 2>&1 &
    pid=$!
    touch $OUT/.watchdog
    while kill -0 $pid 2>/dev/null; do
        sleep 30
        new=$(ls -t $OUT/trials.csv $OUT/.watchdog | head -1)
        age=$(( $(date +%s) - $(stat -c %Y "$new") ))
        if [ "$age" -gt 300 ]; then
            echo "$(date +%T) stalled ${age}s, killing $pid"
            kill "$pid"; sleep 20; kill -9 "$pid" 2>/dev/null
        fi
    done
    wait $pid; rc=$?
    echo "$(date +%T) end record, exit $rc, episodes $(ls $OUT/episodes | wc -l)"
    [ $rc -eq 0 ] && break
done
[ $rc -eq 0 ] || { echo "$(date +%T) gave up after $attempt attempts, no conversion"; exit 1; }
echo "$(date +%T) start convert"
env -u PYTHONPATH "$HOME/venvs/lerobot_data/bin/python" to_lerobot.py --episodes $OUT/episodes --root $OUT/lerobot --repo-id local/arena_so101_oracle_real > logs/$(date +%F_%H%M%S)_e6_convert_real.log 2>&1
echo "$(date +%T) end convert, exit $?"
