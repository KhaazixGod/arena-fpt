#!/bin/bash
# Prints the lines that PREREGISTRATION_FINAL.md section 7 needs (hashes of the sheet, the parameter files, the three DP_W checkpoints) and the list of frozen files.
# Paste them into section 7, commit, then add "lock_commit: <that commit's sha1>" in a second commit (same procedure as scripts/m4_lock.sh).
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
echo "locked/final/test_C2.csv: $(sha256sum locked/final/test_C2.csv | cut -c1-64)"
echo "m4/m4_vs.env: $(sha256sum m4/m4_vs.env | cut -c1-64)"
echo "m4v2/m4v2.env: $(sha256sum m4v2/m4v2.env | cut -c1-64)"
for d in dp_w_s1000 dp_w_s2000 dp_w_s3000; do
    ck=runs/$d/checkpoints/last/pretrained_model
    echo "$d: $(sha256sum $ck/model.safetensors | cut -c1-64)"
    echo "$d/pretrained_model: $( (cd $ck && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | cut -c1-64)"
done
echo "frozen files: m4 m4v2 arena/methods/diffusion_i2.py arena/i2.py arena/dp_i2.py remote_server.py locked/final/test_C2.csv scripts/lib_chain.sh scripts/final_test.sh scripts/final_decide.py"
echo "git HEAD now: $(git rev-parse HEAD)"
