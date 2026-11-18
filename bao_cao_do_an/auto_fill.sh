#!/usr/bin/env bash
# Fills the two thesis reports as soon as the results exist.
#   1. waits for "P6 TEST chain done" in the newest logs/*_p6_test_chain.log; if runs/p6_test_decision.json exists (scripts/p6_decide.py writes it
#      only when every run is complete and every hash matches), rebuilds both .docx with the TEST numbers;
#   2. waits for "P7 benchmark-DEV chain done" in the newest logs/*_p7_bench_chain.log and rebuilds again with runs/p7_bench_compare.json.
# Reads only the files those chains write when they finish (no partial runs, no success rates before the end).  A report that was edited by hand
# after its last build is not overwritten: the new build goes to <name>_moi.docx (bao_cao_do_an/lib.js save()).
# Run from arena/ as a systemd user unit:
#   systemd-run --user --unit arena-reportfill --working-directory=$PWD /usr/bin/bash -c 'bao_cao_do_an/auto_fill.sh > logs/$(date +%F_%H%M%S)_report_fill.log 2>&1'
# ONCE=1 builds once now and exits (with the REPORT_* variables of bao_cao_do_an/fill.js pointing at test inputs).
set -u
cd "$(dirname "$0")/.." || exit 1
PY=/usr/bin/python3     # system python has matplotlib; the cl0 venv does not
log() { echo "$(date '+%F %T') $*"; }

yellow_left() {   # yellow ({{…}}) cells left in each built report
    "$PY" - "${REPORT_OUT:-bao_cao_do_an}" <<'EOF'
import glob, os, sys, zipfile
for f in sorted(glob.glob(os.path.join(sys.argv[1], "Bao_cao_*.docx"))):
    x = zipfile.ZipFile(f).read("word/document.xml").decode()
    n = x.count('<w:highlight w:val="yellow"/>')
    print("  %s: %d yellow runs" % (os.path.basename(f), n))
EOF
}
build() {
    log "build after $1"
    "$PY" bao_cao_do_an/make_result_figures.py && node bao_cao_do_an/build_report.js && node bao_cao_do_an/build_tomtat.js
    local rc=$?
    log "build after $1: exit $rc"
    yellow_left
    return $rc
}
newest() { ls -t logs/*_"$1".log 2>/dev/null | head -1; }

if [ "${ONCE:-}" = "1" ]; then build "ONCE"; exit $?; fi

log "auto_fill start: HEAD $(git rev-parse --short HEAD); waiting for P6 (arena-p6test) and P7 (arena-p7bench)"
s6=wait; s7=wait
while :; do
    if [ $s6 = wait ]; then
        L6=$(newest p6_test_chain)
        if [ -n "$L6" ] && grep -q "P6 TEST chain done" "$L6"; then
            if [ -f runs/p6_test_decision.json ]; then build P6 && s6=filled || s6=build_failed
            else log "P6 chain done but runs/p6_test_decision.json missing (p6_decide.py printed NO DECISION): TEST cells stay yellow"; s6=no_decision; fi
        elif ! systemctl --user is-active -q arena-p6test; then
            log "arena-p6test is not running and its log has no 'P6 TEST chain done': TEST cells stay yellow"; s6=stopped
        fi
    fi
    if [ $s7 = wait ]; then
        L7=$(newest p7_bench_chain)
        if [ -n "$L7" ] && grep -q "P7 benchmark-DEV chain done" "$L7"; then
            if [ -f runs/p7_bench_compare.json ]; then build P7 && s7=filled || s7=build_failed
            else log "P7 chain done but runs/p7_bench_compare.json missing"; s7=no_json; fi
        elif [ $s6 != wait ] && ! systemctl --user is-active -q arena-p7bench; then
            log "arena-p7bench is not running and its log has no 'P7 benchmark-DEV chain done': P7 cells stay yellow"; s7=stopped
        fi
    fi
    if [ $s6 != wait ] && [ $s7 != wait ]; then break; fi
    sleep 60
done
log "auto_fill done: P6 $s6, P7 $s7"
