# SETUP_REPORT — môi trường và kết quả kiểm (CL-0)

## 27/10/2026 — phiên 1: cài đặt (README_CL0 §0 bước 1)

### Máy
| Mục | Giá trị |
|---|---|
| OS | Ubuntu 24.04.5 LTS, kernel 7.0.0-38-generic |
| CPU / RAM / đĩa trống | Intel i9-10900 (20 luồng) / 46 GiB / 264 GB |
| GPU | NVIDIA GeForce RTX 3070 Ti 8 GB, driver 595.99.02 |
| Python hệ thống | 3.12.3 (`/usr/bin/python3`) |
| `PYTHONPATH` mặc định của terminal | trỏ vào `/opt/ros/jazzy/...` (ROS 2 Jazzy) → `scripts/env.sh` đã `unset` |
| `python3` trong PATH | `~/venv-ardupilot/bin/python3` (venv khác đang kích hoạt) → venv CL-0 tạo bằng `/usr/bin/python3` |

### Quyền và thiết bị (lúc kiểm, chưa cắm phần cứng)
| Mục | Trạng thái |
|---|---|
| nhóm `dialout` (serial) | CÓ |
| nhóm `video` (camera) | **CHƯA** → người dùng chạy `sudo usermod -aG video $USER`, đăng xuất/đăng nhập lại |
| `v4l2-ctl` | **CHƯA cài** → người dùng chạy `sudo apt install -y v4l-utils` |
| `/dev/video*` | không có (chưa cắm camera) |
| `/dev/ttyACM*`, `/dev/ttyUSB*` | không có (chưa cắm tay/băng) |
| file hiệu chuẩn LeRobot (`~/.cache/huggingface/lerobot/calibration/`) | không có thư mục này `[chưa kiểm: có thể bạn hiệu chuẩn ở máy khác hoặc đặt HF_LEROBOT_CALIBRATION]` |

### Venv
`/usr/bin/python3 -m venv ~/venvs/cl0`; pip 26.2.2. `pip install "lerobot[feetech]==0.6.1" pytest` (log: `logs/2026-10-27_160625_pip_install.log`); `pip check`: không xung đột.

| Gói | Phiên bản | Khoảng LeRobot 0.6.1 đòi (README §1) |
|---|---|---|
| lerobot | 0.6.1 | — |
| numpy | 2.2.6 | 2.0–2.2 ✓ |
| opencv-python-headless | 4.13.0.92 (không có `opencv-python`) | 4.9–4.13 ✓ |
| pyserial | 3.5 | — |
| torch / torchvision | 2.11.0+cu130 / 0.26.0; `cuda.is_available() = True` (RTX 3070 Ti) | — |
| pytest | 9.1.1 | — |

Import kiểm bằng tay: `lerobot.robots.so_follower.SO101Follower/SO101FollowerConfig`, `lerobot.robots.make_robot_from_config` có mặt; `HF_LEROBOT_CALIBRATION = ~/.cache/huggingface/lerobot/calibration`.

### Kết quả kiểm (chưa chạm phần cứng)
| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| `dir1/g0_analyze.py selftest` | 21/21 OK | chạy tay, 27/10 |
| `pytest -m "not slow"` | **204 qua**, 29 bỏ chọn, 18 s (có LeRobot thật trong venv) | `logs/2026-10-27_*_pytest_fast.log` |
| `pytest` (đủ) | **233 qua**, 4 phút 38 s | `logs/2026-10-27_161202_pytest_full.log` |
| `run_g0 --sim` với `configs/arr_dev_example.csv` | **5/5** `picked_hold_complete`, 29 s; ô `dev_sim` (không phải ô G0) | `runs/sim_check/`, `logs/2026-10-27_*_sim_g0.log` |

### Cấu hình
`cl0.toml` sinh bằng `python -m cl0.config > cl0.toml`, lúc đó **giống hệt mẫu** (README §0 bước 2). Sau đó đã sửa `[camera]` và `[belt]`: xem mục "phiên 1 (tiếp)" bên dưới.

## 27/10/2026 — phiên 1 (tiếp): quyết định phần cứng, cầu nối ROS 2, description

