#!/bin/bash
# The static (L0) pile centred at a = -70 instead of -40: test condition only, CL-0 unchanged.  runs/e9_detect_probe: at -40, 16/20 dev_C3 piles touch the camera window edge (a about 56)
# and the detector rejects the whole merged blob.  CL0 and ORACLE on the same DEV sheets; scene.toml is not edited (--scene-set, recorded in manifest.json).  Simulation only.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
OUT=runs/e9_static70
mkdir -p $OUT
for attempt in $(seq 1 10); do
    echo "$(date +%T) start, attempt $attempt"
    env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --methods CL0,ORACLE --objects sim --cells dev_C0,dev_C1,dev_C2,dev_C3 --speeds L0 --n 20 \
        --scene-set belt.static_center_a_mm=-70 --out $OUT --report > logs/$(date +%F_%H%M%S)_e9_static70.log 2>&1 &
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
    echo "$(date +%T) end, exit $rc"
    [ $rc -eq 0 ] && break
done
echo "$(date +%T) all done"
