#!/bin/bash
# P1 (paper-dev): intervention for the "jaw lands on a wide object" mechanism.  Paired with runs/p1_oracle_train_c2_l05 (41/60).
# F: gripper_open 40 -> 50 (E1 gap ~60 -> ~75 mm) and tcp_offset x -29 -> -37 (new gap centre; fixed jaw at x = 0).  grasp.gripper_w_mm stays 60 (same objects attempted).
# Also: debug video of an L-shape failure (train_C2_042, l15) at L0.5, baseline config.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
( run_until p1_F_open50 runs/p1_slip_F_open50 60 --methods ORACLE --cells train_C2 --n 60 --arrangements-dir arrangements/sim --speeds L0.5 --config configs/arena_p1_open50.toml ) > >(sed -u 's/^/F /') &
pa=$!; sleep 20
( run_until p1_video_042 runs/p1_video_042 1 --methods ORACLE --cells train_C2 --first 41 --n 1 --arrangements-dir arrangements/sim --speeds L0.5 --debug-video ) > >(sed -u 's/^/V /') &
pb=$!
wait $pa $pb
