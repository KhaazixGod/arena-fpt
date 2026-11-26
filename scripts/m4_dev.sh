#!/bin/bash
# M4 (thesis Chapter 6) DEV tuning: DP_W seed 1000 + the corrector of m4/diffusion_vs.py on dev_C2, L0.5 (75 mm/s), the same 20 scenes as the DP_W DEV check
# (runs/p4_dev_dp_w_s1000_dev_c2_l05: 16/20).  DEV only (rule 4); nothing here touches a locked sheet.  One configuration = one run of 20 scenes (about 37 min).
#   bash scripts/m4_dev.sh                      all configurations below, in order
#   CONFIGS="c1_default c4_noauth" bash scripts/m4_dev.sh
#   WAIT_FOR_GPU=1 bash scripts/m4_dev.sh       first waits until no arena.run_arena is running (e.g. another chain), then starts
#   DRY=1 bash scripts/m4_dev.sh                prints the plan
# Every parameter change is a configuration here (one at a time vs c1_default); results: scripts/m4_dev_summary.py.  Log the outcome in ARENA_TUNING_LOG.md.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
source "$(dirname "$(readlink -f "$0")")/m4_wait.sh"
if [ "${WAIT_FOR_GPU:-}" = "1" ]; then m4_wait_gpu; fi
[ "${DRY:-}" = "1" ] || [ "${GPU_SHARE:-}" = "1" ] || need_no_isaac
SEED=${SEED:-1000}                         # DP_W seed of the checkpoint (1000 = the seed the configurations were compared on)
CK=runs/dp_w_s$SEED/checkpoints/last/pretrained_model
need_ckpt $CK

# ---- stage 0: smoke test, 3 dev scenes with the default parameters; the chain stops if the corrector did not run (detector frames, ALIGN ticks) or a trial is invalid
if [ "${DRY:-}" != "1" ] && [ "${SKIP_SMOKE:-}" != "1" ]; then
    out=runs/m4_smoke_dev_c2_l05; port=7600
    srv=$( (set -a; source m4/m4_vs.env; set +a
        DP_CKPT=$CK DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory diffusion_vs:make_method --name "DPVS_smoke" \
            --port $port --path m4 --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_m4_smoke_$port.log" 2>&1 &
        echo $!) )
    for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
    run_until m4_smoke "$out" 3 $(remote_args $port) --cells dev_C2 --speeds L0.5 --n 3 --arrangements-dir arrangements/sim
    kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null
    python3 - "$out" <<'PY' || { echo "$(date +%T) SMOKE FAILED: the chain stops here (look at $out and logs/*m4_smoke*)"; exit 1; }
import csv, json, sys
out = sys.argv[1]
rows = [r for r in csv.DictReader(open(out + "/trials.csv")) if r["valid"] == "1"]
agg = {"vs_frames": 0, "vs_align_ticks": 0, "vs_blind_ticks": 0, "vs_wait_ticks": 0, "vs_auth_timeout": 0, "vs_fallback": 0, "plans": 0}
for r in rows:
    dg = json.load(open(f"{out}/trial_{int(r['trial_id']):04d}.json")).get("diag", {})
    for k in agg: agg[k] += dg.get(k, 0)
print("smoke:", len(rows), "valid trials;", "success", sum(int(r["success"]) for r in rows), "; diag", agg, "; outcomes", [r["outcome"] for r in rows])
sys.exit(0 if len(rows) == 3 and agg["vs_frames"] > 0 and agg["plans"] > 0 else 1)
PY
fi
declare -A CFG=(
  [c1_default]=""
  [c2_nodesc]="VS_DESC=0"
  [c3_posonly]="VS_YAW=0"
  [c4_yawonly]="VS_KXY=0 VS_EPS_XY=1000 VS_EPS_DESC_XY=1000"
  [c5_noauth]="VS_AUTH=0 VS_DESC=0"
  [c6_k5]="VS_KXY=5 VS_KYAW=5"
  [c7_lam05]="VS_LAMBDA=0.5"
  [c8_tight]="VS_EPS_XY=2 VS_EPS_YAW=10 VS_EPS_DESC_XY=5 VS_EPS_DESC_YAW=20"
)
ORDER=${CONFIGS:-"c1_default c2_nodesc c3_posonly c4_yawonly c5_noauth c6_k5 c7_lam05 c8_tight"}
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
port=$((7601 + (SEED - 1000) / 10))
for c in $ORDER; do
    port=$((port + 1))
    out=runs/m4_dev_${c}_dev_c2_l05; [ "$SEED" != 1000 ] && out=runs/m4_dev_${c}_s${SEED}_dev_c2_l05
    if [ "${DRY:-}" = "1" ]; then echo "DRY $c: $(set -a; source m4/m4_vs.env; set +a; echo ${CFG[$c]}) -> $out"; continue; fi
    srv=$( (set -a; source m4/m4_vs.env; set +a; [ -n "${CFG[$c]}" ] && eval "export ${CFG[$c]}"
        DP_CKPT=$CK DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory diffusion_vs:make_method --name "DPVS_${c}_s${SEED}" \
            --port $port --path m4 --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_m4_${c}_$port.log" 2>&1 &
        echo $!) )
    for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
    run_until "m4_dev_$c" "$out" 20 $(remote_args $port) --cells dev_C2 --speeds L0.5 --n 20 --arrangements-dir arrangements/sim
    kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null
done
echo "$(date +%T) M4 DEV chain done: python3 scripts/m4_dev_summary.py"
