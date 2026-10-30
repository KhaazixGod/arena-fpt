# Arena: so sánh phương pháp gắp vật trên băng chuyền trong Isaac Sim (SO-101)

Mọi phương pháp chạy qua **một giao diện**, trên **cùng các tờ sắp xếp**, và trả metrics cùng định dạng với `dir1/g0_analyze.py`. Chỉ mô phỏng; mọi số mang nhãn `engine=isaac`, không trộn với số của tay thật.

| Tài liệu | Nội dung |
|---|---|
| `arena/methods/README.md` | cắm phương pháp của bạn hoặc của paper khác (3 cách) |
| `LABEL_RULES.md` | quy tắc gán thành công và nguyên nhân thất bại |
| `ARENA_SETUP_REPORT.md` | nhật ký từng giai đoạn kèm bằng chứng |
| `CLAUDE.md` | luật làm việc |

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
