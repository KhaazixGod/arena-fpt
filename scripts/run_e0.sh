#!/bin/bash
# E0 end to end: three resolutions, plus a conveyor-extension run. Simulation only.  Usage: arena/scripts/run_e0.sh
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
PY="${ISAAC_PYTHON:-$HOME/env_isaac/bin/python}"
mkdir -p runs/e0 logs
for res in "640 480" "1280 720" "1920 1080"; do
  set -- $res
  env -u PYTHONPATH -u VIRTUAL_ENV timeout 900 "$PY" scripts/e0_probe.py --out runs/e0/$1x$2 --width $1 --height $2 --frames 120 \
      > logs/$(date +%F_%H%M%S)_e0_$1x$2.log 2>&1
  echo "$1x$2 exit $?"
done
env -u PYTHONPATH -u VIRTUAL_ENV timeout 900 "$PY" scripts/e0_probe.py --out runs/e0/conveyor_640x480 --width 640 --height 480 --enable-ext isaacsim.asset.gen.conveyor \
    > logs/$(date +%F_%H%M%S)_e0_conveyor.log 2>&1
echo "conveyor exit $?"
