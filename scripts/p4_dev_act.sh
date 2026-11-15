#!/bin/bash
# P4 DEV pipeline check (paper-dev, KE_HOACH_PAPER.md), after the ACT_W trainings: ACT_W seeds 1000/2000/3000 and ACT_old (act_i2_s1000, re-run with the
# current arena code) on dev_C2 L0.5, first 20 arrangements of arrangements/sim (paired with runs/p2_cl0_dev_c2_l05 and runs/p2_cl0w_dev_c2_l05, which
# contain the same 20).  G2 inference settings (serve_i2: ACT_REPLAN=0, ACT_COMMIT=0).  One Isaac at a time (P3 incident, PAPER_NOTES.md).  DEV only.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
COMMON="--cells dev_C2 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim"
port=7301
for spec in "act_old_s1000:runs/act_i2_s1000" "act_w_s1000:runs/act_w_s1000" "act_w_s2000:runs/act_w_s2000" "act_w_s3000:runs/act_w_s3000"; do
    name=${spec%%:*}; ck=${spec#*:}/checkpoints/last/pretrained_model
    [ -f "$ck/model.safetensors" ] || { echo "missing $ck"; continue; }
    s=$(serve_i2 $port "${name^^}" "$ck"); sleep 25
    run_until p4_dev_$name runs/p4_dev_${name}_dev_c2_l05 20 $(remote_args $port) $COMMON
    kill $s 2>/dev/null; port=$((port + 1))
done
echo "$(date +%T) DEV check done"
