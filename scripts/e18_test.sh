#!/bin/bash
# E18 step F (PREREGISTRATION_E18.md): the LOCKED task test.  Only on the user's explicit order:  CONFIRM_TEST=yes bash scripts/e18_test.sh
#   ACT_I2T on test_Theld (8 held-out tasks x 10) and test_Tseen (32 trained tasks x 5); TASK_EXPERT (ceiling) and NOOP (floor) on the same scenes.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
[ "${CONFIRM_TEST:-}" = "yes" ] || { echo "REFUSED: locked test_T* cells; CONFIRM_TEST=yes only on the user's explicit order"; exit 2; }
git diff --quiet HEAD -- PREREGISTRATION_E18.md && git ls-files --error-unmatch PREREGISTRATION_E18.md >/dev/null 2>&1 \
    || { echo "REFUSED: PREREGISTRATION_E18.md is not committed (or has local changes)"; exit 2; }
grep -q 'act_i2t_s1000: *[0-9a-f]\{64\}' PREREGISTRATION_E18.md || { echo "REFUSED: checkpoint sha256 not in PREREGISTRATION_E18.md"; exit 2; }
need_no_training
CK=runs/act_i2t_s1000/checkpoints/last/pretrained_model
need_ckpt $CK
LK="--objects tasks --tasks --arrangements-dir locked/tasks --allow-locked"
NS=$("$CL0_PY" -c "import json;print(len(json.load(open('locked/tasks/test_Tseen.json'))['items']))")
NH=$("$CL0_PY" -c "import json;print(len(json.load(open('locked/tasks/test_Theld.json'))['items']))")
H=$(( NS / 2 ))
lane_a() {
    s=$(serve_i2 7301 ACT_I2T $CK); sleep 20
    run_until e18_held_act runs/e18_test_held_act $NH $(remote_args 7301) $LK --cells test_Theld --n $NH
    run_until e18_seen_act_a runs/e18_test_seen_act_a $H $(remote_args 7301) $LK --cells test_Tseen --first 0 --n $H; kill $s
    run_until e18_held_ref runs/e18_test_held_ref $(( 2 * NH )) --methods TASK_EXPERT,NOOP $LK --cells test_Theld --n $NH
}
lane_b() {
    s=$(serve_i2 7302 ACT_I2T $CK); sleep 20
    run_until e18_seen_act_b runs/e18_test_seen_act_b $(( NS - H )) $(remote_args 7302) $LK --cells test_Tseen --first $H --n $(( NS - H )); kill $s
    run_until e18_seen_ref runs/e18_test_seen_ref $(( 2 * NS )) --methods TASK_EXPERT,NOOP $LK --cells test_Tseen --n $NS
}
lane_a > >(sed -u 's/^/A /') &
pa=$!
sleep 60
lane_b > >(sed -u 's/^/B /') &
pb=$!
wait $pa $pb
python3 scripts/e18_summary.py test runs/e18_test_* | tee "logs/$(date +%F_%H%M%S)_e18_decision.txt"
