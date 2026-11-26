#!/bin/bash
# Real-time check (thesis Section 8.8, 26/11/2026): DEV only (rule 4), dev_C2 first 20 scenes, L0.5, DP_W seed 1000, the same scenes and checkpoint as the lockstep DEV runs
# (lockstep references on these scenes: M3 16/20 runs/p4_dev_dp_w_s1000_dev_c2_l05, M4 v2 16/20 runs/m4v2_dev_v2b_vd250_dev_c2_l05).
#   emu_*   : fptros.emulated: the lockstep arena behaves as if chunk sampling (~0.55 s) and detection (~36 ms) ran asynchronously on the measured hardware (EMU_SCALE=2: a machine half as fast)
#   ros2_*  : the policy served through ROS 2 (fptros.policy_node <-> fptros.client), lockstep, to show that the transport does not change the behaviour and to time every message
#   CONFIGS="emu_m3_x1 emu_m4v2_x1" PORT=7901 GPU_SHARE=1 bash scripts/rt_dev.sh      (two lanes: different CONFIGS and PORT)
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
[ "${GPU_SHARE:-}" = "1" ] || need_no_isaac
SEED=${SEED:-1000}
CK=runs/dp_w_s$SEED/checkpoints/last/pretrained_model
need_ckpt $CK
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-600}
port=${PORT:-7901}
for c in ${CONFIGS:-emu_m3_x1}; do
    out=runs/rt_dev_${c}_dev_c2_l05
    case $c in
        emu_m3_*)    fac="fptros.emulated:make_dp";    paths="--path . --path ../cl0";                      vs=0 ;;
        emu_m4v2_*)  fac="fptros.emulated:make_dpvs2"; paths="--path m4v2 --path m4 --path . --path ../cl0"; vs=1 ;;
        ros2_m4v2)   fac="diffusion_vs2:make_method";  paths="--path m4v2 --path m4 --path . --path ../cl0"; vs=1 ;;
        *) echo "unknown config $c"; exit 1 ;;
    esac
    scale=1.0; case $c in *_x2) scale=2.0 ;; esac
    if [ "$c" = ros2_m4v2 ]; then
        set +u; source /opt/ros/jazzy/setup.bash; set -u 2>/dev/null
        srv=$( (set -a; source m4/m4_vs.env; source m4v2/m4v2.env; set +a
            DP_CKPT=$CK DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH PYTHONPATH=.:../cl0 "$LR_PY" -m fptros.policy_node --factory $fac $paths > "logs/$(date +%F_%H%M%S)_policy_node_$c.log" 2>&1 &
            echo $!) )
        sleep 20
        args="--methods fptros.client:make_method"
    else
        srv=$( (set -a; source m4/m4_vs.env; [ $vs = 1 ] && source m4v2/m4v2.env; set +a; export EMU_SCALE=$scale
            DP_CKPT=$CK DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory $fac --name "RT_${c}_s${SEED}" \
                --port $port $paths --repeat > "logs/$(date +%F_%H%M%S)_server_rt_${c}_$port.log" 2>&1 &
            echo $!) )
        for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
        args=$(remote_args $port)
    fi
    run_until "rt_dev_$c" "$out" 20 $args --cells dev_C2 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim
    kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null
    port=$((port + 1))
done
echo "$(date +%T) RT DEV done"
