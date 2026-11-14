#!/bin/bash
# E16 repair, 8/11 15:17: lane B's Isaac ran out of GPU memory (segfault, exit 139) in runs/e16_commit_c01 after 20 of 40 trials; its ACT server died on the abrupt
# disconnect (EOFError, fixed in remote_server.py), so the watchdog's retry got "connection refused" and run_arena still exited 0 (no trial run).
# This runs the 20 missing trials (dev_C1 L0, same arrangements, same model, same COMMIT setting) once lane B is free, verifies the count, then rebuilds the summaries.
# Re-running resumes; nothing is deleted.  Started as a systemd user unit (outside the VS Code snap scope).
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
CKPT=runs/act_i2_s1000/checkpoints/last/pretrained_model
OUT=runs/e16_commit_c01
rows() { echo $(( $(wc -l < "$1" 2>/dev/null || echo 1) - 1 )); }
echo "$(date +%T) waiting for lane B (repeat_r100: 20 trials) to finish"
while [ "$(rows runs/e16_repeat_r100/trials.csv)" -lt 20 ] && systemctl --user is-active --quiet arena-e16; do sleep 30; done
for attempt in 1 2 3 4 5; do
    [ "$(rows $OUT/trials.csv)" -ge 40 ] && break
    echo "$(date +%T) resume attempt $attempt, have $(rows $OUT/trials.csv)/40"
    ACT_CKPT=$CKPT ACT_REPLAN=10 ACT_COMMIT=1 env -u PYTHONPATH "$HOME/venvs/lerobot_data/bin/python" remote_server.py --factory arena.methods.act_i2:make_method \
        --name ACT_I2_COMMIT --port 6204 --path . --path ../cl0 --repeat > logs/$(date +%F_%H%M%S)_e16_server_6204.log 2>&1 &
    s=$!
    sleep 25
    mkdir -p $OUT; touch $OUT/.watchdog
    env -u PYTHONPATH -u VIRTUAL_ENV "$HOME/env_isaac/bin/python" -m arena.run_arena --objects sim --n 20 --out $OUT --report --methods REMOTE --method-arg remote=localhost:6204 \
        --cells dev_C0,dev_C1 --speeds L0 > logs/$(date +%F_%H%M%S)_e16_resume_c01.log 2>&1 &
    pid=$!
    while kill -0 $pid 2>/dev/null; do
        sleep 30
        new=$(ls -t "$OUT/trials.csv" "$OUT/.watchdog" 2>/dev/null | head -1)
        age=$(( $(date +%s) - $(stat -c %Y "$new") ))
        if [ "$age" -gt 300 ]; then echo "$(date +%T) stalled ${age}s, killing $pid"; kill $pid; sleep 20; kill -9 $pid 2>/dev/null; fi
    done
    wait $pid; echo "$(date +%T) run_arena exit $?, now $(rows $OUT/trials.csv)/40"
    kill $s 2>/dev/null; sleep 5
done
[ "$(rows $OUT/trials.csv)" -ge 40 ] && echo "$(date +%T) c01 complete (40/40)" || echo "$(date +%T) c01 STILL INCOMPLETE: $(rows $OUT/trials.csv)/40"
while systemctl --user is-active --quiet arena-e16; do sleep 60; done
env -u PYTHONPATH "$HOME/venvs/cl0/bin/python" scripts/e16_pair.py > logs/$(date +%F_%H%M%S)_e16_pair_final.txt 2>&1
env -u PYTHONPATH "$HOME/venvs/cl0/bin/python" scripts/e16_failure_modes.py COMMIT=runs/e16_commit_c23:REMOTE:ACT_I2_COMMIT COMMIT=runs/e16_commit_c01:REMOTE:ACT_I2_COMMIT > logs/$(date +%F_%H%M%S)_e16_failure_modes_after_final.txt 2>&1
echo "$(date +%T) final summaries written"
