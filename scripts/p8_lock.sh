#!/bin/bash
# Lock PREREGISTRATION_P8.md (section 7) before the first P8 TEST trial: lock_commit = HEAD (the frozen code must be committed), sha256 of the sheet,
# the six checkpoints, the two reference-view directories and the frozen files.  Writes section 7 and commits the prereg.  Run once, after the DEV gate.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
P=PREREGISTRATION_P8.md
FROZEN="ports/common.py ports/detector_server.py ports/p05_cns.py ports/p07_vitvs.py ports/p17_odil.py arena/methods/ports.py arena/methods/act_lerobot.py arena/methods/act_i2.py"
dir_hash() { (cd "$1" && find -L . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64; }
git diff --quiet HEAD -- $FROZEN scripts/p8_test.sh scripts/p8_decide.py || { echo "commit the frozen files first"; exit 1; }
grep -q "^lock_commit:" $P && { echo "already locked"; exit 1; }
LOCK=$(git rev-parse HEAD)
{
  echo '```'
  echo "lock_commit: $LOCK"
  echo "locked/paper/test_C2.csv: $(sha256sum locked/paper/test_C2.csv | cut -c1-64)"
  for d in act_j0_s1000 act_j0_s2000 act_j0_s3000 act_w_s1000 act_w_s2000 act_w_s3000; do
      echo "$d: $(sha256sum runs/$d/checkpoints/last/pretrained_model/model.safetensors | cut -c1-64)"
  done
  for d in train_dev testobj; do echo "refs/$d: $(dir_hash runs/p8_refs/$d)"; done
  for f in $FROZEN scripts/p8_test.sh scripts/p8_decide.py; do echo "$f: $(sha256sum $f | cut -c1-64)"; done
  echo '```'
  echo "Khóa lúc $(date '+%F %T'). Từ đây chỉ được thêm vào §8."
} > /tmp/p8_lock_block.$$
python3 - "$P" /tmp/p8_lock_block.$$ <<'EOF'
import sys
p, blk = sys.argv[1], open(sys.argv[2]).read()
s = open(p).read()
a = s.index("## 7. Khóa"); b = s.index("## 8.")
head = s[:a].replace("Trạng thái: **NHÁP**", "Trạng thái: **ĐÃ KHÓA** (§7)")
s = head + "## 7. Khóa\n" + blk + "\n" + s[b:]
open(p, "w").write(s)
EOF
rm -f /tmp/p8_lock_block.$$
git add $P && git commit -q -m "PREREGISTRATION_P8 locked (section 7: lock commit $LOCK, sheet, checkpoints, reference views, frozen files)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git log --oneline -1
