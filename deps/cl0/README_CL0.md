# CL-0 — baseline mô-đun cho G0 (SO-101 + băng chuyền + camera eye-to-hand)

Cập nhật 27/10/2026. Đây là cài đặt **tham chiếu** của CL-0 trong §3.4 của `KE_HOACH_HUONG_1.md`: hiệu chuẩn camera → mặt băng, tách nền, điểm kẹp bằng cực đại biến đổi khoảng cách, luật "xuôi dòng nhất trong vùng với tới", vị trí vật trong hệ băng, và **bộ thực thi hệ băng dùng chung với I2** (IK + s(t)).

> **Trạng thái trung thực.**
> * **Đã làm và đã kiểm:** toàn bộ logic (nhận thức, chọn vật, theo dõi trong hệ băng, bộ thực thi, máy trạng thái), các lệnh hiệu chuẩn, bộ chạy G0. Chạy trong **mô phỏng động học** và **"phòng lab ảo"** (camera, băng, tay, người vận hành ảo, thời gian ảo), cộng test với **thiết bị giả** (serial, robot, camera). Số test và môi trường: §10.
> * **Đã đối chiếu bằng đọc mã nguồn:** API LeRobot 0.6.1 (tên lớp/khoá, bật–tắt torque, quy ước độ). Không chạy robot.
> * **Chưa có dòng nào chạm robot, băng hay camera thật của bạn.** Chỗ rủi ro nhất khi chạy lần đầu: firmware băng của bạn, định nghĩa TCP của má kẹp, hiệu chuẩn LeRobot của tay, V4L2 của camera (§10.5).
> * Mô phỏng là **động học** (không ma sát, không đẩy vật). Nó chứng minh logic, khung toạ độ và định thời *có thể* đúng; nó **không** dự đoán tỉ lệ thành công thật.

---

## 0. Việc bạn phải làm (theo thứ tự)

| # | Việc | Mục | Ước lượng `[ước lượng]` |
|---|---|---|---|
| 1 | Cài đặt, chạy test, thử `--sim` với `configs/arr_dev_example.csv` | §1, §9 | 30–60 phút (tải LeRobot/torch lâu nhất) |
| 2 | Điền cấu hình | §4 | 1–2 giờ |
| 3 | `calibrate fk` (kiểm động học với thước và mặt bàn) | §5.1 | 30 phút |
| 4 | `board` → `belt` → `background` → `lag` (+ `intrinsics` nếu ảnh méo) | §5 | 2–3 giờ lần đầu |
| 5 | Đặt băng đúng vùng tay với tới; xem nhận thức | §6 | 1 giờ |
| 6 | Lượt tĩnh (`--speed 0`), rồi băng chậm | §7 | 1–2 giờ |
| 7 | Tinh chỉnh trên vật/sắp xếp **dev**, **tối đa 2 ngày làm việc**, rồi **đóng băng** | §8 | ≤ 16 giờ |
| 8 | Chạy G0 | §9 | theo kế hoạch |

**Thứ tự cơ khí.** Băng, camera và đế tay phải ở **vị trí cuối** trước bước 4: dời bất kỳ thứ nào sau `board` là phải làm lại bước 4. `tune reach` (bước 5) cần `calib.json` và hướng băng nên chỉ chạy được sau bước 4; vì vậy hãy đặt băng sơ bộ bằng thước theo đầu §6 ngay từ đầu, và coi bước 5 là bước kiểm lại.

Nếu bước 3 hoặc 4 ra số xấu thì **dừng và sửa ở đó**: sai số hiệu chuẩn đi thẳng vào tỉ lệ thành công của CL-0 và làm baseline yếu một cách không công bằng với chính sách học.

---

## 1. Cài đặt (Ubuntu 24.04, Python 3.12)

```bash
sudo apt install -y python3-venv v4l-utils          # Ubuntu 24.04 có sẵn Python 3.12
sudo usermod -aG dialout,video $USER                # cổng serial + camera; đăng xuất/đăng nhập lại
python3 -m venv ~/venvs/cl0 && source ~/venvs/cl0/bin/activate
pip install "lerobot[feetech]==0.6.1"               # cho robot thật; bản mình đã đối chiếu mã; kéo theo torch (vài GB). KHÔNG cần cho test/mô phỏng
pip install pytest
tar xzf dir1_tools.tar.gz                           # ra: dir1/ (công cụ kế hoạch), cl0/ (dự án CL-0), KE_HOACH_HUONG_1.md
cd cl0                                              # thư mục dự án (chứa gói cl0/, configs/, tests/). Chạy MỌI lệnh `python -m cl0.…` từ đây;
                                                    # không cần `pip install` gói này. dir1/ nằm ở ../dir1
python -m pytest -m "not slow"                      # 204 test, ≈ 12–15 giây trên sandbox 2 lõi của mình
```

* **Mỗi terminal mới:** `source scripts/env.sh` — kích hoạt venv (`~/venvs/cl0`, hoặc `$CL0_VENV`), `cd` vào thư mục dự án, `unset PYTHONPATH` (terminal đã source ROS 2 thì `PYTHONPATH` trỏ vào `/opt/ros` và dễ làm lẫn numpy/cv2), đặt `PYTHONUNBUFFERED=1`. Nó còn định nghĩa `cl0log <tên> <lệnh…>`: chạy lệnh bình thường (vẫn gõ Enter, vẫn Ctrl-C) và ghi toàn bộ đầu ra vào `logs/<ngày_giờ>_<tên>.log`, ví dụ `cl0log lag python -m cl0.calibrate lag --config cl0.toml`. Dùng `tee -i` nên Ctrl-C vẫn để chương trình kịp dọn dẹp (dừng băng, mở kẹp, về nhà) và phần chữ đó vẫn vào log.
* Chỉ để chạy test/mô phỏng (không robot): `pip install numpy opencv-python-headless pytest` (đủ; các môi trường test của mình không có pyserial). `pyserial` chỉ cần khi mở băng thật qua serial, và `lerobot[feetech]` đã kéo theo nó; nếu thiếu, mã báo "thiếu pyserial".
* LeRobot 0.6.1 đòi **Python ≥ 3.12, numpy 2.0–2.2, opencv-python-headless 4.9–4.13** (đọc từ metadata của gói). **Đừng cài thêm `opencv-python`** vào cùng venv (hai gói đều cung cấp `cv2`, dễ xung đột). Bản headless không có cửa sổ: `tune watch --show` sẽ lỗi, hãy bỏ `--show` và xem ảnh lưu trong thư mục `--out`.
* `python -m pytest` (không lọc) chạy thêm các test vòng kín và phòng lab ảo: 233 test (204 nhanh + 29 chậm), 4–5 phút trên sandbox 2 lõi của mình.
* Môi trường mình đã chạy test (26–27/10/2026, lần cuối ngày 27/10 đúng mã trong gói). **LeRobot không được cài trong các môi trường này**; test dùng robot/camera/băng giả. Môi trường B chỉ cho biết phiên bản numpy/OpenCV nằm trong khoảng LeRobot 0.6.1 yêu cầu:

  | | Python | numpy | OpenCV | Kết quả |
  |---|---|---|---|---|
  | A (numpy cũ, ngoài khoảng của LeRobot) | 3.12.3 | 1.26.4 | opencv-python-headless 4.11.0 | bộ nhanh: 204 qua, 29 bỏ qua, 11 giây |
  | **B (trong khoảng của LeRobot 0.6.1)** | 3.12.3 | 2.2.6 | opencv-python-headless 4.12.0 | đủ: **233 qua**, 4 phút 11 giây |
  | C (mới hơn khoảng đó) | 3.13.16 | 2.5.3 | OpenCV 5.0.0 | đủ: **233 qua**, 4 phút 23 giây |

  Lần chạy ở môi trường B trong bảng có thêm `pyserial` thật và một gói `lerobot` **giả** (chỉ có `lerobot.robots.RobotConfig` và `make_robot_from_config`) trong `PYTHONPATH`, để mô phỏng máy đã cài LeRobot. Cách này đã bắt một test chỉ đúng khi lerobot vắng mặt (`make_so101` khi thiếu lerobot); đã sửa, và test qua cả khi có lẫn không có gói đó.

