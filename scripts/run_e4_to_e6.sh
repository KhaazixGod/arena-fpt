#!/bin/bash
# After the physics choice (scene.toml): E5 checks, E4 bounds, CL-0 sanity, M8 repeatability, E6 demos.  Sequential (one Isaac at a time).  Simulation only.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
PY="env -u PYTHONPATH -u VIRTUAL_ENV $HOME/env_isaac/bin/python"
log() { echo "$(date +%H:%M:%S) $*"; }
step() { tag=$1; shift; log "start $tag"; $PY "$@" > logs/$(date +%F_%H%M%S)_$tag.log 2>&1; log "end $tag exit $?"; }
step e5_sheet scripts/e5_objects_sheet.py --out runs/e5
step e5_c3 scripts/e5_c3_stability.py --out runs/e5 --cells train_C3,dev_C3
step e4_interim -m arena.run_arena --methods NOOP,ORACLE --cells dev_C0 --speeds L0,L0.25 --n 20 --out runs/e4_final_interim --report
step e4_sim -m arena.run_arena --methods NOOP,ORACLE --cells dev_C0,dev_C2 --speeds L0,L0.25 --n 20 --objects sim --out runs/e4_final_sim --report
step e4_cl0 -m arena.run_arena --methods CL0,CL0_YAW --cells dev_C0 --speeds L0,L0.25 --n 20 --out runs/e4_cl0_interim --report
log "start e3_repeat"; scripts/e3_repeat.sh 20 > logs/$(date +%F_%H%M%S)_e3_repeat_summary.log 2>&1; log "end e3_repeat"
step e6_record -m arena.run_arena --methods ORACLE --cells train_C0,train_C2 --speeds L0,L0.25 --n 15 --objects sim --out runs/e6_demos --record-demos runs/e6_demos/episodes
log "start e6_convert"; env -u PYTHONPATH ~/venvs/cl0/bin/python to_lerobot.py --episodes runs/e6_demos/episodes --root runs/e6_demos/lerobot --repo-id local/arena_so101_oracle > logs/$(date +%F_%H%M%S)_e6_convert.log 2>&1; log "end e6_convert exit $?"
log "all done"
