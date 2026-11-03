#!/bin/bash
# User's layout and camera (scene.toml), user's goal 1/11: good and stable with many objects.  DEV cells only, simulation only.
# CL0 and ORACLE (upper bound, separates perception from the executor) on C1..C3, L0 and L0.25; then a second repetition of CL0 for the repeat check.
# Same watchdog as e6_record_400_resume.sh: no finished trial for 5 min = stalled -> kill and resume.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
[ -n "$1" ] && while kill -0 "$1" 2>/dev/null; do sleep 30; done
OUT=runs/e9_clutter_real
mkdir -p $OUT
run() {
    tag=$1; shift
    for attempt in $(seq 1 10); do
        echo "$(date +%T) start $tag, attempt $attempt"
        env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --objects sim --cells dev_C1,dev_C2,dev_C3 --speeds L0,L0.25 --n 20 --out $OUT --report "$@" > logs/$(date +%F_%H%M%S)_e9_$tag.log 2>&1 &
        pid=$!
        touch $OUT/.watchdog
        while kill -0 $pid 2>/dev/null; do
            sleep 30
            new=$(ls -t $OUT/trials.csv $OUT/.watchdog 2>/dev/null | head -1)
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
    echo "$(date +%T) gave up on $tag"; exit 1
}
run both --methods CL0,ORACLE
run repeat --methods CL0 --reps 2
echo "$(date +%T) all done"
