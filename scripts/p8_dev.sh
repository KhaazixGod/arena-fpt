#!/bin/bash
# P8 DEV (paper-dev, exploratory; BEFORE PREREGISTRATION_P8.md): the paper front-ends re-implemented in ports/ (P05 CNS, P07 ViT-VS, P17 ODIL) and P19
# (= LeRobot ACT on the E6 demos, the benchmark's recipe: ACT_J0 checkpoints + temporal ensembling 0.01), on DEV sheets only.  Nothing locked is run.
#   0. reference views (REFCAP, belt stopped): train+dev objects -> runs/p8_refs/train_dev (main reference set); test objects -> runs/p8_refs/testobj
#      (only for the labelled "+ test references" variant).  Rendering an object alone is not a TEST trial.
#   1. smoke with video: 2 trials (dev_C0, L0) per port, W1 variants and P19 s1000 -> runs/p8_smoke_* (look at videos/)
#   2. the P7 grid (dev_C0, dev_C2 x 10 x L0, L0.25 = 40 pairs): P05_CNS, P07_VITVS, P17_ODIL (CL-0's executor without W1, as the benchmark ran them) and
#      P19 s1000/s2000/s3000 -> compared with the benchmark machine's numbers by scripts/p7_bench_compare.py (runs/p7_bench_dev_p*: "(here)" rows)
#   3. dev_C2 L0.5 n 20 (the P4 DEV cell): the three ports with and without W1, P19 x3, and CL0_W again (must reproduce runs/p2_cl0w_dev_c2_l05
#      outcome for outcome on these 20: the new code must not change the environment)
# Two Isaac lanes.  Never with training (rule 1).  Re-running resumes.  DRY=1 prints the plan; SMOKE_ONLY=1 stops after steps 0-1 (look at the videos first).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
PORTS_PY="$HOME/venvs/ports/bin/python"
STOP=runs/p8_dev_STOP
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
GRID7="--cells dev_C0,dev_C2 --n 10 --speeds L0,L0.25"
GRID5="--cells dev_C2 --n 20 --speeds L0.5"
SMOKE="--cells dev_C0 --n 2 --speeds L0 --video"
[ "${DRY:-}" = "1" ] || need_no_training
[ -f $STOP ] && { echo "NOT STARTED: $STOP exists (an earlier run exceeded 10 % valid=0)"; exit 3; }

invalid_share_ok() {
    python3 - "$1/trials.csv" <<'EOF'
import csv, os, sys
p = sys.argv[1]
rows = list(csv.DictReader(open(p))) if os.path.exists(p) else []
bad = sum(r["valid"] != "1" for r in rows)
print(f"  valid=0 rows: {bad}/{len(rows)}")
sys.exit(1 if rows and bad / len(rows) > 0.10 else 0)
EOF
}
run() {   # run OUT N run_arena-args...   -> 0 complete, 1 incomplete, 3 stop
    local out=$1 n=$2; shift 2
    local tag=$(basename "$out") rc
    [ -f $STOP ] && return 3
    if [ "${DRY:-}" = "1" ]; then echo "DRY $tag ($n): run_arena --objects sim $*"; return 0; fi
    run_until "$tag" "$out" "$n" "$@"; rc=$?
    if ! invalid_share_ok "$out"; then echo "$(date +%T) $tag: more than 10 % valid=0, STOP (rule 7)"; echo "$tag $(date -Is)" >> $STOP; return 3; fi
    return $rc
}
detector() {   # detector KIND PORT REFS -> PID of the server (P07 needs torch: the LeRobot venv)
    local py=$PORTS_PY; [ "$1" = p07_vitvs ] && py=$LR_PY
    env -u PYTHONPATH "$py" ports/detector_server.py --detector "$1" --refs "$3" --port "$2" --repeat > "logs/$(date +%F_%H%M%S)_p8det_$1_$2.log" 2>&1 &
    echo $!
}
p19_server() {   # p19_server SEED PORT -> PID
    ACT_CKPT=runs/act_j0_s$1/checkpoints/last/pretrained_model ACT_TE_COEFF=0.01 env -u PYTHONPATH "$LR_PY" remote_server.py \
        --factory arena.methods.act_lerobot:make_method --name "P19_ACT_TE_S$1" --port "$2" --path . --path ../cl0 --repeat \
        > "logs/$(date +%F_%H%M%S)_p8_p19_s$1_$2.log" 2>&1 &
    echo $!
}
wait_port() { local i; for i in $(seq 1 120); do ss -ltn "sport = :$1" | grep -q LISTEN && return 0; sleep 2; done; return 1; }
with_server() {   # with_server PID PORT -- run ...   (kills the server afterwards)
    local srv=$1 port=$2 rc; shift 3
    if [ "${DRY:-}" = "1" ]; then "$@"; return 0; fi
    wait_port "$port" || { echo "$(date +%T) server on $port did not start"; kill "$srv" 2>/dev/null; return 1; }
    sleep 3
    "$@"; rc=$?
    kill "$srv" 2>/dev/null; sleep 3; kill -9 "$srv" 2>/dev/null
    return $rc
}
port_run() {   # port_run OUT N METHOD KIND PORT REFS [extra run_arena args]   (P17 needs --depth; it is given to every port run, harmless for RGB ones)
    local out=$1 n=$2 meth=$3 kind=$4 port=$5 refs=$6; shift 6
    local srv=0; [ "${DRY:-}" = "1" ] || srv=$(detector "$kind" "$port" "$refs")
    with_server "$srv" "$port" -- run "$out" "$n" --methods "$meth" --method-arg detector=localhost:$port --depth "$@"
}
p19_run() {   # p19_run OUT N SEED PORT [args]
    local out=$1 n=$2 seed=$3 port=$4; shift 4
    local srv=0; [ "${DRY:-}" = "1" ] || srv=$(p19_server "$seed" "$port")
    with_server "$srv" "$port" -- run "$out" "$n" $(remote_args "$port") "$@"
}
step() { "$@"; local rc=$?; [ $rc -eq 3 ] && return 3; [ $rc -ne 0 ] && echo "$(date +%T) INCOMPLETE (resume later): $*"; return 0; }