* Đường dẫn `calib.json`, `background.npz` trong cấu hình là **tương đối theo thư mục đang đứng** (không theo file cấu hình): chạy mọi lệnh từ cùng một thư mục, hoặc dùng đường dẫn tuyệt đối.
* Bản đồ vùng với tới được lưu cache ở `~/.cache/cl0` (dựng lần đầu ≈ 4 giây trên máy sandbox của mình; máy bạn `[chưa đo]`).
* `cl0.freeze` băm mọi file `*.py` trong gói `cl0/` (kể cả `hw/`; trừ `sim/`). **Đừng sửa file nào trong gói sau khi đóng băng** (§8).

---

## 2. Có gì trong gói

```
cl0/
  config.py        cấu hình (dataclass ↔ TOML; khoá lạ = lỗi). `python -m cl0.config` in mẫu đầy đủ
  geometry.py      homography ảnh → mặt băng, khung băng (a, b), ảnh "nhìn từ trên" (Rectifier), khớp bàn cờ → W, hướng băng/mm-xung
  kinematics.py    FK từ URDF so101_new_calib + IK số cho kẹp thẳng đứng + yaw
  reach.py         bản đồ vùng TCP với tới theo độ cao (chọn vật, đặt băng)
  perception.py    nền băng trống → mặt nạ → thành phần → điểm kẹp
  grasp.py         cực đại DT (cao nguyên, gần tâm), trục khép ⟂ PCA, bề ngang dọc trục khép
  tracker.py       gộp quan sát trong HỆ BĂNG (p_b = p_w − s·û hằng số) bằng trung vị
  executor.py      BeltExecutor: bộ lọc tới hạn trong hệ băng + dẫn trước lead_s + tích phân bù lag_ki + IK nóng   ← dùng chung với I2
  controller.py    CL0Controller: WAIT → APPROACH → DESCEND → CLOSE → LIFT → MOVE_HOLD → HOLD → RELEASE → RETURN → DONE + luật chọn vật
  runner.py        vòng điều khiển một lượt trên một "Platform" (thật hoặc ảo)
  system.py        dựng cả chồng từ cấu hình + file hiệu chuẩn; băm mã/cấu hình
  types.py, viz.py kiểu dữ liệu dùng chung; lớp phủ để xem/ghi video
  hw/              arm.py (LeRobot), belt.py (serial/mô hình), camera.py (V4L2), platform.py (nhịp + kiểm tra mất liên lạc)
  calibrate.py     fk | intrinsics | board | belt | background | lag      (calib_tools.py: phần tính thuần, có test)
  tune.py          reach | watch      (đặt băng, xem nhận thức; không ra lệnh cho tay)
  freeze.py        đóng băng mã + cấu hình (sha256) → frozen.json
  run_g0.py        chạy G0: tờ đặt vật → lượt → người thử chấm → CSV đúng định dạng g0_analyze.py
  arrangements.py, placement.py   đọc tờ sắp xếp; vẽ ảnh/bảng đặt vật
  sim/             mô phỏng động học + phòng lab ảo cho calibrate/tune (KHÔNG nằm trong băm đóng băng)
configs/           config_template.toml (sinh tự động, luôn khớp mã), sim_test.toml, arr_dev_example.csv
tests/             pytest (§10)
scripts/env.sh     `source scripts/env.sh`: venv + hàm `cl0log` ghi đầu ra vào logs/ (§1)
```

---

## 3. Quy ước toạ độ (đọc kỹ — nửa số lỗi "tay đi lệch" nằm ở đây)

* **W** = khung `base_link` của URDF SO-101 (`so101_new_calib.urdf`): gốc ở mặt gắn đế, `x` ra phía trước khi pan = 0, `y` sang trái nhìn từ sau robot, `z` lên. Đơn vị mm, độ. Trục pan nằm ở (x, y, z) ≈ (38,8; 0; 62,4) mm.
* **Hướng băng** φ: góc của `û = (cos φ, sin φ)` trong W (hướng băng CHẠY, tức hướng vật đi). `v̂ = (−sin φ, cos φ)` = **bên trái chiều băng chạy**.
* **Toạ độ băng** của điểm `p` (W): `a = p·û`, `b = p·v̂`. Độ dịch băng `s(t)` (mm) tính từ lúc bắt đầu; **vị trí trong hệ băng** `p_b = p_w − s·û` là hằng số khi vật không trượt.
* **Trục khép** θ: góc của đường nối hai má kẹp so với `û`, mod 180°, ngược chiều kim đồng hồ nhìn từ trên xuống. Yaw trong W = φ + θ.
* **Tờ sắp xếp** (`arr_*.csv`, ảnh `placement_<id>.png`): `x_mm` dọc băng so với vật đầu (dương = về phía hạ lưu); `y_mm` từ **mép TRÁI** băng nhìn theo chiều băng chạy; `yaw_deg` ngược chiều kim đồng hồ nhìn từ trên xuống so với hướng băng chạy. Trong ảnh: băng chạy sang phải, mép trái ở trên, yaw dương hướng lên.
* Mặt băng nên **thấp hơn mặt đế robot** (mô phỏng dùng z = −40 mm trong W). `tune reach` in nhận xét "THẤP hơn đế — tốt" khi z mặt băng < −15 mm, ngược lại "CAO ngang đế — vùng với tới thẳng đứng ở độ cao nhấc rất hẹp".

---

## 4. Cấu hình

```bash
python -m cl0.config > cl0.toml      # mẫu đầy đủ, mọi khoá có chú thích, luôn khớp mã
```

Chỉ cần giữ các khoá bạn muốn đổi; khoá vắng lấy mặc định; **khoá gõ sai tên → lỗi** (không bị bỏ qua lặng lẽ).

| Mục | Phải chỉnh | Cách đo / chọn |
|---|---|---|
| `[camera]` | `device`, `width`, `height`, `fps`, `fourcc` (mặc định 640×480, MJPG, 30 fps); `latency_s` | độ phân giải **phải giống lúc hiệu chuẩn**; `v4l2-ctl --list-devices`. `latency_s` do `calibrate belt` đo |
| `[belt]` | `kind`, `serial_port`, `serial_baud`, `cmd_speed`, `cmd_stop`, `line_regex`, `serial_open_delay_s`, `width_mm`, `speed_mm_s`; `mm_per_step` (do `calibrate belt` đo); `textured`, `period_mm` | xem bên dưới |
| `[robot]` | `port`, `robot_id`, `tcp_offset_mm`, `home_q_deg`, `hold_q_deg`, `gripper_open` (+ `gripper_closed`, `gripper_held_margin`) | xem bên dưới |
| `[perception.grasp]` | `gripper_w_mm`, `width_margin_mm` | `gripper_w_mm` = khe hữu dụng (mm) giữa hai má khi `gripper.pos = gripper_open`, đo bằng thước kẹp |
| `[executor]` | `lead_s` (từ `calibrate lag`), `a_pick_min/max` (từ `tune reach`) | |

