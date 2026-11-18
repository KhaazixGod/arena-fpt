#!/bin/bash
# P6: the paper's TEST (PREREGISTRATION_PAPER.md sections 3, 5, 6) on the NEW locked sheet locked/paper/test_C2.csv (seed 1611, the old TEST objects).
#   CONFIRM_TEST=yes bash scripts/p6_test.sh     only on the user's explicit order (arena/CLAUDE.md rule 5)
#   DRY=1 bash scripts/p6_test.sh                checks every guard and prints the plan, runs nothing
# Lane A, one rendering Isaac at a time:  CL0, CL0_W (L0.5) -> ACT_old s1000, s2000, ACT_W s1000, s2000, s3000 -> DP_W s1000, s2000, s3000, ACT_W_slow s1000
#                                         -> CL0, CL0_W (L0.25)
# Lane B, alongside lane A (ORACLE methods do not render): ORACLE, ORACLE_W (L0.5) -> ORACLE, ORACLE_W (L0.25)
# Every run: runs/p6_test_c2_<l05|l025>_<name>, n = 60, the same 60 arrangements.  run_until resumes and re-runs invalid trials until 60 are valid (prereg
# section 5); a run that ends with more than 10 % valid=0 rows writes runs/p6_test_STOP and both lanes stop before their next run (rule 7: stop and ask).  A run
# still incomplete after its retries is reported and the lane goes on (it can be resumed later; p6_decide.py prints no decision while any run is incomplete).
# Inference exactly as on DEV: ACT through serve_i2 (ACT_REPLAN=0, ACT_COMMIT=0); DP through arena.methods.diffusion_i2 (DP_REPLAN=0 -> n_action_steps 32,
# DP_STEPS=0 -> the checkpoint's 100 denoising steps).  At the end: scripts/p6_decide.py test (logs/*_p6_decision.txt, runs/p6_test_decision.json) and
# scripts/p2_compare.py on the modular pairs (W1 breakdown, descriptive).
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
PREREG=PREREGISTRATION_PAPER.md
SHEET=locked/paper/test_C2.csv
STOP=runs/p6_test_STOP
FROZEN="arena configs remote_server.py $SHEET scripts/lib_chain.sh scripts/p6_test.sh scripts/p6_decide.py"
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
LK="--cells test_C2 --n 60 --arrangements-dir locked/paper --allow-locked"

die() { echo "REFUSED: $*"; exit 2; }
prereg_hash() { awk -v k="$1:" '$1 == k && length($2) >= 40 { print $2; exit }' "$PREREG"; }
dir_hash() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64; }

