#!/bin/bash
# M4 confirmation (PREREGISTRATION_M4.md) on the NEW locked sheet locked/m4/test_C2.csv (seed 1120): DP_W (M3) and DP_W + corrector (M4), seeds 1000, 2000, 3000, L0.5 (75 mm/s),
# the same 60 scenes for all six runs (about 1.9 h each, one Isaac at a time).
#   CONFIRM_TEST=yes bash scripts/m4_test.sh      only on the user's explicit order (arena/CLAUDE.md rule 5)
#   DRY=1 bash scripts/m4_test.sh                 checks every guard and prints the plan, runs nothing
#   WAIT_FOR_GPU=1 ...                            first waits until no arena.run_arena is running
# Order: s1000 M3, s1000 M4, s2000 M3, s2000 M4, s3000 M3, s3000 M4 (so that a late stop still leaves paired runs).  At the end: scripts/m4_decide.py.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
PREREG=PREREGISTRATION_M4.md
SHEET=locked/m4/test_C2.csv
STOP=runs/m4_test_STOP
FROZEN="m4 arena/methods/diffusion_i2.py arena/methods/act_i2.py arena/i2.py arena/dp_i2.py remote_server.py $SHEET scripts/lib_chain.sh scripts/m4_wait.sh scripts/m4_test.sh scripts/m4_decide.py"
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}
LK="--cells test_C2 --n 60 --arrangements-dir locked/m4 --allow-locked"
die() { echo "REFUSED: $*"; exit 2; }
prereg_hash() { awk -v k="$1:" '$1 == k && length($2) >= 40 { print $2; exit }' "$PREREG"; }
dir_hash() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64; }
[ "${CONFIRM_TEST:-}" = "yes" ] || [ "${DRY:-}" = "1" ] || die "this chain runs the LOCKED sheet $SHEET: CONFIRM_TEST=yes only on the user's explicit order (rule 5)"
git ls-files --error-unmatch $PREREG $SHEET scripts/m4_test.sh scripts/m4_decide.py m4/m4_vs.env >/dev/null 2>&1 || die "$PREREG, $SHEET, the M4 scripts or m4/m4_vs.env are not committed"
git diff --quiet HEAD -- $PREREG $FROZEN || die "local changes in $PREREG or the frozen files"
LOCK=$(prereg_hash "lock_commit")
[ ${#LOCK} -eq 40 ] && git cat-file -e "$LOCK^{commit}" 2>/dev/null || die "no valid lock commit ('lock_commit: <sha1>') in $PREREG section 7"
git diff --quiet "$LOCK" HEAD -- $FROZEN || die "frozen files changed since the lock commit $LOCK"
[ "$(sha256sum $SHEET | cut -c1-64)" = "$(prereg_hash "$SHEET")" ] || die "sha256 of $SHEET differs from $PREREG"
[ "$(sha256sum m4/m4_vs.env | cut -c1-64)" = "$(prereg_hash "m4/m4_vs.env")" ] || die "m4/m4_vs.env differs from $PREREG"
for d in dp_w_s1000 dp_w_s2000 dp_w_s3000; do
    ck=runs/$d/checkpoints/last/pretrained_model
    [ "$(sha256sum $ck/model.safetensors | cut -c1-64)" = "$(prereg_hash "$d")" ] || die "weights of $d differ from $PREREG"
    [ "$(dir_hash $ck)" = "$(prereg_hash "$d/pretrained_model")" ] || die "files of $ck differ from $PREREG"
done
need_no_training
source "$(dirname "$(readlink -f "$0")")/m4_wait.sh"
if [ "${WAIT_FOR_GPU:-}" = "1" ]; then m4_wait_gpu; fi
[ "${DRY:-}" = "1" ] || [ "${GPU_SHARE:-}" = "1" ] || need_no_isaac
[ -f $STOP ] && die "$STOP exists (an earlier run exceeded 10 % valid=0): decide by hand first"
invalid_share_ok() {
    python3 - "$1/trials.csv" <<'PY'
import csv, os, sys
p = sys.argv[1]
rows = list(csv.DictReader(open(p))) if os.path.exists(p) else []
bad = sum(r["valid"] != "1" for r in rows)
print(f"  valid=0 rows: {bad}/{len(rows)}")
sys.exit(1 if rows and bad / len(rows) > 0.10 else 0)
PY
}
one() {   # one KIND SEED PORT     KIND = dp_w (M3) | dpvs (M4)
    local kind=$1 seed=$2 port=$3 out=runs/m4_test_c2_l05_${1}_s$2 ck=runs/dp_w_s$2/checkpoints/last/pretrained_model srv fac=arena.methods.diffusion_i2
    [ $kind = dpvs ] && fac=diffusion_vs
    [ -f $STOP ] && return 3
    if [ "${DRY:-}" = "1" ]; then echo "DRY $kind s$seed -> $out (factory $fac, port $port, ckpt $ck)"; return 0; fi
    srv=$( (set -a; source m4/m4_vs.env; set +a
        DP_CKPT=$ck DP_REPLAN=0 DP_STEPS=0 env -u PYTHONPATH "$LR_PY" remote_server.py --factory $fac:make_method --name "${kind^^}_S$seed" \
            --port $port --path m4 --path . --path ../cl0 --repeat > "logs/$(date +%F_%H%M%S)_server_m4_${kind}_$port.log" 2>&1 &
        echo $!) )
    for i in $(seq 1 90); do ss -ltn "sport = :$port" | grep -q LISTEN && break; sleep 2; done
    run_until "m4_test_${kind}_s$seed" "$out" 60 $(remote_args $port) $LK --speeds L0.5
    local rc=$?
    kill $srv 2>/dev/null; sleep 3; kill -9 $srv 2>/dev/null
    if ! invalid_share_ok "$out"; then echo "$(date +%T) $kind s$seed: more than 10 % valid=0, STOP (rule 7)"; echo "$kind s$seed $(date -Is)" >> $STOP; return 3; fi
    return $rc
}
echo "$(date '+%F %T') M4 TEST start: HEAD $(git rev-parse HEAD), lock $LOCK"
port=7701
for s in 1000 2000 3000; do
    for kind in dp_w dpvs; do port=$((port + 1)); one $kind $s $port || { [ $? -eq 3 ] && break 2; }; done
done
[ "${DRY:-}" = "1" ] || env -u PYTHONPATH "$CL0_PY" scripts/m4_decide.py --json runs/m4_test_decision.json 2>&1 | tee "logs/$(date +%F_%H%M%S)_m4_decision.txt"
echo "$(date '+%F %T') M4 TEST chain done"
