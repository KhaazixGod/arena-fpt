#!/bin/bash
# P1 (paper-dev): debug videos, one per remaining ORACLE failure type of runs/p1_oracle_train_c2_l05 (baseline config, L0.5, unlocked train_C2).
# Runs after the train_C2_042 video of p1_open50.sh is done, so at most 2 Isaac processes run at once.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
until [ "$(valid_rows runs/p1_video_042/trials.csv)" -ge 1 ]; do sleep 20; done
# idx:label  (idx = 0-based row of train_C2)
for item in 14:015_cyl11_empty_grasp 46:047_cyl08_dropped 7:008_cyl09_drop_in_transfer 29:030_l14_hold_complete_fail 17:018_ring20_dropped 27:028_t17_ik_fail 3:004_box04_late; do
    i=${item%%:*}; tag=${item#*:}
    run_until p1_video_$tag runs/p1_video_$tag 1 --methods ORACLE --cells train_C2 --first $i --n 1 --arrangements-dir arrangements/sim --speeds L0.5 --debug-video
done
