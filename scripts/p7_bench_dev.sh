#!/bin/bash
# P7 (exploratory, NOT pre-registered): every learned policy of the paper and the modular methods on the DEV grid of the 30-paper benchmark
# (../../Benmark_Capstone, arena-fpt 4963d40 = an ancestor of this HEAD with the same objects_sim.json, scene.toml and arrangements/sim sheets):
#   cells dev_C0, dev_C2 (first 10 arrangements each) x speeds L0, L0.25  ->  40 trials per method, the exact 40 (arrangement, speed) pairs on which the
#   benchmark ran CL0, ORACLE, P05, P07, P17, P18, P19.  DEV only: no locked sheet, no --allow-locked (arena/CLAUDE.md rule 5 does not apply).
#   WAIT_P6=1 bash scripts/p7_bench_dev.sh   waits until the P6 TEST chain (unit arena-p6test) has ended cleanly, then runs
#   DRY=1 bash scripts/p7_bench_dev.sh       prints the plan, runs nothing
# Lane A, one rendering Isaac at a time: CL0, CL0_W -> ACT_old s1000, s2000 -> ACT_W s1000, s2000, s3000 -> ACT_W_slow s1000 -> DP_W s1000, s2000, s3000
# Lane B, alongside (ORACLE methods do not render): ORACLE, ORACLE_W
# Inference exactly as in the P6 TEST: ACT through serve_i2 (ACT_REPLAN=0, ACT_COMMIT=0), DP through diffusion_i2 (DP_REPLAN=0, DP_STEPS=0).
# The checkpoints are checked against PREREGISTRATION_PAPER.md section 7 (the ones tested in P6).  At the end: scripts/p7_bench_compare.py.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
PREREG=PREREGISTRATION_PAPER.md
P6LOG=logs/2026-11-18_141151_p6_test_chain.log
STOP=runs/p7_bench_STOP
BENCH=${BENCH:-../../Benmark_Capstone}
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
GRID="--cells dev_C0,dev_C2 --n 10 --speeds L0,L0.25"
N=40

die() { echo "NOT STARTED: $*"; exit 3; }
prereg_hash() { awk -v k="$1:" '$1 == k && length($2) >= 40 { print $2; exit }' "$PREREG"; }
dir_hash() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64; }

# ---- wait for the P6 TEST chain (one Isaac at a time, rule 1), start only if it ended cleanly
if [ "${WAIT_P6:-}" = "1" ] && [ "${DRY:-}" != "1" ]; then
    echo "$(date '+%F %T') waiting for unit arena-p6test to end"
    while systemctl --user is-active -q arena-p6test; do sleep 60; done
    echo "$(date '+%F %T') arena-p6test ended"
    sleep 30
fi
if [ "${DRY:-}" != "1" ]; then
    grep -q "P6 TEST chain done" $P6LOG || die "the P6 TEST chain did not finish ($P6LOG): resume the TEST first"
    [ -f runs/p6_test_STOP ] && die "runs/p6_test_STOP exists: decide on the TEST first"
    grep -q "INCOMPLETE" $P6LOG && die "a P6 TEST run is INCOMPLETE: resume the TEST first"
    need_no_isaac
fi
need_no_training
[ -d "$BENCH/results/raw" ] || die "benchmark results not found at $BENCH/results/raw"
CKPTS="act_i2_s1000 act_i2_s2000 act_w_s1000 act_w_s2000 act_w_s3000 act_w_slow_s1000 dp_w_s1000 dp_w_s2000 dp_w_s3000"
for d in $CKPTS; do
    ck=runs/$d/checkpoints/last/pretrained_model
    [ "$(sha256sum $ck/model.safetensors | cut -c1-64)" = "$(prereg_hash "$d")" ] || die "weights of $d differ from $PREREG"
    [ "$(dir_hash $ck)" = "$(prereg_hash "$d/pretrained_model")" ] || die "files of $ck differ from $PREREG"
done
[ -f $STOP ] && die "$STOP exists (an earlier run exceeded 10 % valid=0): decide by hand first"

