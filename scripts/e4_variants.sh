#!/bin/bash
# E4: ORACLE on 20 dev_C0 arrangements at L0.25 under physics variants (all [assumptions], see scene.toml).  Simulation only.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
PY="$HOME/env_isaac/bin/python"
B="--scene-set robot.pad_friction=1.5 --scene-set robot.torsional_patch_radius_mm=5 --scene-set objects.torsional_patch_radius_mm=5"
declare -A V
V[B_fric15_tors5]="$B"
V[C_B_iters32]="$B --scene-set objects.solver_pos_iters=32 --scene-set objects.solver_vel_iters=4 --scene-set robot.solver_pos_iters=32 --scene-set robot.solver_vel_iters=4"
V[D_B_grip90]="$B --scene-set robot.gripper_max_vel_deg_s=90"
for tag in B_fric15_tors5 C_B_iters32 D_B_grip90; do
  env -u PYTHONPATH -u VIRTUAL_ENV "$PY" -m arena.run_arena --methods ORACLE --cells dev_C0 --speeds L0.25 --n 20 --out runs/e4/var_$tag ${V[$tag]} > logs/$(date +%F_%H%M%S)_e4_var_$tag.log 2>&1
  python3 -c "
import csv
rs=list(csv.DictReader(open('runs/e4/var_$tag/trials.csv')))
print('$tag', sum(int(r['success']) for r in rs), '/', len(rs), 'fails', [(r['arrangement_id'][-3:], r['outcome']) for r in rs if r['success']=='0'])"
done