### Thông tin người dùng đưa (đang làm từ xa, chưa cắm được gì)
| Mục | Giá trị | Hệ quả |
|---|---|---|
| Hiệu chuẩn LeRobot (`lerobot-calibrate`) | **chưa chạy** | phải làm ở lab TRƯỚC `calibrate fk`; dùng LeRobot 0.6.1 của venv này (file vào `.../robots/so_follower/<robot_id>.json`) |
| Băng | Arduino **Uno/Nano**; muốn đi qua **ROS 2** | chọn phương án A: `so101_env/src/so101_belt_bridge` giữ cổng Arduino, mở pty `/tmp/cl0_belt` cho CL-0 |
| Camera | RealSense **D435i** (có depth), **1920×1080** | `cl0.toml`: 1920×1080, 30 fps, `fourcc = "YUYV"` `[chưa kiểm trên camera thật]`; CL-0 chỉ dùng ảnh màu qua V4L2, KHÔNG dùng depth (định nghĩa CL-0, kế hoạch §3.4; depth chỉ mở đường cho CL-2 tuỳ chọn) |
| Description | `/home/pread/Projects/so101_env/src` | package mới `so101_cell_description`; `so101_description` có sẵn KHÔNG đụng tới |

### Kiểm ROS 2 ↔ venv CL-0
`rclpy`, `std_msgs`, `sensor_msgs` (JointState) import và publish được trong venv numpy 2.2.6; **`cv_bridge` hỏng** ("compiled using NumPy 1.x"). ROS Jazzy dùng numpy 1.26 của hệ thống. ⇒ không đưa ảnh qua ROS vào CL-0; băng đi qua pty để không phải sửa mã CL-0.

### `cl0.toml` đã sửa (chưa đóng băng)
* `[camera]` width 1920, height 1080, fps 30, fourcc "YUYV" (device = 0 còn phải chọn khi cắm: nút màu của D435i).
* `[belt]` `kind = "counter"`, `serial_port = "/tmp/cl0_belt"`; `cmd_speed`/`cmd_stop`/`line_regex` giữ mặc định (= giao thức của cầu nối).

### Package mới trong `so101_env/src` (chưa commit git)
| Package | Kiểm | Kết quả |
|---|---|---|
| `so101_belt_bridge` | 8 test pytest (giao thức, Arduino giả, pty: hai chiều, không dội, xả tồn đọng, symlink); chạy thử đầu-cuối Arduino GIẢ ↔ cầu nối ↔ pty ↔ lớp `Belt` thật của CL-0 (venv) + ROS 2 | CL-0 lệnh 30 mm/s → đo 30,13 mm/s; `healthy` cả lúc đứng/chạy; 0 dòng hỏng; `/belt/steps` 99,9 Hz; `/belt/commanded` thấy lệnh của CL-0; lệnh ROS 500 xung/s → 0,0100 m/s; Ctrl-C gửi `V 0`, xoá symlink |
| `so101_cell_description` | 7 test pytest + `check_urdf` | URDF chính thức sha256 trùng bản CL-0 nhúng; khớp/link tay trùng nguyên văn; **hàm `_load_urdf` của CL-0 đọc URDF của cell ra đúng chuỗi nhúng (1e-12)**; TF `base_link→gripper_frame_link` ở q = 0 = (0,391; 0,000; 0,226) m = FK CL-0 (391,36; −0,01; 226,47) mm; `belt_moving` chạy theo `/belt/joint_states` |

### Phát hiện về mã CL-0 có sẵn (KHÔNG sửa, chỉ ghi lại)
`cl0/hw/belt.py::_rx_loop` đọc `serial.read(256)` với timeout 0,05 s ⇒ mỗi lần đọc chờ đủ 50 ms, chỉ giữ số đếm mới nhất và gán dấu thời gian lúc cửa sổ đóng: CL-0 lấy mẫu s(t) ở **20 Hz**, dấu thời gian trễ tối đa một chu kỳ báo của Arduino (≤ 10 ms ở 100 Hz ≈ 0,5 mm ở 50 mm/s). Phần trung bình được `calibrate belt` hấp thụ; phần dao động thì không. Đo được trong thử đầu-cuối: khoảng cách giữa các số đếm CL-0 nhận, trung vị 50,2 ms. Đã ghi yêu cầu firmware báo ≥ 100 Hz. Sửa (đọc theo `in_waiting`) là đổi lớp phần cứng của CL-0: chờ người dùng quyết.

## 27/10/2026 — phiên 1 (tiếp 2): trả lời của người dùng