refs() {   # reference views, one lane, before anything else
    local d
    for d in train_dev testobj; do
        local cells=refs_train,refs_dev n=20; [ $d = testobj ] && cells=refs_testobj n=10
        local exp=26; [ $d = testobj ] && exp=10
        local out=runs/p8_refs/run_$d views=runs/p8_refs/$d
        if [ "${DRY:-}" = "1" ]; then echo "DRY refs $d: REFCAP $cells -> $views"; continue; fi
        [ "$(ls $views/*.json 2>/dev/null | wc -l)" -ge $exp ] && continue
        run "$out" $exp --methods REFCAP --method-arg refcap_out=$views --depth --arrangements-dir arrangements/p8_refs --cells $cells --n $n --speeds L0 \
            --t-limit 3 || return
        [ "$(ls $views/*.json 2>/dev/null | wc -l)" -ge $exp ] || { echo "$(date +%T) refs $d: $(ls $views/*.json 2>/dev/null | wc -l)/$exp views"; return 1; }
    done
}

R=runs/p8_refs/train_dev
lane_a() {
    step port_run runs/p8_smoke_p05_w 2 P05_CNS_W p05_cns 7701 $R $SMOKE || return
    step port_run runs/p8_smoke_p07_w 2 P07_VITVS_W p07_vitvs 7702 $R $SMOKE || return
    [ "${SMOKE_ONLY:-}" = 1 ] && return
    step port_run runs/p7_bench_dev_p05_cns 40 P05_CNS p05_cns 7703 $R $GRID7 || return
    step port_run runs/p7_bench_dev_p07_vitvs 40 P07_VITVS p07_vitvs 7704 $R $GRID7 || return
    step port_run runs/p7_bench_dev_p17_odil 40 P17_ODIL p17_odil 7705 $R $GRID7 || return
    step port_run runs/p8_dev_p05_cns 20 P05_CNS p05_cns 7706 $R $GRID5 || return
    step port_run runs/p8_dev_p05_cns_w 20 P05_CNS_W p05_cns 7707 $R $GRID5 || return
    step port_run runs/p8_dev_p07_vitvs 20 P07_VITVS p07_vitvs 7708 $R $GRID5 || return
    step port_run runs/p8_dev_p07_vitvs_w 20 P07_VITVS_W p07_vitvs 7709 $R $GRID5 || return
    step port_run runs/p8_dev_p17_odil 20 P17_ODIL p17_odil 7710 $R $GRID5 || return
    step port_run runs/p8_dev_p17_odil_w 20 P17_ODIL_W p17_odil 7711 $R $GRID5 || return
    step p19_run runs/p7_bench_dev_p19_act_te_s3000 40 3000 7712 $GRID7 || return     # balances the lanes
}
lane_b() {
    step port_run runs/p8_smoke_p17_w 2 P17_ODIL_W p17_odil 7751 $R $SMOKE || return
    step p19_run runs/p8_smoke_p19_s1000 2 1000 7752 $SMOKE || return
    [ "${SMOKE_ONLY:-}" = 1 ] && return
    step run runs/p8_dev_cl0_w 20 --methods CL0_W $GRID5 || return
    step p19_run runs/p7_bench_dev_p19_act_te_s1000 40 1000 7753 $GRID7 || return
    step p19_run runs/p7_bench_dev_p19_act_te_s2000 40 2000 7754 $GRID7 || return
    step p19_run runs/p8_dev_p19_s1000 20 1000 7756 $GRID5 || return
    step p19_run runs/p8_dev_p19_s2000 20 2000 7757 $GRID5 || return
    step p19_run runs/p8_dev_p19_s3000 20 3000 7758 $GRID5 || return
}

for s in 1000 2000 3000; do [ "${DRY:-}" = "1" ] || need_ckpt runs/act_j0_s$s/checkpoints/last/pretrained_model; done
echo "$(date '+%F %T') P8 DEV start: HEAD $(git rev-parse --short HEAD)$(git diff --quiet HEAD || echo ' (+ local changes)')"
refs || { echo "$(date +%T) reference views incomplete: stop"; exit 1; }
[ "${DRY:-}" = "1" ] || nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader -l 60 > "logs/$(date +%F_%H%M%S)_p8_vram.log" 2>&1 &
vram=$!
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
kill $vram 2>/dev/null
echo "$(date '+%F %T') P8 DEV chain done"
