# Dùng:  source scripts/env.sh        (trong MỖI terminal mới, trước khi chạy lệnh `python -m cl0.…`)
#
# * kích hoạt venv (mặc định ~/venvs/cl0; đổi bằng biến CL0_VENV), chuyển vào thư mục dự án cl0/;
# * `unset PYTHONPATH`: nếu terminal đã source ROS 2 (setup.bash) thì PYTHONPATH trỏ vào /opt/ros và dễ làm numpy/cv2 lẫn nhau;
# * PYTHONUNBUFFERED=1: để lời nhắc "Enter >" hiện ngay khi đầu ra đi qua `tee`;
# * định nghĩa `cl0log <tên> <lệnh…>`: chạy lệnh như bình thường (vẫn gõ Enter/Ctrl-C được) và ghi toàn bộ đầu ra vào
#   logs/<ngày_giờ>_<tên>.log để Claude Code đọc lại. `tee -i` bỏ qua Ctrl-C nên khi bạn nhấn Ctrl-C chương trình vẫn kịp
#   dọn dẹp (dừng băng, mở kẹp, về nhà) và phần chữ đó vẫn vào log.
#
#   ví dụ:  cl0log board python -m cl0.calibrate board --config cl0.toml --cols 9 --rows 6 --square-mm 20

_CL0_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CL0_VENV="${CL0_VENV:-$HOME/venvs/cl0}"
if [ ! -f "$CL0_VENV/bin/activate" ]; then
  echo "Không thấy venv tại $CL0_VENV (tạo theo README_CL0.md mục 1, hoặc đặt CL0_VENV=<đường dẫn>)." >&2
  return 1 2>/dev/null || exit 1
fi
# shellcheck disable=SC1091
source "$CL0_VENV/bin/activate"
unset PYTHONPATH
export PYTHONUNBUFFERED=1
cd "$_CL0_ROOT" || return 1

cl0log() {
  if [ "$#" -lt 2 ]; then
    echo "dùng: cl0log <tên> <lệnh…>    ví dụ: cl0log lag python -m cl0.calibrate lag --config cl0.toml" >&2
    return 2
  fi
  local name="$1"; shift
  mkdir -p logs
  local f; f="logs/$(date +%F_%H%M%S)_${name}.log"
  printf '$ %s\n' "$*" | tee "$f"
  "$@" 2>&1 | tee -i -a "$f"
  local rc="${PIPESTATUS[0]}"
  echo "[thoát mã $rc]" | tee -a "$f"
  return "$rc"
}
