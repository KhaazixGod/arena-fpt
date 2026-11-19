#!/bin/bash
# P8 TEST (PREREGISTRATION_P8.md section 3): the re-implemented paper ports and P19 on the locked sheet locked/paper/test_C2.csv (the P6 sheet), n 60.
# Runs: runs/p8_test_c2_<l05|l025>_<name>.  CL0_W / ACT_W at L0.5 and CL0_W at L0.25 are the P6 runs (same sheet, same machine).
# Guards: CONFIRM_TEST=yes (rule 5; order in PREREGISTRATION_P8.md section 1), prereg committed and locked (section 7: lock_commit + hashes),
# the frozen files unchanged since the lock commit, checkpoints and reference views identical to the recorded hashes.  Never with training.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
PREREG=PREREGISTRATION_P8.md
SHEET=locked/paper/test_C2.csv
PORTS_PY="$HOME/venvs/ports/bin/python"
STOP=runs/p8_test_STOP
FROZEN="ports/common.py ports/detector_server.py ports/p05_cns.py ports/p07_vitvs.py ports/p17_odil.py arena/methods/ports.py arena/methods/act_lerobot.py arena/methods/act_i2.py"
LK="--cells test_C2 --n 60 --arrangements-dir locked/paper --allow-locked"
export RUN_UNTIL_ATTEMPTS=${RUN_UNTIL_ATTEMPTS:-30} RUN_UNTIL_STALL_S=${RUN_UNTIL_STALL_S:-360}