**Băng.** Mặc định `kind = "model"` (không phản hồi). Nên dùng **`kind = "counter"`** nếu vi điều khiển báo số xung tích luỹ về PC: PC đọc bằng `line_regex` (nhóm 1 = số xung), nhận lệnh tốc độ theo mẫu `cmd_speed` (trường `{steps_per_s}` và `{v_mm_s}`) và `cmd_stop`. Mặc định (chỉ là ví dụ của mình): gửi `V <xung/giây>\n`, dừng bằng `V 0\n`, đọc các dòng dạng `S 12345`. **Firmware của bạn khác thì sửa 3 chuỗi đó trong TOML, không cần sửa mã.**
`serial_open_delay_s` (mặc định 2 s): Arduino/ESP tự reset khi mở cổng serial và bỏ qua lệnh lúc khởi động; mã chờ rồi xoá bộ đệm nhận.
`kind = "model"`: s(t) tính từ lệnh + dốc gia tốc `accel_mm_s2` + trễ `cmd_delay_s`; **chỉ dùng được với băng trơn** (cần hiệu `s(t_now) − s(t_img)`), và `mm_per_step` phải điền tay từ cơ khí (hoặc firmware nhận trực tiếp mm/s qua `{v_mm_s}`); `calibrate belt` khi đó chỉ báo tốc độ đo được bằng ảnh để bạn so với lệnh. Băng có texture (`textured = true`) bắt buộc `kind = "counter"` và `period_mm > 0`.
Với `counter`, nếu trong lúc băng chạy mà không có dòng đếm mới trong 0,5 s (sau 1,5 s chờ khởi động + dốc tăng tốc), lượt bị cắt với `BeltCommError` (in số dòng khớp/không khớp `line_regex` và dòng cuối để bạn thấy ngay firmware gửi gì).

**Robot.**
* `robot_id` phải đúng tên bạn đã dùng khi `lerobot-calibrate`. **File hiệu chuẩn nằm ở `<HF_LEROBOT_CALIBRATION>/robots/so_follower/<robot_id>.json`** (LeRobot 0.6.1; mặc định `~/.cache/huggingface/lerobot/calibration/`), còn **bản LeRobot cũ lưu ở `.../robots/so101_follower/`**. Hiệu chuẩn bằng bản cũ thì 0.6.1 không thấy file và sẽ tự hiệu chuẩn lại, ghi đè thanh ghi lệch-gốc của động cơ (làm lệch "0°" so với tay leader và dữ liệu cũ). Vì vậy CL-0 **dừng với lỗi trước khi kết nối** nếu thiếu file (kèm chỉ dẫn `cp` khi thấy file cùng tên ở thư mục cũ). Nếu LeRobot thấy hiệu chuẩn trong động cơ lệch file, nó **tự hỏi bằng `input()`**: nhấn Enter = dùng file hiệu chuẩn đã lưu; chỉ gõ `c` khi bạn thật sự muốn hiệu chuẩn lại (rồi làm lại cả §5 và hiệu chuẩn tay leader).
* `home_q_deg`, `hold_q_deg` trong file mẫu **chỉ là ví dụ của mình, chưa kiểm là an toàn trên máy bạn**. Cách đặt: tắt torque, đỡ tay tới tư thế bạn muốn (home: tay không che camera, cách xa băng và vật; hold: tay giơ vật lên cao), chạy `calibrate fk` và chép dãy `q=` in ra. Ngay sau khi kết nối, `run_g0` cho tay **tự đi tới `home_q_deg`** trong ≥ 3 s.
* `gripper_open` là giá trị `gripper.pos` (0–100) khi mở để kẹp; `gripper_w_mm` là khe thật tại giá trị đó. Mở tay kẹp bằng tay tới khi `fk` in `gripper=` đúng `gripper_open`, rồi đo khe.
* **`tcp_offset_mm`** = điểm (trong khung `gripper_frame_link`: z = hướng tiến vào, x = trục khép, y = bản lề) mà bộ điều khiển đưa lên **điểm kẹp của vật**. Mặc định (0, 0, 0) = gốc khung đó. SO-101 chỉ có **một má động**, nên "tâm kẹp" không hiển nhiên: nếu TCP đặt đúng mũi má cố định thì khi hạ xuống, má cố định sẽ đè lên vật; cần dịch TCP về giữa khe mở một lượng ≈ `gripper_w_mm / 2` theo trục khép (dấu + hay − tuỳ má động nằm phía nào so với trục x công cụ; `calibrate fk` in vectơ "khép" trong W để bạn xác định). **Mình chưa biết gốc khung nằm đâu trên má kẹp máy bạn `[chưa kiểm]`; đây là việc phải xác nhận bằng mắt ở lượt tĩnh (§7).** `calibrate board` yêu cầu chạm bằng chính điểm TCP đã khai ở đây, nên khai `tcp_offset_mm` trước khi chạy `board` và đừng đổi giữa chừng (đổi thì hiệu chuẩn lại).
* `max_relative_target`: 0 = không dùng bộ chặn của LeRobot (bộ thực thi đã tự chặn tốc độ khớp ở `q_dot_max_deg_s` = 150°/s).

---

## 5. Hiệu chuẩn (thứ tự cố định)

Mỗi lệnh in dòng `KẾT QUẢ` và việc cần chép vào cấu hình. `--help` của từng lệnh có giải thích tham số.

```bash
python -m cl0.calibrate fk          --config cl0.toml     # 5.1  kiểm FK với thước (torque TẮT, bạn đỡ tay; Ctrl-C để thoát)
python -m cl0.calibrate intrinsics  --config cl0.toml     # (tuỳ chọn) gỡ méo ống kính => intrinsics.npz; nếu làm thì LÀM LẠI các bước sau
python -m cl0.calibrate board       --config cl0.toml --cols 9 --rows 6 --square-mm 20     # 5.2  => calib.json
python -m cl0.calibrate belt        --config cl0.toml --speed <xung/giây hoặc mm/s>        # 5.3
python -m cl0.calibrate background  --config cl0.toml     # 5.4  => background.npz (+ ảnh xem trước)
python -m cl0.calibrate lag         --config cl0.toml     # 5.5  => gợi ý executor.lead_s
```

### 5.1 `fk` — kiểm động học
In liên tục `q`, `gripper`, TCP (x, y, z trong W), hướng tiến vào, hướng khép và yaw khi bạn kéo tay. Kiểm:
1. **Mặt bàn:** nếu đế robot đặt trực tiếp trên mặt bàn, chạm điểm TCP vật lý xuống mặt bàn → `z` ≈ 0 (mặt gắn đế). Lệch vài mm là bình thường (tấm đế, độ dày); lệch cả cm ⇒ `tcp_offset_mm[2]` hoặc hiệu chuẩn sai.
2. **Thước:** khoảng cách ngang từ trục pan (x ≈ 38,8; y = 0) tới TCP ở 3–4 tư thế. **Sai quá vài mm hoặc sai dấu ⇒ dừng.**
3. **Dấu của offset:** xem vectơ "khép" (x công cụ trong W) và nhìn má động nằm phía nào.

Quy ước của LeRobot cần biết: với `use_degrees=True`, **0° = trung điểm tầm chuyển động đã ghi lúc `lerobot-calibrate`** (mã: `(raw − (min+max)/2)·360/4095`). Vì vậy lúc hiệu chuẩn phải kéo **từng khớp tới tận hai đầu giới hạn cơ khí**; ghi thiếu một đầu thì 0° lệch, FK lệch vài độ và camera↔robot lệch theo. FK ở đây dùng thẳng độ của LeRobot với URDF `so101_new_calib` (mã `robot_kinematic_processor.py` của LeRobot 0.6.1 làm y như vậy, không cộng offset).

### 5.2 `board` — camera → mặt băng
Bàn cờ phẳng đặt yên trên băng (trong tầm nhìn **và** tầm với). Camera tự tìm góc; bạn chạm **9 điểm** (4 góc, 4 trung điểm cạnh, tâm; đi vòng viền rồi vào tâm) bằng điểm TCP, tay đỡ (torque tắt). Phần mềm khớp phép biến đổi cứng bàn cờ→W (cho phép phản xạ), loại **một** điểm chạm sai (leave-one-out), ước tỉ lệ bàn cờ, rồi dựng homography metric.
* Bàn mặc định 9×6 góc trong, ô 20 mm (in ra 10×7 ô = 200×140 mm; các góc trong trải 160×100 mm). **Bàn càng to càng tốt**: nhiễu tay ~1 mm mỗi lần chạm, các điểm chạm càng xa nhau thì sai số xoay/tịnh tiến càng nhỏ.
* `sai số chạm (rigid)` ≈ 1–1,5 mm là bình thường với tay người; **> 3 mm ⇒ cảnh báo, làm lại** (kiểm TCP chạm đúng góc, FK, `tcp_offset_mm`).
* `tỉ lệ kích thước thực/danh nghĩa` phải ≈ 1,00; cảnh báo khi lệch > 1,5% (hoặc > 3 độ lệch chuẩn của ước lượng): ô in bị co/giãn ⇒ đo ô bằng thước và truyền `--square-mm` đúng.
* `độ lệch giữa các lần chạm` của z phải < 3 mm (cảnh báo nếu hơn).
* Ví dụ trong phòng lab ảo (nhiễu chạm 1 mm, bàn nhỏ 7×4 góc ô 15 mm = 90×45 mm): ánh xạ ảnh→W sai trung bình 1,7 mm, tối đa 3,4 mm trên ±200 mm dọc băng. Bàn mặc định lớn hơn nên kỳ vọng tốt hơn `[ước lượng]`.

