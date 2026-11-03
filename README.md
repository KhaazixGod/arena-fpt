# Arena: so sánh phương pháp gắp vật trên băng chuyền trong Isaac Sim (SO-101)

Mọi phương pháp chạy qua **một giao diện**, trên **cùng các tờ sắp xếp**, và trả metrics cùng định dạng với `dir1/g0_analyze.py`. Chỉ mô phỏng; mọi số mang nhãn `engine=isaac`, không trộn với số của tay thật.

| Tài liệu | Nội dung |
|---|---|
| `arena/methods/README.md` | cắm phương pháp của bạn hoặc của paper khác (3 cách) |
| `LABEL_RULES.md` | quy tắc gán thành công và nguyên nhân thất bại |
| `ARENA_SETUP_REPORT.md` | nhật ký từng giai đoạn kèm bằng chứng |
| `CLAUDE.md` | luật làm việc |

## Cài trên máy khác
Code tìm CL-0 và bộ công cụ G0 **cạnh** thư mục này (`../cl0`, `../dir1`); git giữ bản sao của chúng trong `deps/` (cùng hai file kế hoạch).
```bash
git clone -b <nhánh> https://github.com/KhaazixGod/arena-fpt.git arena
cd arena && python setup_workspace.py     # chép deps/cl0 -> ../cl0, deps/dir1 -> ../dir1 (không ghi đè); in hash đóng băng CL-0, phải là 006af1c9…
```
Môi trường đã dùng (Linux, RTX 3070 Ti 8 GB):

| môi trường | gói chính | dùng cho |
|---|---|---|
| Isaac (`~/env_isaac`, Python 3.12) | `isaacsim 6.0.0.1`, torch 2.11, numpy 2.3, opencv-python-headless 4.13 | `run_arena`, `calib_from_scene.py` |
| `~/venvs/cl0` (Python 3.12) | numpy 2.2, opencv-python-headless 4.13, lerobot 0.6.1, pytest | test, báo cáo, CL-0 |
| `~/venvs/lerobot_data` | thêm `datasets 4.8`, `accelerate 1.15` | đổi demo sang LeRobotDataset, huấn luyện ACT, phục vụ ACT qua `remote_server.py` |

Không có trong git (quá 100 MB/file hoặc sinh lại được): demo thô và bộ LeRobot của `runs/e6_demos_real` (ghi lại bằng `scripts/e6_record_400.sh` rồi `to_lerobot.py`), checkpoint ACT `runs/act_j0_s1000` (huấn luyện lại ≈ 2,3 giờ, lệnh trong `ARENA_SETUP_REPORT.md` E11), GT từng tick (`*_gt.npz`) của các lượt từ 1/11. Chạy song song 2 Isaac đã kiểm cho kết quả trùng (`runs/e11_parallel_check`). Trên Windows: hash đóng băng CL-0 dùng dấu phân cách đường dẫn của hệ điều hành nên sẽ **khác** 006af1c9… dù mã y hệt `[chưa kiểm trên Windows]`; so mã bằng `git diff`, đừng so hash.

## Chạy nhanh
```bash
cd ~/Projects/dir1_tools/arena
ISAAC="env -u PYTHONPATH -u VIRTUAL_ENV $HOME/env_isaac/bin/python"

# 1. (một lần, hoặc sau khi đổi cảnh/camera) hiệu chuẩn từ cảnh: runs/calib/calib.json + background.npz
$ISAAC calib_from_scene.py --out runs/calib

# 2. chạy so sánh, rồi in báo cáo
$ISAAC -m arena.run_arena --methods CL0,ORACLE,NOOP --cells dev_C0,dev_C2 --speeds L0,L0.25 --n 20 --objects sim --out runs/<tên> --report
env -u PYTHONPATH ~/venvs/cl0/bin/python -m arena.report runs/<tên>/trials.csv --ref CL0

# 3. test (không cần Isaac)
env -u PYTHONPATH ~/venvs/cl0/bin/python -m pytest tests -q
```

Tuỳ chọn hay dùng:

| tuỳ chọn | tác dụng |
|---|---|
| `--video` / `--debug-video` | quay camera thật / camera chéo để xem |
| `--depth` | phương pháp nhận thêm ảnh độ sâu lý tưởng |
| `--no-hard-reset` | tắt việc dựng lại cảnh PhysX trước mỗi lượt (mặc định là có dựng lại, nên kết quả không phụ thuộc thứ tự chạy; không tốn thêm thời gian) |
| `--shuffle-seed` | xáo thứ tự lượt (đo M8) |
| `--scene-set sec.key=giá_trị` | đổi một thông số cảnh cho lần chạy này |
| `--record-demos DIR` | ghi demo (E6) |

Chạy lại cùng lệnh thì **tiếp tục** từ chỗ dở.

## Thành phần

| | |
|---|---|
| `configs/scene.toml` | cảnh: vật lý 300 Hz, băng (rộng 200 mm, ngang mặt đế, dải đặt vật x = 130–230 mm), camera, tay, các giả định vật lý |
| `configs/arena.toml` | cấu hình CL-0 cho sim = `cl0.toml` + 11 khác biệt có chú thích |
| `arena/world.py`, `arena/platform.py` | Isaac + nền tảng lockstep (cài `cl0.runner.Platform`: camera trễ 0,1 s, băng có bộ đếm xung, 50 Hz) |
| `arena/objects.py`, `arena/objects_gen.py` | vật tạm (6) và bộ vật sinh theo thủ tục (36: train 20 / dev 6 / test 10, test có ba dạng khó) |
| `arrangements/` | tờ sắp xếp. `arrangements/sim/`: train/dev cho bộ 36 vật. `locked/`: **test, không chạy khi người dùng chưa ra lệnh** |
| `arena/run_arena.py`, `arena/labeler.py`, `arena/report.py` | chạy, gán nhãn, báo cáo |
| `arena/methods/` | `CL0`, `NOOP`, `ORACLE` (đặc quyền: GT), `CL0_YAW` (không phải baseline), `REMOTE`, bộ chuyển phát hiện kẹp trên ảnh |
| `remote_server.py` | chạy phương pháp ở môi trường Python khác |
| `to_lerobot.py` | đổi demo sang LeRobotDataset (chạy trong `~/venvs/cl0`) |

## Ô và tốc độ
- **Ô** = `<split>_<mức clutter>`, ví dụ `dev_C2`. C0: 1 vật; C1: 2 vật cách xa; C2: 3–4 vật gần (10–25 mm); C3: 4–5 vật gần như chạm (0–3 mm). Bảng `LEVELS` lấy từ `dir1/make_arrangements.py`.
- **Tốc độ:** `L0` (băng đứng yên), `L0.25` (37,5 mm/s), `L0.5` (75 mm/s), với L = v·τ/w, w = 60 mm, τ = 0,4 s `[giả định]`, hoặc `v<mm/s>`. L = 1,0 vượt tầm với của CL-0 ở hình học này.

## Giới hạn hiện tại
Xem mục 5 của `arena/methods/README.md`: lực, tốc độ và ma sát của kẹp là giả định; hiệu chuẩn hoàn hảo; một camera cố định.

Trạng thái các cổng S0 và các vấn đề còn mở nằm ở cuối `ARENA_SETUP_REPORT.md`.