# ---- guards (rule 5, prereg section 6)
[ "${CONFIRM_TEST:-}" = "yes" ] || [ "${DRY:-}" = "1" ] || die "this chain runs the LOCKED sheet $SHEET: CONFIRM_TEST=yes only on the user's explicit order (rule 5)"
git ls-files --error-unmatch $PREREG $SHEET scripts/p6_test.sh scripts/p6_decide.py >/dev/null 2>&1 || die "$PREREG, $SHEET or the P6 scripts are not committed"
git diff --quiet HEAD -- $PREREG $FROZEN || die "local changes in $PREREG or the frozen files"
LOCK=$(prereg_hash "lock_commit")
[ ${#LOCK} -eq 40 ] && git cat-file -e "$LOCK^{commit}" 2>/dev/null || die "no valid lock commit ('lock_commit: <sha1>') in $PREREG section 7"
git diff --quiet "$LOCK" HEAD -- $FROZEN || die "frozen files changed since the lock commit $LOCK"
[ "$(sha256sum $SHEET | cut -c1-64)" = "$(prereg_hash "$SHEET")" ] || die "sha256 of $SHEET differs from $PREREG"
CKPTS="act_i2_s1000 act_i2_s2000 act_w_s1000 act_w_s2000 act_w_s3000 dp_w_s1000 dp_w_s2000 dp_w_s3000 act_w_slow_s1000"
for d in $CKPTS; do
    ck=runs/$d/checkpoints/last/pretrained_model
    [ "$(sha256sum $ck/model.safetensors | cut -c1-64)" = "$(prereg_hash "$d")" ] || die "weights of $d differ from $PREREG"
    [ "$(dir_hash $ck)" = "$(prereg_hash "$d/pretrained_model")" ] || die "files of $ck differ from $PREREG"
done
need_no_training
[ "${DRY:-}" = "1" ] || need_no_isaac
ls runs/p6_test_c2_* >/dev/null 2>&1 && echo "note: runs/p6_test_c2_* exist, run_until resumes them"
[ -f $STOP ] && die "$STOP exists (an earlier run exceeded 10 % valid=0): decide by hand first"

# ---- one run
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
cell() {   # cell NAME SPEED run_arena-method-args...   -> 0 complete, 1 incomplete, 3 stop
    local name=$1 sp=$2; shift 2
    local st; st=$(echo "$sp" | tr -d . | tr L l)
    local out=runs/p6_test_c2_${st}_$name tag=p6_${st}_$name rc
    [ -f $STOP ] && { echo "$(date +%T) $tag not started: $STOP exists"; return 3; }
    if [ "${DRY:-}" = "1" ]; then echo "DRY $tag -> $out: run_arena $* $LK --speeds $sp"; return 0; fi
    run_until "$tag" "$out" 60 "$@" $LK --speeds "$sp"; rc=$?
    if ! invalid_share_ok "$out"; then echo "$(date +%T) $tag: more than 10 % valid=0, STOP (rule 7)"; echo "$tag $(date -Is)" >> $STOP; return 3; fi
    return $rc
}
serve() {   # serve act|dp PORT NAME CKPT -> PID
    if [ "$1" = act ]; then serve_i2 "$2" "$3" "$4"; return; fi
    DP_CKPT=$4 DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory arena.methods.diffusion_i2:make_method --name "$3" \
        --port "$2" --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_$2.log" 2>&1 &
    echo $!
}
remote_cell() {   # remote_cell NAME SPEED act|dp CKPT_RUN PORT   (server name = NAME in capitals -> method REMOTE:<NAME>)
    local name=$1 sp=$2 kind=$3 ck=runs/$4/checkpoints/last/pretrained_model port=$5 srv rc round i before
    local out=runs/p6_test_c2_$(echo "$sp" | tr -d . | tr L l)_$name
    if [ "${DRY:-}" = "1" ]; then echo "DRY server $kind ${name^^} <- $ck on $port"; cell "$name" "$sp" $(remote_args "$port"); return 0; fi
    for round in 1 2 3; do
        [ -f $STOP ] && return 3
        before=$(valid_rows "$out/trials.csv")
        srv=$(serve "$kind" "$port" "${name^^}" "$ck")
        for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
        sleep 5
        cell "$name" "$sp" $(remote_args "$port"); rc=$?
        kill "$srv" 2>/dev/null; sleep 5; kill -9 "$srv" 2>/dev/null
        [ $rc -ne 1 ] && return $rc
        echo "$(date +%T) $name incomplete after server round $round ($before -> $(valid_rows "$out/trials.csv") valid)"
        [ "$(valid_rows "$out/trials.csv")" -le "$before" ] && [ "$round" -gt 1 ] && break     # two rounds without progress: give up, resume by hand
    done
    return 1
}
step() { "$@"; local rc=$?; [ $rc -eq 3 ] && return 3; [ $rc -ne 0 ] && echo "$(date +%T) INCOMPLETE (resume later): $*"; return 0; }

lane_a() {
    step cell cl0 L0.5 --methods CL0 || return
    step cell cl0_w L0.5 --methods CL0_W || return
    step remote_cell act_old_s1000 L0.5 act act_i2_s1000 7501 || return
    step remote_cell act_old_s2000 L0.5 act act_i2_s2000 7502 || return
    step remote_cell act_w_s1000 L0.5 act act_w_s1000 7503 || return
    step remote_cell act_w_s2000 L0.5 act act_w_s2000 7504 || return
    step remote_cell act_w_s3000 L0.5 act act_w_s3000 7505 || return
    step remote_cell dp_w_s1000 L0.5 dp dp_w_s1000 7506 || return
    step remote_cell dp_w_s2000 L0.5 dp dp_w_s2000 7507 || return
    step remote_cell dp_w_s3000 L0.5 dp dp_w_s3000 7508 || return
    step remote_cell act_w_slow_s1000 L0.5 act act_w_slow_s1000 7509 || return
    step cell cl0 L0.25 --methods CL0 || return
    step cell cl0_w L0.25 --methods CL0_W || return
}
lane_b() {
    step cell oracle L0.5 --methods ORACLE || return
    step cell oracle_w L0.5 --methods ORACLE_W || return
    step cell oracle L0.25 --methods ORACLE || return
    step cell oracle_w L0.25 --methods ORACLE_W || return
}

if [ "${DRY:-}" = "1" ]; then
    echo "--- lane A"; lane_a; echo "--- lane B"; lane_b
    echo "DRY: every guard passed (lock commit $LOCK, HEAD $(git rev-parse --short HEAD)); nothing was run"; exit 0
fi
echo "$(date '+%F %T') P6 TEST start: lock commit $LOCK, HEAD $(git rev-parse HEAD), sheet $(sha256sum $SHEET | cut -c1-12)"
nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader -l 60 > "logs/$(date +%F_%H%M%S)_p6_vram.log" 2>&1 &
vram=$!
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
kill $vram 2>/dev/null
env -u PYTHONPATH "$CL0_PY" scripts/p6_decide.py test --json runs/p6_test_decision.json 2>&1 | tee "logs/$(date +%F_%H%M%S)_p6_decision.txt"
python3 scripts/p2_compare.py runs/p6_test_c2_l05_cl0 runs/p6_test_c2_l05_cl0_w runs/p6_test_c2_l05_oracle runs/p6_test_c2_l05_oracle_w \
    runs/p6_test_c2_l025_cl0 runs/p6_test_c2_l025_cl0_w runs/p6_test_c2_l025_oracle runs/p6_test_c2_l025_oracle_w > "logs/$(date +%F_%H%M%S)_p6_w1_compare.txt" 2>&1
echo "$(date '+%F %T') P6 TEST chain done"
