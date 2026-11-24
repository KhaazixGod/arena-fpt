#!/bin/bash
# FINAL TEST (PREREGISTRATION_FINAL.md): M1 (CV + IK, open loop), M3 (DP_W) and M4 v2 (DP_W + corrector v2) on the NEW locked sheet locked/final/test_C2.csv (seed 1125, 120 scenes),
# L0.5 (75 mm/s) on scenes 1-120, L0.25 (37.5 mm/s) and L0 (0 mm/s) on scenes 1-60.  Two lanes (two Isaac processes at once, as in P6/P8):
#   lane A: L0.5 scenes 1-60, then L0.25 scenes 1-60        lane B: L0.5 scenes 61-120, then L0 scenes 1-60
# Within a block: M1, then for seed 1000, 2000, 3000: M3, M4 v2 (so that a late stop leaves paired runs).  Lane B ends with the optional M4 v1 runs.  Outputs runs/final_c2_<speed>_<block>_<kind>_s<seed>.
#   CONFIRM_TEST=yes bash scripts/final_test.sh     only on the user's explicit order (arena/CLAUDE.md rule 5)
#   DRY=1 bash scripts/final_test.sh                checks every guard and prints the plan, runs nothing
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
PREREG=PREREGISTRATION_FINAL.md
SHEET=locked/final/test_C2.csv
STOP=runs/final_test_STOP
FROZEN="m4 m4v2 arena/methods/diffusion_i2.py arena/i2.py arena/dp_i2.py remote_server.py $SHEET scripts/lib_chain.sh scripts/final_test.sh scripts/final_decide.py"
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
die() { echo "REFUSED: $*"; exit 2; }
prereg_hash() { awk -v k="$1:" '$1 == k && length($2) >= 40 { print $2; exit }' "$PREREG"; }
dir_hash() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64; }
[ "${CONFIRM_TEST:-}" = "yes" ] || [ "${DRY:-}" = "1" ] || die "this chain runs the LOCKED sheet $SHEET: CONFIRM_TEST=yes only on the user's explicit order (rule 5)"
git ls-files --error-unmatch $PREREG $SHEET scripts/final_test.sh scripts/final_decide.py m4v2/m4v2.env m4v2/diffusion_vs2.py m4v2/kin_cv_ik.py >/dev/null 2>&1 || die "$PREREG, the sheet or the final scripts are not committed"
git diff --quiet HEAD -- $PREREG $FROZEN || die "local changes in $PREREG or the frozen files"
LOCK=$(prereg_hash "lock_commit")
[ ${#LOCK} -eq 40 ] && git cat-file -e "$LOCK^{commit}" 2>/dev/null || die "no valid lock commit ('lock_commit: <sha1>') in $PREREG section 7"
git diff --quiet "$LOCK" HEAD -- $FROZEN || die "frozen files changed since the lock commit $LOCK"
[ "$(sha256sum $SHEET | cut -c1-64)" = "$(prereg_hash "$SHEET")" ] || die "sha256 of $SHEET differs from $PREREG"
for f in m4/m4_vs.env m4v2/m4v2.env; do [ "$(sha256sum $f | cut -c1-64)" = "$(prereg_hash "$f")" ] || die "$f differs from $PREREG"; done
for d in dp_w_s1000 dp_w_s2000 dp_w_s3000; do
    ck=runs/$d/checkpoints/last/pretrained_model
    [ "$(sha256sum $ck/model.safetensors | cut -c1-64)" = "$(prereg_hash "$d")" ] || die "weights of $d differ from $PREREG"
    [ "$(dir_hash $ck)" = "$(prereg_hash "$d/pretrained_model")" ] || die "files of $ck differ from $PREREG"
done
need_no_training
[ "${DRY:-}" = "1" ] || [ "${GPU_SHARE:-}" = "1" ] || [ "$(pgrep -fc 'arena.run_arena')" -eq 0 ] || die "another arena.run_arena is running (set GPU_SHARE=1 only if it is one of this chain's lanes or one you accept)"
[ -f $STOP ] && die "$STOP exists (an earlier run exceeded 10 % valid=0): decide by hand first"
invalid_share_ok() {
    python3 - "$1/trials.csv" <<'PY'
import csv, os, sys
p = sys.argv[1]
rows = list(csv.DictReader(l for l in open(p) if not l.startswith('#'))) if os.path.exists(p) else []
bad = sum(r["valid"] != "1" for r in rows)
print(f"  valid=0 rows: {bad}/{len(rows)}")
sys.exit(1 if rows and bad / len(rows) > 0.10 else 0)
PY
}
# After its own blocks, lane B also runs M4 v1 (m4/diffusion_vs.py, kind dpvs) on L0.5 scenes 1-60 for the three seeds: a descriptive comparator that is skipped if it has not started by 27/11/2026 12:00.
V1_DEADLINE=$(date -d '2026-11-27 12:00' +%s)
# one SPEED BLOCK KIND SEED PORT       SPEED = L0.5|L0.25|L0, BLOCK = a (scenes 1-60) | b (scenes 61-120);  KIND = kin | dp_w | dpvs2 | dpvs (M4 v1)
one() {
    local sp=$1 blk=$2 kind=$3 seed=$4 port=$5 tag first=0 srv fac ck
    case $sp in L0.5) tag=l05;; L0.25) tag=l025;; L0) tag=l0;; esac
    [ $blk = b ] && first=60
    local out=runs/final_c2_${tag}_${blk}_${kind}_s${seed}
    local LK="--cells test_C2 --first $first --n 60 --arrangements-dir locked/final --allow-locked --speeds $sp"
    [ -f $STOP ] && return 3
    if [ $kind = dpvs ] && [ "${DRY:-}" != "1" ] && [ "$(date +%s)" -gt "$V1_DEADLINE" ]; then echo "$(date +%T) $kind s$seed: after the v1 deadline, skipped"; return 0; fi
    if [ "${DRY:-}" = "1" ]; then echo "DRY $sp $blk $kind s$seed -> $out (port $port, first $first)"; return 0; fi
    if [ $kind = kin ]; then
        run_until "final_${tag}_${blk}_kin" "$out" 60 --methods m4v2.kin_cv_ik:make_method $LK
    else
        ck=runs/dp_w_s$seed/checkpoints/last/pretrained_model; fac=arena.methods.diffusion_i2
        [ $kind = dpvs2 ] && fac=diffusion_vs2
        [ $kind = dpvs ] && fac=diffusion_vs
        srv=$( (set -a; source m4/m4_vs.env; source m4v2/m4v2.env; set +a
            DP_CKPT=$ck DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory $fac:make_method --name "${kind^^}_S${seed}_${tag}${blk}" \
                --port $port --path m4v2 --path m4 --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_final_${kind}_$port.log" 2>&1 &
            echo $!) )
        for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
        run_until "final_${tag}_${blk}_${kind}_s$seed" "$out" 60 $(remote_args $port) $LK
    fi
    local rc=$?
    [ -n "$srv" ] && { kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null; }
    if ! invalid_share_ok "$out"; then echo "$(date +%T) $kind s$seed $sp$blk: more than 10 % valid=0, STOP (rule 7)"; echo "$sp $blk $kind s$seed $(date -Is)" >> $STOP; return 3; fi
    return $rc
}
block() {   # block SPEED BLOCK PORTBASE
    local sp=$1 blk=$2 p=$3
    one $sp $blk kin 0 $((p)) || { [ $? -eq 3 ] && return 3; }
    for s in 1000 2000 3000; do
        for kind in dp_w dpvs2; do p=$((p + 1)); one $sp $blk $kind $s $p || { [ $? -eq 3 ] && return 3; }; done
    done
}
echo "$(date '+%F %T') FINAL TEST start: HEAD $(git rev-parse HEAD), lock $LOCK"
( block L0.5 a 7800 && block L0.25 a 7820 ) &
LA=$!
( [ "${DRY:-}" = "1" ] || sleep 120; block L0.5 b 7840 && block L0 a 7860 && for s in 1000 2000 3000; do one L0.5 a dpvs $s $((7880 + s / 1000)) || break; done ) &
LB=$!
wait $LA $LB
[ "${DRY:-}" = "1" ] || env -u PYTHONPATH "$CL0_PY" scripts/final_decide.py --json runs/final_test_decision.json 2>&1 | tee "logs/$(date +%F_%H%M%S)_final_decision.txt"
echo "$(date '+%F %T') FINAL TEST chain done"
