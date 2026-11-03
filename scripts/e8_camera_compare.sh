#!/bin/bash
# Real layout (scene.toml): bounds + CL-0; then CL-0 with the alternative camera (scene_cam_near.toml) on the same arrangements.  Simulation only.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
PY="env -u PYTHONPATH -u VIRTUAL_ENV $HOME/env_isaac/bin/python"
A="--objects sim --n 20"
run() { tag=$1; shift; echo "$(date +%H:%M:%S) start $tag"; $PY -m arena.run_arena "$@" > logs/$(date +%F_%H%M%S)_e8_$tag.log 2>&1; echo "$(date +%H:%M:%S) end $tag exit $?"; }
run real_C0  --methods NOOP,ORACLE,CL0 --cells dev_C0 --speeds L0,L0.25 $A --out runs/e8_real --report
run real_C2  --methods CL0 --cells dev_C2 --speeds L0.25 $A --out runs/e8_real --report
run near_C0  --methods CL0 --cells dev_C0 --speeds L0,L0.25 $A --out runs/e8_cam_near --scene-file configs/scene_cam_near.toml --calib-dir runs/calib_cam_near --report
run near_C2  --methods CL0 --cells dev_C2 --speeds L0.25 $A --out runs/e8_cam_near --scene-file configs/scene_cam_near.toml --calib-dir runs/calib_cam_near --report
echo "$(date +%H:%M:%S) all done"