die() { echo "REFUSED: $*"; exit 2; }
prereg_hash() { awk -v k="$1:" '$1 == k && length($2) >= 40 { print $2; exit }' "$PREREG"; }
dir_hash() { (cd "$1" && find -L . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64; }

[ "${CONFIRM_TEST:-}" = "yes" ] || [ "${DRY:-}" = "1" ] || die "locked sheet: CONFIRM_TEST=yes only on the user's order (rule 5)"
git ls-files --error-unmatch $PREREG $SHEET scripts/p8_test.sh scripts/p8_decide.py $FROZEN >/dev/null 2>&1 || die "prereg, sheet, scripts or frozen files not committed"
git diff --quiet HEAD -- $PREREG $FROZEN scripts/p8_test.sh || die "local changes in $PREREG, the frozen files or this script"
LOCK=$(prereg_hash "lock_commit")
[ ${#LOCK} -eq 40 ] && git cat-file -e "$LOCK^{commit}" 2>/dev/null || die "no lock_commit in $PREREG section 7"
git diff --quiet "$LOCK" HEAD -- $FROZEN || die "frozen files changed since the lock commit"
[ "$(sha256sum $SHEET | cut -c1-64)" = "$(prereg_hash "$SHEET")" ] || die "sha256 of $SHEET differs from $PREREG"
for d in act_j0_s1000 act_j0_s2000 act_j0_s3000 act_w_s1000 act_w_s2000 act_w_s3000; do
    ck=runs/$d/checkpoints/last/pretrained_model
    [ "$(sha256sum $ck/model.safetensors | cut -c1-64)" = "$(prereg_hash "$d")" ] || die "weights of $d differ from $PREREG"
done
for d in train_dev testobj; do [ "$(dir_hash runs/p8_refs/$d)" = "$(prereg_hash "refs/$d")" ] || die "reference views $d differ from $PREREG"; done
[ -f $STOP ] && die "$STOP exists"
[ "${DRY:-}" = "1" ] || need_no_training
mkdir -p runs/p8_refs/all && for f in runs/p8_refs/train_dev/* runs/p8_refs/testobj/*; do ln -sf "../$(basename "$(dirname "$f")")/$(basename "$f")" runs/p8_refs/all/; done

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
run() {   # run NAME SPEED run_arena-method-args...
    local name=$1 sp=$2; shift 2
    local tag="p8_test_${sp/./}_$name" out rc
    out=runs/p8_test_c2_$(echo "$sp" | sed 's/L0.5/l05/; s/L0.25/l025/')_$name
    [ -f $STOP ] && return 3
    if [ "${DRY:-}" = "1" ]; then echo "DRY $out: run_arena $* $LK --speeds $sp"; return 0; fi
    run_until "$tag" "$out" 60 "$@" $LK --speeds "$sp"; rc=$?
    if ! invalid_share_ok "$out"; then echo "$(date +%T) $out: more than 10 % valid=0, STOP (rule 7)"; echo "$out $(date -Is)" >> $STOP; return 3; fi
    return $rc
}
wait_port() { local i; for i in $(seq 1 120); do ss -ltn "sport = :$1" | grep -q LISTEN && return 0; sleep 2; done; return 1; }
with_server() {   # with_server PID PORT -- cmd...
    local srv=$1 port=$2 rc; shift 3
    if [ "${DRY:-}" = "1" ]; then "$@"; return 0; fi
    wait_port "$port" || { echo "$(date +%T) server on $port did not start"; kill "$srv" 2>/dev/null; return 1; }
    sleep 3; "$@"; rc=$?
    kill "$srv" 2>/dev/null; sleep 3; kill -9 "$srv" 2>/dev/null
    return $rc
}
port() {   # port NAME SPEED METHOD KIND PORT REFS
    local name=$1 sp=$2 meth=$3 kind=$4 p=$5 refs=$6 srv=0 py=$PORTS_PY
    [ "$kind" = p07_vitvs ] && py=$LR_PY
    [ "${DRY:-}" = "1" ] || { env -u PYTHONPATH "$py" ports/detector_server.py --detector "$kind" --refs "$refs" --port "$p" --repeat \
        > "logs/$(date +%F_%H%M%S)_p8det_${kind}_${p}.log" 2>&1 & srv=$!; }
    with_server "$srv" "$p" -- run "$name" "$sp" --methods "$meth" --method-arg detector=localhost:$p --depth
}
p19() {   # p19 SEED SPEED PORT
    local srv=0
    [ "${DRY:-}" = "1" ] || { ACT_CKPT=runs/act_j0_s$1/checkpoints/last/pretrained_model ACT_TE_COEFF=0.01 env -u PYTHONPATH "$LR_PY" remote_server.py \
        --factory arena.methods.act_lerobot:make_method --name "P19_ACT_TE_S$1" --port "$3" --path . --path ../cl0 --repeat \
        > "logs/$(date +%F_%H%M%S)_p8_p19_s$1_$3.log" 2>&1 & srv=$!; }
    with_server "$srv" "$3" -- run "p19_s$1" "$2" $(remote_args "$3")
}
actw() {   # actw SEED SPEED PORT   (as P6: serve_i2, ACT_REPLAN=0, ACT_COMMIT=0; server name ACT_W_S<seed> as in P6)
    local srv=0
    [ "${DRY:-}" = "1" ] || srv=$(serve_i2 "$3" "ACT_W_S$1" runs/act_w_s$1/checkpoints/last/pretrained_model)
    with_server "$srv" "$3" -- run "act_w_s$1" "$2" $(remote_args "$3")
}
step() { "$@"; local rc=$?; [ $rc -eq 3 ] && return 3; [ $rc -ne 0 ] && echo "$(date +%T) INCOMPLETE (resume later): $*"; return 0; }

R=runs/p8_refs/train_dev; RA=runs/p8_refs/all
lane_a() {
    for sp in L0.5 L0.25; do
        local b=7801; [ $sp = L0.25 ] && b=7811
        step port p05_cns_w $sp P05_CNS_W p05_cns $b $R || return
        step port p07_vitvs_w $sp P07_VITVS_W p07_vitvs $((b + 1)) $R || return
        step port p17_odil_w $sp P17_ODIL_W p17_odil $((b + 2)) $R || return
        step port p05_cns $sp P05_CNS p05_cns $((b + 3)) $R || return
        step port p07_vitvs $sp P07_VITVS p07_vitvs $((b + 4)) $R || return
        step port p17_odil $sp P17_ODIL p17_odil $((b + 5)) $R || return
    done
    step port p05_cns_w_t L0.5 P05_CNS_W p05_cns 7821 $RA || return
    step port p07_vitvs_w_t L0.5 P07_VITVS_W p07_vitvs 7822 $RA || return
    step port p17_odil_w_t L0.5 P17_ODIL_W p17_odil 7823 $RA || return
}
lane_b() {
    step p19 1000 L0.5 7851 || return
    step p19 2000 L0.5 7852 || return
    step p19 3000 L0.5 7853 || return
    step actw 1000 L0.25 7854 || return
    step actw 2000 L0.25 7855 || return
    step actw 3000 L0.25 7856 || return
    step p19 1000 L0.25 7857 || return
    step p19 2000 L0.25 7858 || return
    step p19 3000 L0.25 7859 || return
}

echo "$(date '+%F %T') P8 TEST start: HEAD $(git rev-parse HEAD), lock $LOCK"
[ "${DRY:-}" = "1" ] || nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader -l 60 > "logs/$(date +%F_%H%M%S)_p8_test_vram.log" 2>&1 &
vram=$!
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
kill $vram 2>/dev/null
env -u PYTHONPATH "$CL0_PY" scripts/p8_decide.py --json runs/p8_test_decision.json 2>&1 | tee "logs/$(date +%F_%H%M%S)_p8_decision.txt"
echo "$(date '+%F %T') P8 TEST chain done"
