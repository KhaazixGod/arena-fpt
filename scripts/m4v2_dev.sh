#!/bin/bash
# M4 v2 DEV (thesis, 25/11/2026): the descent-release fix of m4v2/diffusion_vs2.py on dev_C2, L0.5, the same 20 scenes and DP_W seed as m4_dev.sh
# (baselines on these scenes: DP_W s1000 16/20, M4 v1 c1_default 18/20).  DEV only (rule 4).  One configuration = one run of 20 scenes.
#   CONFIGS="v2a_vd150" PORT=7701 bash scripts/m4v2_dev.sh        (two lanes: run twice with different CONFIGS and PORT, GPU_SHARE=1 on both)
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
[ "${GPU_SHARE:-}" = "1" ] || need_no_isaac
SEED=${SEED:-1000}
CK=runs/dp_w_s$SEED/checkpoints/last/pretrained_model
need_ckpt $CK
declare -A CFG=(
  [v2a_vd150]="VS2_VDESC=150"
  [v2b_vd250]="VS2_VDESC=250"
  [v2c_vd100]="VS2_VDESC=100"
  [v2d_vd150_noopen]="VS2_VDESC=150 VS2_HOLDOPEN=0"
  [v2e_pause]="VS2_MODE=pause"
)
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
port=${PORT:-7701}
for c in ${CONFIGS:-v2a_vd150}; do
    out=runs/m4v2_dev_${c}_dev_c2_l05; [ "$SEED" != 1000 ] && out=runs/m4v2_dev_${c}_s${SEED}_dev_c2_l05
    srv=$( (set -a; source m4/m4_vs.env; set +a; [ -n "${CFG[$c]}" ] && eval "export ${CFG[$c]}"
        DP_CKPT=$CK DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory diffusion_vs2:make_method --name "DPVS2_${c}_s${SEED}" \
            --port $port --path m4v2 --path m4 --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_m4v2_${c}_$port.log" 2>&1 &
        echo $!) )
    for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
    run_until "m4v2_dev_$c" "$out" 20 $(remote_args $port) --cells dev_C2 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim
    kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null
    port=$((port + 1))
done
echo "$(date +%T) M4v2 DEV done"