### 5.3 `belt` — hướng băng, mm/xung, độ trễ ảnh↔băng
Chạy 3 lượt (`--runs 3`). Mỗi lượt: băng trống → đặt **vạch phẳng** tương phản (giấy/băng dính màu, không dùng khối cao) ở thượng nguồn, mỗi lượt ở vị trí ngang khác nhau → vạch đứng yên 1,5 s (`--static-s`) rồi băng chạy 4 s (`--duration`). Đoạn đứng yên là bắt buộc để đo độ trễ ảnh.
* `--speed` mặc định 60. Nếu `belt.mm_per_step` còn 0 thì đó là **xung/giây**, không phải mm/s: chọn sao cho băng chạy khoảng 30–60 mm/s (ước thô mm/xung từ cơ khí: bước/vòng × vi bước, đường kính puli). Chọn quá chậm thì vạch dịch ít, "độ nhạy thấp" và lượt bị bỏ. Sau khi có `mm_per_step`, `--speed` là mm/s.
* Đọc: `hướng băng φ` (ổn định giữa các lượt), `mm/xung` (sai > 1–2% ảnh hưởng thẳng vào định thời), `độ trễ` từng lượt (lượt có độ nhạy < 0,2 mm bị bỏ; lấy trung vị).
* Chép `camera.latency_s` và `belt.mm_per_step` vào TOML.
* Phòng lab ảo (nhiễu chạm 1 mm): φ lệch 0,6° (90,62° so với 90°); mm/xung lệch −0,9%; độ trễ lệch +6,4 ms. φ lệch chủ yếu do xoay của phép khớp bàn cờ (nhiễu chạm), không phải do vạch; bàn cờ to hơn thì nhỏ hơn.
* **Đo thêm một lần độc lập, đừng bỏ:** đặt vật có dấu ở 2 vị trí cách nhau ≥ 300 mm trên băng, chạy băng một đoạn, so quãng đường thật bằng thước với Δs mà chương trình tính.
* `kind = "model"`: lệnh in "tốc độ đo được" để so với lệnh; lệch > 1–2% thì sửa hệ số quy đổi.

### 5.4 `background` — nền băng trống
Băng trống, **tay robot ở home** (bạn tự đưa về; tay là một phần của nền, nếu không tay bị phát hiện thành "vật"), tay người ra khỏi ảnh. In cửa sổ nhìn từ trên; **cảnh báo nếu > 0,45 Mpx** (nhận thức tốn ≈ 75 ms/Mpx trên CPU cỡ máy dev ⇒ trễ vòng kín). Thu cửa sổ về băng + vùng với tới bằng `--a-range a_min,a_max --b-range b_min,b_max` (toạ độ băng đã in ở dòng trên) hoặc tăng `perception.res_mm` lên 1,0. Xem `background_preview.png` (không được có vật lạ/bóng tay) và `background_window.png` (viền xanh = cửa sổ, mũi tên vàng = chiều băng).
Nền gắn với `calib.json`: đổi `calib.json` thì **dựng lại nền** (`build_stack` từ chối nền cũ). **Đổi ánh sáng đáng kể ⇒ dựng lại nền.**
Nên **khoá phơi sáng và cân bằng trắng** của camera trước khi hiệu chuẩn (tên điều khiển tuỳ camera, xem `v4l2-ctl -d /dev/video0 --list-ctrls`; thường là `auto_exposure`/`exposure_time_absolute`/`white_balance_automatic`). Mã chỉ bù được sự đổi sáng toàn ảnh (`photometric_comp`), không bù được tự phơi sáng theo vật `[chưa kiểm trên camera thật]`.

### 5.5 `lag` — độ trễ servo của tay
Tay chạy theo đoạn thẳng dọc băng với vận tốc hằng (`--speed` 40 mm/s, `--duration` 3 s) ở độ cao chờ, so lệnh với vị trí đo (FK của khớp đọc về), ra độ tụt ổn định ≈ v·τ. Gợi ý `executor.lead_s = τ` (phòng lab ảo: 0,128 s với servo ảo ≈ 0,12 s). Bộ thực thi còn có tích phân bù `lag_ki` nên giá trị này không cần chính xác tuyệt đối. Vùng robot phải trống và băng dừng; tay đi tới điểm đầu **chậm** (3 s) sau khi bạn nhấn Enter.

---

## 6. Đặt băng và xem nhận thức

**Đặt sơ bộ bằng thước (làm TRƯỚC §5).** Với kẹp thẳng đứng và độ cao mặc định (kẹp = mặt băng + 10 mm, chờ + 40, nhấc + 60), bản đồ với tới của gói (`cl0/reach.py`, chỉ động học, biên khớp 3° và 5 mm; **không** xét va chạm với đế/băng) cho thấy cả ba độ cao cùng với tới được khi khoảng cách ngang `r` từ **trục pan** (trục quay của khớp xoay ở đế) tới điểm nhặt nằm trong:

| Mặt băng so với mặt đế tay | `r` với tới được ở cả ba độ cao |
|---|---|
| thấp hơn 40 mm | ≈ 55–260 mm |
| thấp hơn 20 mm | ≈ 65–250 mm |
| ngang mặt đế | ≈ 90–225 mm |

`[tính từ mô hình động học, chưa kiểm trên tay thật]`. Đoạn nhặt (dài ≳ `v·(t_to_grasp_s + follow_margin_s)`, ví dụ 140 mm ở 50 mm/s, cộng thời gian xác nhận vật) phải nằm trọn trong vành khăn đó. Gợi ý `[ước lượng]`: cho băng chạy ngang tầm với của tay, đường giữa băng cách trục pan chừng 120–200 mm (đoạn nằm trong vành khăn khi đó dài 330–460 mm với `r_max` = 260 mm), và hạ mặt băng thấp hơn mặt đế càng nhiều càng tốt (≥ 20 mm).

```bash
python -m cl0.tune reach --config cl0.toml [--image frame.png] [--out reach.png]   # vùng với tới vẽ lên ảnh camera + bảng theo b
python -m cl0.tune watch --config cl0.toml --seconds 30 --out tune_out [--reach] [--belt-speed 30]
```
* `reach`: vùng TCP thẳng đứng với tới được ở ba độ cao (kẹp / chờ / nhấc). **Vật chỉ được chọn khi nằm trong vùng với tới ngay lúc chọn và suốt đoạn tới hết lúc nhấc** (xem §10.4, lỗi số 1). Đoạn băng cần ≳ `v·(t_to_grasp_s + follow_margin_s)` (mặc định 1,8 + 1,0 = 2,8 s × tốc độ), trừ thời gian xác nhận vật. Lệnh gợi ý tâm băng ở độ lệch `b` nào và `a_pick_min/max`. Băng chạy qua phía sau/đế robot thì vùng với tới rất hẹp (giới hạn pan ±110°).
* `watch`: chạy bộ nhận thức trên camera thật, lưu ảnh lớp phủ (viền mặt nạ, điểm kẹp, trục khép, bề rộng, lý do loại) và `watch_summary.json` (ms/khung, số phát hiện, bề rộng, p95). Cảnh báo nếu p95 > 0,8 × chu kỳ khung. Kiểm: vật đặt yên cho `ok_per_frame_mean` đúng số vật; **bề rộng trung vị khớp thước + 2–3 mm** (bộ phát hiện đo rộng hơn thật 2–3 mm do nhoè; `width_margin_mm` đã tính); không có phát hiện giả trên băng trống và khi tay ở home.

