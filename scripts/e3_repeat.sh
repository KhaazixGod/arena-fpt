#!/bin/bash
# E3 / M8: does a trial's result depend only on the trial (repeatability), or also on the trials run before it (order)?
# Same plan four times: plain order / shuffled order, without / with --hard-reset.  ORACLE (no rendering) keeps it fast.  Simulation only.
#   arena/scripts/e3_repeat.sh [n_arrangements]
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
PY="$HOME/env_isaac/bin/python"; N=${1:-20}
common="--methods ORACLE --cells dev_C0 --speeds L0,L0.25 --n $N"
for v in "plain:--no-hard-reset" "shuffled:--no-hard-reset --shuffle-seed 1" "hard:" "hard_shuffled:--shuffle-seed 1"; do   # hard reset is the run_arena default since 30/10
  tag=${v%%:*}; extra=${v#*:}
  env -u PYTHONPATH -u VIRTUAL_ENV "$PY" -m arena.run_arena $common --out runs/e3_repeat/$tag $extra > logs/$(date +%F_%H%M%S)_e3_repeat_$tag.log 2>&1
  echo "$tag exit $?"
done
R=runs/e3_repeat
for pair in "plain shuffled" "hard hard_shuffled" "plain hard"; do
  set -- $pair
  env -u PYTHONPATH ~/venvs/cl0/bin/python -c "
import sys; sys.path.insert(0, '.')
from arena.report import read_rows, compute
r = compute(read_rows('$R/$1/trials.csv'), 'CL0', read_rows('$R/$2/trials.csv'))['repeat']
print('$1 vs $2:', r['same_success'], '/', r['pairs'], 'same success,', r['same_outcome'], '/', r['pairs'], 'same outcome; differing:', [(d['arrangement_id'][-3:], d['L']) for d in r['differing']])"
done
