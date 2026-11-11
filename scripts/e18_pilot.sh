#!/bin/bash
# E18 step B (KE_HOACH_TASKS.md §4): expert gate.  TASK_EXPERT on pilot_T (40 tasks x 5 scenes, NOT the train or test scenes), no rendering, two lanes.
#   bash scripts/e18_pilot.sh        -> logs/*_e18_gate.txt  (a task passes with >= 4/5)
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
T="--objects tasks --tasks --methods TASK_EXPERT --cells pilot_T"
run_until e18_pilot_a runs/e18_pilot_a 100 $T --first 0 --n 100 > >(sed -u 's/^/A /') &
pa=$!
sleep 40
run_until e18_pilot_b runs/e18_pilot_b 100 $T --first 100 --n 100 > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
python3 scripts/e18_summary.py gate runs/e18_pilot_a runs/e18_pilot_b | tee "logs/$(date +%F_%H%M%S)_e18_gate.txt"
