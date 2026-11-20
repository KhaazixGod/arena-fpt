#!/bin/bash
# Source it.  m4_wait_gpu: returns when the M4 chain may start.
#  default            : no arena.run_arena process and no other arena-* unit running (arena-m4* excluded).
#  GPU_SHARE=1        : start NEXT TO ONE other Isaac (lane B of the P8 TEST chain) as soon as lane A of that chain has finished (its last run runs/p8_test_c2_l05_p17_odil_w_t has 60 valid
#                       rows, or the P8 unit is gone), at most one Isaac is running and at least GPU_SHARE_MIN_FREE_MB (default 3800) of VRAM are free, for 10 checks of 60 s in a row
#                       (so that a pause between two runs of lane A is not mistaken for the end of the lane).  Measured: one Isaac 2.2 GB, ACT server 0.5 GB, desktop 1.3 GB.
m4_wait_gpu() {
    if [ "${GPU_SHARE:-}" = "1" ]; then
        local ok=0 n free a
        echo "$(date +%T) GPU_SHARE: waiting for lane A of P8 to finish and >= ${GPU_SHARE_MIN_FREE_MB:-3800} MiB free"
        while :; do
            n=$(pgrep -fc 'arena.run_arena'); free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
            a=$(valid_rows runs/p8_test_c2_l05_p17_odil_w_t/trials.csv)
            if [ "$n" -le 1 ] && [ "$free" -ge "${GPU_SHARE_MIN_FREE_MB:-3800}" ] && { [ "$a" -ge 60 ] || ! systemctl --user is-active -q arena-p8test; }; then ok=$((ok + 1)); else ok=0; fi
            [ "$a" -ge 60 ] && [ "$n" -le 1 ] && [ "$free" -ge "${GPU_SHARE_MIN_FREE_MB:-3800}" ] && break     # lane A is finished: no pause to wait for
            [ $ok -ge 10 ] && break
            sleep 60
        done
        echo "$(date +%T) GPU_SHARE: go (isaac processes $n, free ${free} MiB, lane A runs valid $a)"
    else
        local busy
        busy() { pgrep -f 'arena.run_arena' >/dev/null || systemctl --user list-units 'arena-*' --state=running --no-legend 2>/dev/null | grep -v 'arena-m4' | grep -q .; }
        echo "$(date +%T) waiting for the GPU (arena.run_arena or another arena-* unit is running)"
        while busy; do sleep 60; done
        echo "$(date +%T) GPU free"
    fi
}
