#!/bin/bash
# E6 on the REAL layout: expert (ORACLE) demos on the TRAIN objects, all clutter levels, belt stopped and L0.25, successes kept (target >= 400); then LeRobotDataset.
# 240 arrangements x 2 speeds = 480 trials.  Simulation only.  Waits for the PID given as $1 (one Isaac at a time).  Re-running resumes.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
[ -n "$1" ] && while kill -0 "$1" 2>/dev/null; do sleep 30; done
OUT=runs/e6_demos_real
echo "$(date +%H:%M:%S) start record"
env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --methods ORACLE --objects sim --cells train_C0,train_C1,train_C2,train_C3 --speeds L0,L0.25 --n 60 \
    --out $OUT --record-demos $OUT/episodes --report > logs/$(date +%F_%H%M%S)_e6_record_real.log 2>&1
echo "$(date +%H:%M:%S) end record exit $?; episodes: $(ls $OUT/episodes | wc -l)"
env -u PYTHONPATH "$HOME/venvs/lerobot_data/bin/python" to_lerobot.py --episodes $OUT/episodes --root $OUT/lerobot --repo-id local/arena_so101_oracle_real > logs/$(date +%F_%H%M%S)_e6_convert_real.log 2>&1
echo "$(date +%H:%M:%S) end convert exit $?"