---

## 7. Thử an toàn trước khi tinh chỉnh

1. Một tay luôn gần công tắc nguồn/ngắt khẩn cấp. Lần đầu hạ `robot.q_dot_max_deg_s` xuống ~60 (mặc định 150).
2. Mọi lệnh khớp bị cắt theo giới hạn URDF ± `joint_margin_deg` (3°); lệnh nhảy > 45° so với vị trí đo ⇒ `SafetyError`; NaN/sai kích thước ⇒ `SafetyError`.
3. Mỗi lượt bắt đầu bằng `go_home` (2 s) và kết thúc/ngắt bằng dừng băng → mở kẹp → về home. `Ctrl-C` giữa lượt: dừng băng, mở kẹp, về home, lượt đó chưa ghi. Vật đang kẹp sẽ rơi. **Khi chương trình thoát, LeRobot tắt torque** (mặc định `disable_torque_on_disconnect = True`) nên tay rũ xuống tư thế gập: đỡ tay, hoặc đặt `home_q_deg` gần tư thế nghỉ, và đảm bảo bên dưới tay không có băng, camera hay vật.
4. **Mất liên lạc giữa lượt được phát hiện, không bị đọc nhầm thành thất bại của CL-0:** camera im > 1 s (`CameraCommError`), bộ đếm băng im (`BeltCommError`), lỗi bus/serial của servo (`ArmCommError`). Với các lỗi này `run_g0` hỏi phân loại và gợi ý "không hợp lệ" (§9). `SafetyError` (lệnh nhảy bị chặn) **không** được gợi ý như vậy, vì nó có thể là lỗi phần mềm/IK.
5. **Lượt tĩnh** (`--speed 0`): băng đứng yên, một vật dễ (đĩa/hộp ~30 mm, tương phản) đặt trong đoạn nhặt. Kỳ vọng: chọn → tới → hạ → khép → nhấc → giữ 2 s. **Quan sát bằng mắt tại độ cao chờ:** điểm giữa khe hai má có nằm trên tâm vật không (lệch cố định theo trục khép ⇒ chỉnh `tcp_offset_mm[0]`; theo hướng tiến vào ⇒ `[2]`; lệch ngang cố định ⇒ `board`).
6. **Băng chậm** (20 mm/s), một vật; rồi tăng tới tốc độ thật. Nếu vật hụt dọc băng: `camera.latency_s`, `lead_s`, `mm_per_step`.

```bash
python -m cl0.run_g0 --config cl0.toml --arrangements configs/arr_dev_example.csv --cell dev_static --out runs/dev --speed 0 --only 1-3
```
Ô `dev_*` không phải ô G0: dùng `--out` riêng để không lẫn vào số liệu G0.

---

## 8. Tinh chỉnh (≤ 2 ngày làm việc) và ĐÓNG BĂNG

Quy tắc công bằng §3.4: tinh chỉnh **chỉ trên vật dev và sắp xếp dev**, tối đa 2 ngày làm việc (ghi số giờ), rồi đóng băng toàn bộ trước lượt test đầu tiên. Gợi ý thứ tự (mỗi nút chỉ đổi khi có bằng chứng từ `tune watch`/lượt dev):

1. **Nhận thức** — `perception.k_sigma`, `t_min` (ngưỡng nền), `open_mm`/`close_mm` (làm sạch mặt nạ), `min_area_mm2`, `perception.grasp.gripper_w_mm`, `width_margin_mm`.
2. **Định thời** — `camera.latency_s`, `executor.lead_s`, `omega_xy` (độ nhanh của bộ lọc), `settle_s`, `tol_*`.
3. **Cú kẹp** — `executor.z_grasp_above_belt_mm`, `pre_height_mm`, `lift_height_mm`, `close_wait_s`; `robot.tcp_offset_mm` (nếu đổi ở đây thì đã đổi định nghĩa TCP so với lúc `board`: xem §4).
4. **Chọn vật** — `a_pick_min/max`, `t_to_grasp_s`, `follow_margin_s`, `track.n_confirm`, `track.gate_mm`.
5. **Nút KHÔNG thuộc CL-0 gốc (mặc định TẮT):** `perception.grasp.yaw_mode = "local"` (PCA cục bộ quanh điểm kẹp; hợp vật có quai/lõm), `perception.split = "watershed"` (tách vật dính nhau). **Nếu bật phải ghi vào `--notes` khi đóng băng và công bố**, vì chúng làm CL-0 mạnh hơn bản mô tả trong kế hoạch.

Đóng băng:
```bash
python -m cl0.freeze --config cl0.toml --hours 14 --notes "dev: 4 vật, 12 sắp xếp; yaw_mode=local"
python -m cl0.run_g0 ... --require-frozen        # từ chối chạy nếu mã hoặc cấu hình khác bản đóng băng
```
`frozen.json` ghi sha256 của cấu hình và của mọi file `*.py` trong gói `cl0/` (trừ `sim/`), giờ tinh chỉnh, ghi chú, phiên bản Python. `calib.json` và `background.npz` **không** nằm trong băm (hiệu chuẩn đổi theo buổi, kế hoạch §4.2 yêu cầu ghi lại mỗi buổi), nhưng băm của chúng được ghi vào `trial_NNNN.json` của từng lượt.
**Buộc phải sửa sau khi đóng băng** (lỗi phần mềm/phần cứng): sửa, rồi `python -m cl0.freeze --config cl0.toml --force --notes "SỬA ĐỔI: <lý do>"`. `--force` bắt buộc có ghi chú và **không xoá dấu vết**: bản đóng băng cũ (băm, giờ, ghi chú) được chuyển vào mục `amendments` của `frozen.json` mới cùng lý do. Phải công bố các sửa đổi đó (kế hoạch: mục "Sai lệch so với kế hoạch").

---

## 9. Chạy G0

Sinh sắp xếp (cùng một bộ cho MỌI phương pháp; **chỉnh bảng `LEVELS` trong `../dir1/make_arrangements.py` cho hợp kẹp của bạn TRƯỚC khi sinh bộ test**). Chạy từ thư mục dự án `cl0/`:
```bash
W=<belt.width_mm trong cl0.toml>           # mm; cùng một giá trị cho mọi bộ
cp ../dir1/objects_template.csv objects.csv    # điền tên, đường kính bao (mm), split = train|dev|test; xoá dòng ví dụ
python3 ../dir1/make_arrangements.py --objects objects.csv --split train --clutter C0 --n 30 --belt-width $W --seed 12 --out arr_seen_C0.csv
python3 ../dir1/make_arrangements.py --objects objects.csv --split test  --clutter C0 --n 30 --belt-width $W --seed 13 --out arr_novel_C0.csv
python3 ../dir1/make_arrangements.py --objects objects.csv --split test  --clutter C2 --n 60 --belt-width $W --seed 11 --out arr_novel_C2.csv
python3 ../dir1/make_arrangements.py --objects objects.csv --split test  --clutter C3 --n 30 --belt-width $W --seed 14 --out arr_novel_C3.csv
```
G0 dùng các sắp xếp ĐẦU danh sách (`--only`); G2 sau này dùng cả danh sách (n = 60 cặp ở `novel_C2`, 30 ở các ô còn lại). Chạy **`seen_C0` trước**: dưới 80% (< 16/20) là lỗi hiệu chuẩn/kỹ thuật theo kế hoạch §5: dừng, sửa (ghi vào `amendments`, §8), chạy lại.
```bash
run() { python -m cl0.run_g0 --config cl0.toml --arrangements arr_$1.csv --cell $1 --only $2 \
              --objects objects.csv --out runs/g0 --require-frozen --operator "<tên bạn>"; }
run seen_C0 1-20                                          # 1) ô kiểm hệ thống TRƯỚC
python3 ../dir1/g0_analyze.py cells runs/g0/g0_trials.csv # xem hàng seen_C0: < 16/20 => dừng, sửa, chạy lại (không đi tiếp)
run novel_C0 1-20; run novel_C2 1-30; run novel_C3 1-20   # 2) rồi các ô còn lại
python3 ../dir1/g0_analyze.py g0 runs/g0/g0_trials.csv --method CL0   # quy tắc G0 (cần đủ seen_C0 và novel_C2; thiếu thì báo THIẾU DỮ LIỆU)
```

