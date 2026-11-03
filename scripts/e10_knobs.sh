#!/bin/bash
# Two knobs outside the original CL-0, one at a time, DEV only, simulation only (user agreed 2/11).  Baselines: runs/e8_real (dev_C0), runs/e9_clutter_real (C1..C3).
# Then the thesis speed L0.5 on dev_C2 for the baseline, both knobs and ORACLE, which had not been measured on this layout.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
run() {
    tag=$1; out=$2; shift 2
    mkdir -p "$out"
    for attempt in $(seq 1 10); do
        echo "$(date +%T) start $tag, attempt $attempt"
        env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --objects sim --n 20 --out "$out" --report "$@" > logs/$(date +%F_%H%M%S)_e10_$tag.log 2>&1 &
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
    echo "$(date +%T) gave up on $tag"; exit 1
}
ALL="--cells dev_C0,dev_C1,dev_C2,dev_C3 --speeds L0,L0.25"
run yawlocal runs/e10_yawlocal --methods CL0 $ALL --config configs/arena_yawlocal.toml
run watershed runs/e10_watershed --methods CL0 $ALL --config configs/arena_watershed.toml
# At a = -40 the detector rejects a blob touching the window edge BEFORE splitting (runs/e10_probe_watershed), so watershed also gets the static piles at a = -70; baseline runs/e9_static70.
run watershed_s70 runs/e10_watershed_s70 --methods CL0 --cells dev_C2,dev_C3 --speeds L0 --config configs/arena_watershed.toml --scene-set belt.static_center_a_mm=-70
L05="--cells dev_C2 --speeds L0.5"
run base_L05 runs/e10_base_L05 --methods CL0,ORACLE $L05
run yawlocal_L05 runs/e10_yawlocal --methods CL0 $L05 --config configs/arena_yawlocal.toml
run watershed_L05 runs/e10_watershed --methods CL0 $L05 --config configs/arena_watershed.toml
echo "$(date +%T) all done"