| Mục | Người dùng báo | Kiểm / hệ quả |
|---|---|---|
| `v4l-utils`, nhóm `video` | đã làm | `v4l2-ctl 1.26.1` có; `getent group video` có `pread`, **nhưng phiên đăng nhập hiện tại chưa có nhóm** (`id -nG` không có `video`) ⇒ đăng xuất/đăng nhập lại (hoặc khởi động lại) trước khi mở camera |
| Firmware Uno | làm sau | được: `calibrate fk` và `calibrate board` không mở băng (`cl0/calibrate.py`: chỉ `cmd_belt` và `cmd_background` gọi `open_belt`). Phải có firmware trước `calibrate belt`. Băng vẫn phải ở **vị trí cuối** trước `board` |
| Lấy giới hạn khớp theo `so101_env/src` thay cho `lerobot-calibrate` | hỏi | **không được**, xem dưới |
| "90 độ" | độ mở kẹp? `[chưa rõ]` | CL-0 cần `perception.grasp.gripper_w_mm` bằng **mm** (khe giữa hai má ở `robot.gripper_open` = 60 trên thang 0–100 của LeRobot), đo bằng thước sau `lerobot-calibrate`. **Chưa điền**, giữ 40.0 |
| Bề rộng băng | 20 cm | `cl0.toml` `belt.width_mm` 150 → **200**; `so101_cell_description/config/cell.yaml` `width_mm` 200 |

### Vì sao không thay `lerobot-calibrate` bằng giới hạn trong URDF
* LeRobot 0.6.1 (`robots/so_follower/so_follower.py::calibrate`) đo trên tay thật: tư thế giữa → `Homing_Offset`, quét khớp → `range_min/max` (đơn vị xung encoder). `write_calibration` ghi các số này vào **EEPROM servo** (`Min/Max_Position_Limit`). Chúng phụ thuộc cách lắp từng servo; URDF không chứa.
* 0° của LeRobot = **giữa khoảng đã quét** (`motors_bus.py`: `mid = (min+max)/2`). URDF `so101_new_calib` (CL-0 dùng) giả định đúng quy ước này. Giới hạn trong `so101_description` là quy ước khác: điểm giữa `joint_1..4` = −64,2°, 21,0°, −9,3°, 68,0° (`so101.urdf.xacro`), và `so101.urdf` cùng package lại ghi ±90° ⇒ hai file mâu thuẫn nhau. Dùng các số này sẽ làm lệch FK.
* Giới hạn mềm của CL-0 đã có sẵn: giới hạn URDF chính thức ± `robot.joint_margin_deg` (3°), cộng `SafetyError` khi lệnh nhảy > 45° (README §7).

### Bề rộng 200 mm và vùng với tới `[tính từ mô hình động học, chưa kiểm trên tay thật]`
Gọi thẳng `cl0.tune.belt_reach_table` + `plan_belt` (cùng hàm `tune reach` dùng) với φ = 90°, kẹp thẳng đứng, độ cao mặc định, `belt.speed_mm_s` 50 ⇒ cần đoạn nhặt ≥ 140 mm; script `/tmp/claude-1000/-home-pread-Projects-dir1-tools/daa32be4-6a9c-48d2-a2fe-c09de4009627/scratchpad/reach200/plan.py`.

| Mặt băng so với mặt đế | đoạn nhặt dài nhất phủ đủ 200 mm | tốc độ tối đa (chưa trừ thời gian xác nhận vật) | tâm băng cách trục pan |
|---|---|---|---|
| 0 mm | 48 mm | — | 120 mm |
| −20 mm | 88 mm | — | 130 mm |
| −40 mm | 122 mm | ≈ 44 mm/s | 130 mm |
| −50 mm | 184 mm | ≈ 66 mm/s | 190 mm |
| −60 mm | 192 mm | ≈ 69 mm/s | 190 mm |
| −80 mm | 244 mm | ≈ 87 mm/s | 180 mm |

So sánh: băng 150 mm ở −20 mm đã cho 252 mm. ⇒ với băng 200 mm, hạ mặt băng thấp hơn đế tay **≥ 50 mm** (hoặc chạy chậm hơn). `make_arrangements.py` rải vật trên cả bề rộng (cách mép 10 mm + bán kính), nên mép xa nằm ngoài tầm với là thất bại thật của mọi phương pháp. Kiểm lại bằng `tune reach` sau `calibrate board`.