**Trước lượt đầu**, chương trình in danh sách kiểm và đòi gõ `chay` mới kết nối robot/camera/băng. **Mỗi lượt:** in bảng + ảnh `placement_<id>.png`. Bạn đặt vật lên băng **đang dừng**, tay rời vùng robot, một tay gần công tắc nguồn, nhấn Enter (`s` = bỏ qua sắp xếp này, `q` = thoát). Sau lượt: Enter = theo gợi ý (thành công ⇔ `picked_hold_complete`), `1`/`0` để sửa (ghi chú tự thêm "người thử đổi…"), `i` = **không hợp lệ** (chỉ lỗi phần cứng/ngắt khẩn cấp/mất giao tiếp; bắt buộc nêu lý do; lượt đó PHẢI chạy lại). Thất bại thì chọn `fail_cause`:

| Kết quả bộ điều khiển | Nghĩa | Gợi ý `fail_cause` |
|---|---|---|
| `picked_hold_complete` | nhấc và giữ ≥ `hold_s` | — (thành công) |
| `dropped_in_hold` | mất vật trong lúc giữ | `slip` |
| `empty_grasp` | khép mà không giữ được gì | `grasp_point` (xem video: đẩy vật = `collision`, tuột = `slip`) |
| `no_target` | hết giờ không chọn được vật | `seg_miss` (vật quá rộng, mặt nạ hỏng, ngoài vùng với tới…) |
| `late`, `timeout`, `hard_timeout` | không kịp / quá hạn | `timing` |
| `ik_fail` | IK hỏng quá `ik_fail_abort_s` | `other` (vật ở biên vùng với tới) |

Bạn là người quyết định nguyên nhân cuối cùng sau khi xem video.

**Lượt bị cắt giữa chừng bởi lỗi** (mất camera/băng/servo, `SafetyError`…): chương trình in lỗi và hỏi `i` (không hợp lệ, chạy lại), `f` (thất bại hợp lệ, `fail_cause = other`), `q` (thoát, không ghi). Với mất liên lạc thiết bị, Enter = `i`; với lỗi khác phải tự chọn. Dòng CSV có `outcome = aborted:<loại lỗi>`, `trial_NNNN.json` có traceback. Sau mỗi lượt không hợp lệ chương trình in tỉ lệ không hợp lệ của ô và **cảnh báo khi > 10%** (kế hoạch §4.3: dừng và sửa).

Mỗi lượt ghi vào `--out`: `g0_trials.csv` (đúng cột của `g0_analyze.py`, thêm cột phụ), `trial_NNNN.json` (sự kiện, pha, chẩn đoán, băm cấu hình/mã/hiệu chuẩn), `trial_NNNN_log.csv` (nhật ký điều khiển 50 Hz), `trial_NNNN.mp4` (video gốc, không vẽ gì lên), `placement_<id>.png`. **Chạy lại cùng lệnh sẽ tiếp tục:** bỏ qua sắp xếp đã có lượt hợp lệ ở ô đó, chạy lại sắp xếp mới chỉ có lượt không hợp lệ.

**Vật thật không có "trục tham chiếu" sẵn:** trước khi đặt, chọn trục (vd. trục dài; vật tròn thì một dấu bút) và chụp ảnh cùng danh sách vật; yaw trong tờ là góc của trục đó.

Thử toàn quy trình không cần phần cứng: `python -m cl0.run_g0 --sim --config configs/sim_test.toml --arrangements configs/arr_dev_example.csv --cell dev_sim --out /tmp/g0_sim --no-video` (5 sắp xếp, ≈ 25 giây; kết quả hiện tại 5/5 trong mô phỏng).

---

## 10. Đã kiểm chứng gì (và chưa gì)

### 10.1 Test tự động (`python -m pytest`)

233 test = 204 nhanh + 29 chậm (`-m slow`: 18 vòng kín, 9 phòng lab ảo, 2 của `run_g0`). Bảng dưới là số test theo file và việc chúng kiểm; tất cả chạy trên dữ liệu **tổng hợp** hoặc thiết bị **giả** (giới hạn: §10.2, §10.5).

| File | Số test | Kiểm gì |
|---|---|---|
| `test_geometry.py` | 18 | homography ảnh → mặt băng (có/không lật ảnh); khung băng (a, b); hướng băng và tỉ lệ ở 6 góc; khớp cứng có phản xạ; ảnh nhìn từ trên (Rectifier); hiệu chuẩn bàn cờ với nhiễu chạm; cửa sổ tự động; đọc/ghi `calib.json` |
| `test_kinematics.py` | 8 | FK ↔ IK; kẹp thẳng đứng; IK nóng liên tục và nhánh dự phòng; vị trí trục pan; giới hạn khớp; `tcp_offset` |
| `test_perception.py` | 20 | thanh ở nhiều góc (bề rộng, trục khép); đĩa; vật rộng hơn kẹp bị loại; vòng (điểm kẹp nằm trên thân, không ở lỗ); băng trống không phát hiện giả; bù đổi sáng toàn ảnh; loại vùng quanh tay; tách vật dính (chỉ khi bật watershed); băng có texture; lưu/đọc nền |
| `test_grasp_tracker.py` | 14 | điểm kẹp (cực đại DT), trục khép ⟂ trục dài, bề rộng dọc dây cung; theo dõi trong hệ băng: xác nhận sau N quan sát, tách vật, bỏ phát hiện bị loại, xoá track mất, vật chập chờn không được xác nhận |
| `test_executor.py` | 8 | bộ thực thi: sai số bám ≈ v·trễ khi không bù; bù bằng `lead_s` hoặc tích phân; các tốc độ băng; giới hạn tốc độ khớp; mục tiêu ngoài vùng với tới; độ cao tối thiểu trên băng |
| `test_controller_select.py` | 9 | luật chọn vật: ngoài vùng với tới hoặc sắp ra khỏi vùng thì không chọn; tính cả dẫn trước; cửa sổ nhặt chỉ áp lúc kẹp/nhấc; chọn xuôi dòng nhất; chưa xác nhận thì không chọn |
| `test_closed_loop.py` | 18 (chậm) | vòng kín trong mô phỏng: đĩa ở 6 cấu hình hướng băng/lật ảnh/tốc độ; 4 dạng vật và góc khác nhau; clutter chọn vật xuôi dòng nhất; vật rộng hoặc băng trống → `no_target`; băng quá nhanh → `late`; luôn kết thúc ở trạng thái đã biết; **sai hướng băng 10° làm hỏng; sai mm/xung 25% làm hỏng, 2% thì chịu được**; băng có texture + bộ đếm |
| `test_calib_tools.py` | 35 | phần tính của hiệu chuẩn: bố cục và nhận góc bàn cờ; thứ tự và chỉ số điểm chạm; loại điểm chạm sai (leave-one-out) và không loại nhầm khi nhiễu bình thường; vạch phẳng; độ trễ ảnh ↔ băng (5 giá trị, lệch đồng hồ, thiếu đoạn đứng yên, băng đứng, độ nhạy thấp); độ trễ servo |
| `test_lab_calibrate.py` | 9 (chậm) | chạy chính các lệnh `calibrate board/belt/background/lag` và `tune` trong "phòng lab ảo" với người vận hành ảo: ghi đủ file; ánh xạ ảnh → W sai vài mm; φ, mm/xung, độ trễ; gợi ý `lead_s`; nhật ký có đủ chẩn đoán; dựng chồng từ file hiệu chuẩn rồi gắp; ca khó thất bại đúng lý do đã nêu; mm/xung sai trong cấu hình bị vòng kín phát hiện |
| `test_hw_fakes.py` | 36 | băng serial giả (dòng đếm, dòng vỡ/rác, nhiều dòng cùng lúc, mẫu lệnh lấy từ TOML, chờ board reset, kiểm cấu hình); mô hình băng; adapter LeRobot giả (thứ tự khớp, từ chối chế độ chuẩn hoá, cắt giới hạn, chặn lệnh nhảy, kẹp, torque, `go_to`); chốt chặn thiếu file hiệu chuẩn LeRobot (từ chối kết nối trước khi LeRobot kịp tự hiệu chuẩn lại; gợi ý `cp` từ thư mục cũ); `make_so101` khi thiếu lerobot; camera giả (dấu thời gian, định dạng, lỗi mở, cảnh báo độ phân giải); nhịp điều khiển; phát hiện mất camera/băng/servo |
| `test_run_g0.py` | 32 (2 chậm) | gợi ý nguyên nhân thất bại; `--only`; CSV/JSON/nhật ký và băm hiệu chuẩn; chạy tiếp; Ctrl-C; lỗi giữa lượt (mất liên lạc → không hợp lệ, lỗi khác → phải chọn); cảnh báo > 10% không hợp lệ; lời nhắc cho người thử; CSV đọc được bởi `g0_analyze.py`; tờ sắp xếp mẫu hợp lệ và chạy được trong mô phỏng; `--require-frozen`; CLI `--sim` đầu-cuối |
| `test_freeze.py` | 10 | băm mã/cấu hình; phát hiện đổi; `--force` cần lý do và giữ chuỗi sửa đổi; file hỏng; cảnh báo > 2 ngày; đường dẫn tuỳ chọn; băm mã bỏ qua `sim/` |
| `test_config.py` | 10 | TOML ↔ dataclass; khoá lạ báo lỗi (nêu tên mục); `configs/config_template.toml` khớp mã; cấu hình mô phỏng đọc được |
| `test_placement.py` | 6 | quy ước yaw (dương hướng về mép trái); nội dung tờ đặt vật; đọc tờ sắp xếp (bỏ dòng `#`) |