invalid_share_ok() {   # trials.csv: valid=0 share <= 10 %
    python3 - "$1/trials.csv" <<'EOF'
import csv, os, sys
p = sys.argv[1]
rows = list(csv.DictReader(open(p))) if os.path.exists(p) else []
bad = sum(r["valid"] != "1" for r in rows)
print(f"  valid=0 rows: {bad}/{len(rows)}")
sys.exit(1 if rows and bad / len(rows) > 0.10 else 0)
EOF
}
cell() {   # cell NAME run_arena-method-args...   -> 0 complete, 1 incomplete, 3 stop
    local name=$1; shift
    local out=runs/p7_bench_dev_$name tag=p7_$name rc
    [ -f $STOP ] && { echo "$(date +%T) $tag not started: $STOP exists"; return 3; }
    if [ "${DRY:-}" = "1" ]; then echo "DRY $tag -> $out: run_arena $* $GRID"; return 0; fi
    run_until "$tag" "$out" $N "$@" $GRID; rc=$?
    if ! invalid_share_ok "$out"; then echo "$(date +%T) $tag: more than 10 % valid=0, STOP (rule 7)"; echo "$tag $(date -Is)" >> $STOP; return 3; fi
    return $rc
}
serve() {   # serve act|dp PORT NAME CKPT -> PID
    if [ "$1" = act ]; then serve_i2 "$2" "$3" "$4"; return; fi
    DP_CKPT=$4 DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.diffusion_i2:make_method --name "$3" \
        --port "$2" --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_$2.log" 2>&1 &
    echo $!
}
remote_cell() {   # remote_cell NAME act|dp CKPT_RUN PORT   (server name = NAME in capitals -> method REMOTE:<NAME>)
    local name=$1 kind=$2 ck=runs/$3/checkpoints/last/pretrained_model port=$4 srv rc round i before
    local out=runs/p7_bench_dev_$name
    if [ "${DRY:-}" = "1" ]; then echo "DRY server $kind ${name^^} <- $ck on $port"; cell "$name" $(remote_args "$port"); return 0; fi
    for round in 1 2 3; do
        [ -f $STOP ] && return 3
        before=$(valid_rows "$out/trials.csv")
        srv=$(serve "$kind" "$port" "${name^^}" "$ck")
        for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
        sleep 5
        cell "$name" $(remote_args "$port"); rc=$?
        kill "$srv" 2>/dev/null; sleep 5; kill -9 "$srv" 2>/dev/null
        [ $rc -ne 1 ] && return $rc
        echo "$(date +%T) $name incomplete after server round $round ($before -> $(valid_rows "$out/trials.csv") valid)"
        [ "$(valid_rows "$out/trials.csv")" -le "$before" ] && [ "$round" -gt 1 ] && break
    done
    return 1
}
step() { "$@"; local rc=$?; [ $rc -eq 3 ] && return 3; [ $rc -ne 0 ] && echo "$(date +%T) INCOMPLETE (resume later): $*"; return 0; }

lane_a() {
    step cell cl0 --methods CL0 || return
    step cell cl0_w --methods CL0_W || return
    step remote_cell act_old_s1000 act act_i2_s1000 7601 || return
    step remote_cell act_old_s2000 act act_i2_s2000 7602 || return
    step remote_cell act_w_s1000 act act_w_s1000 7603 || return
    step remote_cell act_w_s2000 act act_w_s2000 7604 || return
    step remote_cell act_w_s3000 act act_w_s3000 7605 || return
    step remote_cell act_w_slow_s1000 act act_w_slow_s1000 7606 || return
    step remote_cell dp_w_s1000 dp dp_w_s1000 7607 || return
    step remote_cell dp_w_s2000 dp dp_w_s2000 7608 || return
    step remote_cell dp_w_s3000 dp dp_w_s3000 7609 || return
}
lane_b() {
    step cell oracle --methods ORACLE || return
    step cell oracle_w --methods ORACLE_W || return
}

if [ "${DRY:-}" = "1" ]; then
    echo "--- lane A"; lane_a; echo "--- lane B"; lane_b
    echo "DRY: guards passed (HEAD $(git rev-parse --short HEAD)); nothing was run"; exit 0
fi
echo "$(date '+%F %T') P7 benchmark-DEV start: HEAD $(git rev-parse HEAD)"
nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader -l 60 > "logs/$(date +%F_%H%M%S)_p7_vram.log" 2>&1 &
vram=$!
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
kill $vram 2>/dev/null
env -u PYTHONPATH "$CL0_PY" scripts/p7_bench_compare.py --bench "$BENCH" --json runs/p7_bench_compare.json 2>&1 | tee "logs/$(date +%F_%H%M%S)_p7_bench_compare.txt"
echo "$(date '+%F %T') P7 benchmark-DEV chain done"
