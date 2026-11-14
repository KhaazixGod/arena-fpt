#!/bin/bash
# P1 (paper-dev): debug videos of 3 SUCCESSFUL ORACLE trials of runs/p1_oracle_train_c2_l05 (baseline config, L0.5), to compare with the failure videos.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
for item in 4:ok_005_l13 20:ok_021_ring20 9:ok_010_t17; do
    i=${item%%:*}; tag=${item#*:}
    run_until p1_video_$tag runs/p1_video_$tag 1 --methods ORACLE --cells train_C2 --first $i --n 1 --arrangements-dir arrangements/sim --speeds L0.5 --debug-video
done