### 10.2 Mô phỏng và giới hạn của nó
Mô phỏng **động học**: vật đứng yên trong hệ băng, tay là bộ lọc bậc nhất (τ = 0,10 s) + trễ lệnh 0,02 s, kẹp được đánh giá bằng hình học (TCP trong thân vật, dây cung ≤ độ mở − 1,5 mm, pháp tuyến đối cực với ma sát 0,5, má kẹp không chạm vật khác, độ cao đủ; nhấc ≥ 25 mm giữ ≥ 2 s). **Không có** ma sát/đẩy vật khi khép, rung, tuột, đổ, phản xạ, bóng, nhiễu camera thật. Vì vậy tỉ lệ thành công trong mô phỏng **không** dự đoán số G0. Nhưng nó có phát hiện được lỗi thật: sai hướng băng 10° hoặc sai mm/xung 25% làm hỏng lượt (test chốt điều này), và nó đã bắt các lỗi ở §10.4.

### 10.3 Kết quả mô phỏng đáng nhớ (chạy lại ngày 26/10/2026)
* **Hiệu chuẩn bằng chính các lệnh `calibrate`** trên phòng lab ảo (người chạm nhiễu Gauss 1 mm, bàn cờ 7×4 góc ô 15 mm): ánh xạ ảnh→W sai trung bình 1,68 mm / tối đa 3,36 mm; sai số chạm 1,29 mm; φ = 90,62° (thật 90°); mm/xung = 0,9906 × thật; độ trễ ảnh lệch +6,4 ms; `lead_s` = 0,128 s; z mặt băng lệch 0,00 mm. Cả chuỗi `board → belt → background → lag` chạy ≈ 26 giây thời gian thật.
* **Dựng chồng CL-0 từ các file đó, mỗi dạng 1 lượt** (băng 50 mm/s, vị trí/yaw ngẫu nhiên cố định hạt giống): 6/6 dạng "dễ" gắp được (đĩa 30, hộp 25×50, elip 28×48, đĩa 30 tương phản thấp với băng, đĩa 22, thanh 18×60), TCP lệch tâm vật 1,3–1,6 mm lúc má kẹp chạm.
* **Dạng khó (mỗi dạng 1 lượt, yaw 0 — chỉ để thấy cơ chế, không có ý nghĩa thống kê):** hộp 60×60 rộng hơn kẹp ⇒ `no_target`; tấm dẹt 20×45 thấp hơn độ cao kẹp cố định ⇒ `empty_grasp` (`too_high`); vòng ⇒ `empty_grasp` (`slip`); chữ L và cốc có quai "thành công" trong mô phỏng nhưng điểm kẹp (cực đại DT) lệch tâm vật 14–15 mm; ngoài đời các dạng lõm/có quai này rất đáng ngờ.
* **Hướng băng/tốc độ:** cùng bộ điều khiển gắp được đĩa 30 với 6 cấu hình (φ = 0°, 90°, 135°, 180°, 200°, 270°; có/không lật ảnh; 30–60 mm/s).
* **Thử `--sim` với `configs/arr_dev_example.csv`:** 5/5 sắp xếp (một vật, hai–ba vật cách nhau).
* **`cl0log` (`scripts/env.sh`)** — thử tay (không có test tự động): gửi SIGINT thật tới nhóm tiến trình của một chương trình giả có `input()` và khối dọn dẹp khi Ctrl-C. Có `tee -i`: dòng dọn dẹp và mã thoát vào log. Bỏ `-i`: `tee` chết theo Ctrl-C, dòng dọn dẹp mất khỏi cả màn hình lẫn log.

### 10.4 Lỗi mà test/mô phỏng đã bắt (đã sửa)
1. **Chọn vật quá sớm** *(test vòng kín, φ = 0°)*: bộ chọn chỉ kiểm vật vào vùng với tới *lúc kẹp*, trong khi bộ thực thi bám vị trí *hiện tại* của vật ⇒ IK hỏng khi vật còn ngoài vùng với tới. Nay kiểm cả lúc chọn, giữa chừng, lúc kẹp, lúc nhấc, và cả vị trí dẫn trước `lead_s`.
2. **Ảnh tờ đặt vật vẽ yaw bị lật chiều** *(test hướng yaw)*.
3. **`go_to` chỉ đọc vị trí robot một lần** *(test với giới hạn nhảy 15°)*: chuyển động dài hơn ngưỡng "nhảy" bị chặn nhầm giữa chừng.
4. **Băng: nhiều dòng serial đến trong cùng một lần đọc** *(test tách dòng)*: giữ nhầm số đếm cũ; nay giữ số đếm mới nhất.
5. **`run_g0 --sim` dùng sai tâm băng khi φ ≠ 90°** *(chạy thử CLI)*.

Lỗi/thiếu sót tìm ra khi **rà lại mã** (không phải do test bắt; đã sửa và thêm test sau đó):
6. Mất camera/băng/servo giữa lượt sẽ bị đọc thành thất bại của CL-0 ⇒ nay phát hiện (`CameraCommError`, `BeltCommError`, `ArmCommError`), hỏi phân loại, đếm tỉ lệ không hợp lệ.
7. Mở cổng serial không chờ Arduino/ESP reset ⇒ thêm `serial_open_delay_s`.
8. `freeze --force` ghi đè bản đóng băng cũ không để lại dấu vết ⇒ nay chuyển vào `amendments`, bắt buộc có lý do.
9. Băm của `calib.json`/`background.npz` không được ghi theo lượt ⇒ nay ghi vào `trial_NNNN.json`.
10. Lệnh `fk` in thiếu vectơ khép (cần để xác định dấu `tcp_offset_mm`) ⇒ nay in.
11. LeRobot 0.6.1 đổi thư mục hiệu chuẩn (`so_follower` thay vì `so101_follower`) và **tự hiệu chuẩn mới, ghi đè động cơ, nếu thiếu file** ⇒ thêm `check_calibration_file` chặn trước `connect()` (thêm 3 test).
12. Test `make_so101` "khi thiếu lerobot" **sẽ FAIL trên máy đã cài LeRobot** ("DID NOT RAISE": đường import cuối không đi qua `importlib.import_module` nên không bị chặn). Tái hiện bằng gói `lerobot` giả; nay chặn bằng `sys.modules["lerobot"] = None`.

