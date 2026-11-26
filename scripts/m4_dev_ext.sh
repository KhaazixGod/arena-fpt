#!/bin/bash
# DEV extension (not pre-registered, no tuning): dev_C2 scenes FIRST+1..FIRST+20 (default FIRST=20: scenes 21-40; FIRST=40: scenes 41-60), which were never used to choose or ablate anything.  M3 (DP_W) and M4 (default parameters of m4/m4_vs.env, as locked)
# for the DP_W seeds 1000, 2000, 3000, L0.5; 6 runs of 20 scenes (about 40 min each).  Outputs runs/m4_dev2_{dp_w,dpvs}_s<seed>_dev_c2_l05.  Interruptible and resumable (run_until).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
[ "${GPU_SHARE:-}" = "1" ] || need_no_isaac
FIRST=${FIRST:-20}; TAG=${TAG:-dev2}
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
port=$((7650 + FIRST))
for s in ${SEEDS:-1000 2000 3000}; do
    ck=runs/dp_w_s$s/checkpoints/last/pretrained_model; need_ckpt $ck
    for kind in dp_w dpvs; do
        port=$((port + 1)); out=runs/m4_${TAG}_${kind}_s${s}_dev_c2_l05
        if [ $kind = dpvs ]; then
            srv=$( (set -a; source m4/m4_vs.env; set +a; DP_CKPT=$ck DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory diffusion_vs:make_method --name "DPVS_DEV2_S$s" \
                --port $port --path m4 --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_m4dev2_${kind}_$port.log" 2>&1 & echo $!) )
        else
            srv=$( (DP_CKPT=$ck DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.diffusion_i2:make_method --name "DPW_DEV2_S$s" \
                --port $port --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_m4dev2_${kind}_$port.log" 2>&1 & echo $!) )
        fi
        for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
        run_until "m4_${TAG}_${kind}_s$s" "$out" 20 $(remote_args $port) --cells dev_C2 --speeds L0.5 --first $FIRST --n 20 --arrangements-dir arrangements/sim
        kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null
    done
done
echo "$(date +%T) M4 DEV extension done"
