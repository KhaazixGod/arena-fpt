#!/bin/bash
# Prints the lines that PREREGISTRATION_M4.md section 7 needs (hashes of the sheet, the three DP_W checkpoints, the corrector parameters) and the list of frozen files.
# Paste them into section 7, commit, then add "lock_commit: <that commit's sha1>" in a second commit (same procedure as scripts/p8_lock.sh).
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
echo "locked/m4/test_C2.csv: $(sha256sum locked/m4/test_C2.csv | cut -c1-64)"
echo "m4/m4_vs.env: $(sha256sum m4/m4_vs.env | cut -c1-64)"
for d in dp_w_s1000 dp_w_s2000 dp_w_s3000; do
    ck=runs/$d/checkpoints/last/pretrained_model
    echo "$d: $(sha256sum $ck/model.safetensors | cut -c1-64)"
    echo "$d/pretrained_model: $( (cd $ck && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64)"
done
echo "frozen files: m4 arena/methods/diffusion_i2.py arena/methods/act_i2.py arena/i2.py arena/dp_i2.py remote_server.py locked/m4/test_C2.csv scripts/lib_chain.sh scripts/m4_wait.sh scripts/m4_test.sh scripts/m4_decide.py"
echo "git HEAD now: $(git rev-parse HEAD)"