### 10.5 CHƯA kiểm trên phần cứng (rủi ro khi bạn chạy lần đầu)
* **LeRobot** — đã khớp mã nguồn 0.6.1 (`SO101Follower`/`SO101FollowerConfig` từ `lerobot.robots.so_follower`, khoá `"<khớp>.pos"`, `bus.enable_torque()/disable_torque()`, `use_degrees=True`) nhưng **chưa chạy với robot thật**. Bản LeRobot khác có thể đổi tên; khi đó dùng `--arm-adapter mô_đun:Lớp` (cần `connect/state/send/torque/disconnect`).
* **Hiệu chuẩn LeRobot của tay** quyết định "0°" (§5.1). Nếu sai, FK lệch và mọi thứ sau lệch theo; `fk` và `board` sẽ lộ ra.
* **TCP/tâm kẹp của má đơn động** (§4): chưa biết gốc khung `gripper_frame_link` nằm đâu trên má kẹp của bạn; vật bị đẩy khi khép (không có trong mô phỏng).
* **Băng:** firmware, chuỗi lệnh/dòng báo, đơn vị, độ trễ serial, gia tốc thật. `kind = "model"` chưa thử với băng thật.
* **Camera:** V4L2/MJPG, độ trễ thật, rung, tự phơi sáng/cân bằng trắng, nhiễu, méo ống kính (chạy `intrinsics`); `CAP_PROP_BUFFERSIZE` có thể không được driver tôn trọng (độ trễ do bộ đệm sẽ nằm trong `camera.latency_s` nếu ổn định).
* Các lời nhắc tương tác trong `calibrate`/`run_g0`: chạy thử với người vận hành ảo và thiết bị giả, chưa với bạn.
* **Vật cao — thị sai:** homography đúng cho *mặt băng*; đỉnh vật cao lệch xuyên tâm so với chân nên điểm kẹp lấy từ mặt nạ trên cùng sẽ lệch. Vật cao hơn ~30 mm (so với độ cao camera) cần kiểm riêng `[chưa kiểm]`.
* **Độ cao kẹp cố định** `z_grasp_above_belt_mm` (CL-0 không biết chiều cao vật): vật mỏng hơn mức đó không kẹp được.
* **Vật không lồi** (vòng, chữ L, có quai): CL-0 gốc lấy cực đại DT + trục ⟂ PCA ⇒ dễ trượt; `yaw_mode = "local"` chỉ là nút tinh chỉnh (§8).
* Cánh tay/bàn tay trong ảnh: `arm_exclusion_mm` (55 mm quanh TCP) loại phát hiện; phát hiện lớn hơn `max_area_mm2` bị bỏ.
* Thời gian thực: p95 nhận thức phải < ~0,8 chu kỳ khung (`tune watch` in ra); máy dev của mình khác máy bạn.

---

## 11. Bộ thực thi dùng chung với I2

`executor.py::BeltExecutor` là thành phần "IK + s(t)" của §3.2. Nhận **mục tiêu trong hệ băng** `tgt_bf = (a_b, b)` (vị trí p_b của điểm cần tới), góc khép θ và độ cao tham chiếu; trả góc khớp lệnh:
```python
ex = BeltExecutor(cfg, kin, phi_deg, z_belt_mm); ex.reset(q0_deg)
ex.start(tcp, s_now, sdot)                       # tcp = dict(a, b, z, theta) từ FK của khớp đọc về (a, b là toạ độ THẾ GIỚI-căn-theo-băng)
q_cmd, err_meas, th_ref = ex.step(t, dt, s_now, sdot, tcp, tgt_bf, theta_deg, z_ref)
```
Công thức: `p_w,lệnh = p_b,mục tiêu + (s(t) + ṡ·lead_s)·û`, qua bộ lọc tới hạn trong hệ băng (`omega_xy`, `vmax_xy`), cộng tích phân bù `lag_ki` (lệnh gốc − đo được), IK nóng, chặn tốc độ khớp. Theo kế hoạch §3.2, chính sách học I2 xuất `a_k = p_b,mục tiêu − p_b,EE(t_img)`; đổi về `tgt_bf = p_b,EE(t_img) + a_k` rồi gọi `step` — **dùng đúng module này, cùng tham số** (`lead_s`, `lag_ki`, `omega_*`) để so công bằng với CL-0.

---

## 12. Sự cố thường gặp

| Hiện tượng | Nguyên nhân hay gặp | Cách xử lý |
|---|---|---|
| `không mở được camera` | quyền (nhóm `video`), sai chỉ số | `v4l2-ctl --list-devices`; thử `device = "/dev/video2"` |
| cảnh báo `camera trả WxH` | camera không hỗ trợ độ phân giải yêu cầu | chọn độ phân giải được hỗ trợ **rồi hiệu chuẩn lại từ đầu** |
| `CameraCommError` | rút cáp USB, camera treo | cắm lại; lượt đó là không hợp lệ |
| `BeltCommError` (chưa từng có dòng khớp) | sai cổng/baud, `line_regex` không khớp, firmware không gửi | xem "dòng cuối" trong thông báo; sửa `line_regex`/`serial_baud` |
| `BeltCommError` (đang chạy thì mất) | cáp serial, MCU treo | lượt đó là không hợp lệ |
| `ArmCommError` | bus servo lỗi, hết nguồn, rút cáp | kiểm nguồn/cáp; lượt đó là không hợp lệ |
| `Không thấy file hiệu chuẩn LeRobot của robot_id=…` | sai `robot_id`, hoặc hiệu chuẩn làm bằng LeRobot bản cũ (thư mục `so101_follower`) | xem §4: `cp` file sang thư mục `so_follower`; **đừng** để LeRobot tự hiệu chuẩn lại |
| `SafetyError: lệnh nhảy …°` | tay bị đẩy/tắt torque, dấu IK sai, `robot_id` sai (hiệu chuẩn khác) | `calibrate fk`; kiểm hiệu chuẩn LeRobot. KHÔNG tự gọi là không hợp lệ |
| LeRobot hỏi "Press ENTER to use provided calibration file…" | hiệu chuẩn trong động cơ lệch file `robot_id` | Enter = dùng file; gõ `c` chỉ khi định hiệu chuẩn lại |
| `ik_fail` lặp lại | vật ở biên vùng với tới | `tune reach`; dời băng gần đế hơn / hạ băng; đặt `a_pick_*` |
| `no_target` lặp lại | mặt nạ hỏng, vật `wide`, nền lệch, ánh sáng đổi | `tune watch`; dựng lại nền; xem `reject_wide` trong `diag` của `trial_*.json` |
| tay bị coi là vật | nền dựng khi tay không ở home | dựng lại nền với tay ở home |
| "nền dựng với calib.json khác" | đã chạy lại `board`/`belt` | `calibrate background` lại |
| tay luôn tới sau vật | `camera.latency_s`, `lead_s`, `mm_per_step` | đo lại §5.3; so `cmd_a_b` với `tcp_a_b` trong `trial_*_log.csv` |
| lệch ngang cố định | `tcp_offset_mm`, sai số `board` | lượt tĩnh; chạm lại 9 điểm với bàn cờ to hơn |
| lệch dọc tăng dần theo vị trí | hướng băng φ hoặc mm/xung sai | đo lại §5.3 (đo độc lập bằng thước) |
| `n_late` lớn trong `extra` của `trial_*.json` | nhận thức chậm | thu cửa sổ nền (`--a-range/--b-range`), `res_mm = 1.0`, đóng ứng dụng khác |
