# ARENA_SETUP_REPORT — môi trường Isaac Sim cho đấu trường

## 29/10/2026 — E0 (làm lại): môi trường và khả thi

Chỉ mô phỏng; không chạm robot, băng hay camera thật. Người dùng yêu cầu làm lại toàn bộ E0 (29/10). Lần chạy đầu để ở `archive/e0_run1_2026-10-29/` (không xoá, vì luật không xoá log). Lần này chạy bằng một lệnh: `arena/scripts/run_e0.sh`; số trong bảng lấy từ `arena/scripts/e0_summary.py` (đọc `runs/e0/*/e0_probe.json`), không gõ tay. Log: `arena/logs/2026-10-29_*_e0_*.log`.

### Khác với prompt/kế hoạch (ghi lại, không tự sửa)
| Điều | Thực tế | Xử lý |
|---|---|---|
| Đường dẫn `~/thesis/{arena,cl0,…}` | không tồn tại; mọi thứ ở `~/Projects/dir1_tools/{arena,cl0,dir1}` | `arena/` tạo cạnh `cl0/`; ghi trong `arena/CLAUDE.md` |
| Kế hoạch đấu trường dẫn "`KE_HOACH_HUONG_1.md` §3.6" và bảng "Khớp sim–thật" | `KE_HOACH_HUONG_1.md` (bản 27/10, 383 dòng) chỉ có mục 3.1–3.5; `grep -n "3\.6"` không ra gì. Kiểm lại 29/10 12:49: file không đổi | **chưa giải quyết**; mình chưa đọc được nội dung §3.6 (S0/S1/S2, bảng khớp sim–thật) |

### Máy và Isaac Sim
| Mục | Giá trị | Nguồn |
|---|---|---|
| Isaac Sim | 6.0.0.1 (pip), `~/env_isaac/bin/python`, Python 3.12.3 | `pip list`, `e0_probe.json` |
| Isaac Lab | không thấy `[chưa kiểm sâu]` | `pip list`, `~/IsaacLab*` |
| GPU | RTX 3070 Ti 8192 MiB, driver 595.99.02; trước khi chạy đã dùng ≈ 930–975 MiB (màn hình), không có tiến trình tính toán nào khác | `vram_mib_before_app`, `nvidia-smi` |
| numpy trong Isaac | 2.3.1 (LeRobot 0.6.1 đòi 2.0–2.2: chỉ ảnh hưởng nếu import `lerobot`; đường mô phỏng của CL-0 không import) | |
| Khởi động `SimulationApp` headless | 17,1–18,1 s (cache shader nóng) | `app_start_s` |
| Extension khi khởi động | bật: `omni.replicator.core`, `isaacsim.sensors.camera`, `omni.physx`, `isaacsim.core.api`. **Tắt**: `isaacsim.asset.gen.conveyor`, `isaacsim.ros2.bridge` | `e0_probe.json` |
| Bật conveyor lúc chạy (`--enable-ext isaacsim.asset.gen.conveyor`) | chạy được, `enabled_now = true`, khung hình bình thường | `runs/e0/conveyor_640x480/` |
| Bật CẢ conveyor lẫn ros2.bridge lúc chạy | **segfault** một lần ở lần chạy đầu, tại `app.update()` đầu tiên sau `timeline.play()` (stack Python: `omni.kit.manipulator.prim.core … xform_set_time`); log `archive/e0_run1_2026-10-29/logs/2026-10-29_015114_e0_probe_1080p_v2.log`. Lần chạy lại này không bật ros2.bridge nên **không tái hiện được** `[chưa lặp riêng ros2.bridge để chắc nguyên nhân]`. Arena không cần ROS 2 bridge ⇒ không bật | |

### Hai bẫy dựng cảnh đã gặp (để E1 không dẫm lại)
1. Khung **đen/phẳng**: camera USD có mặt phẳng gần mặc định = 1 đơn vị cảnh = 1 m (khi `metersPerUnit = 1`), nên mặt nền cách 0,8 m bị cắt mất. Đặt `clippingRange = (0,01; 20)` thì hết. Chẩn đoán: `scripts/e0_black_diag.py`, ảnh trong `archive/e0_run1_2026-10-29/runs/e0/diag_*.png`.
2. Cảnh chỉ sáng khi có `DomeLight`; `DistantLight` đơn lẻ cho ảnh đen `[chưa rõ vì sao; E1 chọn ánh sáng và kiểm phơi sáng]`.

### Đo (cảnh trống + 1 khối đỏ 4 cm rơi lên nền, 1 camera, RGB annotator, timeline đang chạy; 120 khung mỗi độ phân giải)
| Độ phân giải | ms/khung (`orchestrator.step` + đọc ảnh) p50 / p95 | VRAM đỉnh | vật lý trực tiếp |
|---|---|---|---|
| 640×480 | 69,1 / 81,1 | 2,61 GiB (2612 MiB) | 0,642 ms/bước |
| 1280×720 | 72,5 / 85,1 | 2,87 GiB (2870 MiB) | 0,643 ms/bước |
| 1920×1080 | 149,3 / 155,5 | 3,60 GiB (3596 MiB) | 0,655 ms/bước |

* Tái lập: lần chạy đầu cho 1080p = 152,3 / 154,5 và 153,0 / 154,8; 720p = 72,1 / 85,1; 480p = 67,2 / 72,2 (`archive/e0_run1_2026-10-29/`). Lệch giữa các lần ≤ 3 ms ở p50.
* Số 87 ms của một lần chạy 1080p cũ (khung đen) **không dùng**.
* Vật lý "trực tiếp" = `simulate()+fetch_results()` ở 240 Hz với một vật. Chỉ là vật lý; cảnh có tay + băng + nhiều vật sẽ chậm hơn `[chưa đo, E1]`. `[chưa kiểm]` đây có phải đường lockstep đúng khi timeline đang chạy; E2 xác nhận.
* 480p và 720p gần như bằng nhau (≈ 70 ms): phần lớn là chi phí cố định của `orchestrator.step`, không phải số điểm ảnh. 1080p tốn gấp đôi.
* Khối lập phương dừng ở z = 0,02 m (= 4 cm / 2) sau 30 lần cập nhật ở cả bốn lần chạy ⇒ vật lý chạy theo timeline.
* Ước tính thô `[ước lượng]`: một lượt 20 s ở 30 fps camera = 600 khung ⇒ ≈ 42 s (480p/720p) tới ≈ 90 s (1080p) chỉ riêng render, chưa cộng tay + vật lý.

### Quyết định tiến trình (đề xuất, chờ E2 xác nhận)
**Cùng một tiến trình, Python của Isaac.** Python Isaac 3.12.3 = Python của venv CL-0. Kiểm lại 29/10: `PYTHONPATH=…/cl0 ~/env_isaac/bin/python -c "import cl0.runner, cl0.system, cl0.kinematics, cl0.sim.platform, cl0.run_g0"` chạy được (numpy 2.3.1, cv2 4.13.0), và `lerobot` không nằm trong `sys.modules`. Không cài thêm gì vào `~/env_isaac`. Không file nào trong `cl0/` bị sửa (không có `.py` nào mới hơn `run_e0.sh`).
`[chưa kiểm]`: `pytest` CL-0 trong `~/env_isaac` (pytest chưa có ở đó; bộ test vẫn chạy bằng `~/venvs/cl0`); một lượt CL-0 thật trong Isaac (E2).
Chỉ cần tách tiến trình (socket, lockstep) nếu sau này cần LeRobot cùng tiến trình với Isaac.

### Ảnh render (đã mở xem)
`runs/e0/1920x1080/e0_frame_1920x1080.png`, `runs/e0/1280x720/e0_frame_1280x720.png`, `runs/e0/640x480/e0_frame_640x480.png`: khối đỏ giữa khung trên nền xám, trung bình điểm ảnh ≈ (127; 127; 127).

### E0 chưa trả lời
* Ánh sáng và phơi sáng thật cho cảnh băng; vật lý có tay + gắp (E1, E4).
* Băng: chưa dựng, chưa đo vận tốc vật; `isaacsim.asset.gen.conveyor` bật được.
* §3.6 của kế hoạch chính (xem bảng đầu).

## 29/10/2026 — E1: cảnh tối thiểu

Chỉ mô phỏng. Người dùng chọn: **dùng USD mới** (dựng từ URDF chính thức), "vật thì muốn đa dạng" (E5). Các ô trống còn lại dùng mặc định (đã nói với người dùng; chưa ai duyệt): camera 1280×720, băng dài 600 mm, camera thẳng xuống cao 510 mm, ngưỡng `[đề xuất]` như kế hoạch. Cảnh: `arena/arena/scene.py` + `arena/configs/scene.toml` (tách khỏi `arena.toml` vì bộ đọc cấu hình của CL-0 báo lỗi khi gặp khoá lạ; `arena.toml` tạo ở E2).

### USD mới (`arena/assets/so101_lerobot/so101_new_calib.usda`)
* Nguồn: `so101_new_calib.urdf` chính thức, sha256 `3a65d2d3…022c` (bản trong `so101_cell_description`, đã so băm), mesh qua symlink `arena/assets/so101_src/assets`. Bộ chuyển: `urdf_usd_converter` 0.1.2 của Isaac, `--no-physics-scene`. Không đụng `so101_description` hay `so101.usda` của người dùng.
* Tên khớp **đúng tên LeRobot**: `shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper` (không cần bảng ánh xạ); giới hạn khớp trùng URDF (−110…110; −100…100; −96,8…96,8; −95…95; −157,2…162,8; gripper −10…100 độ). Góc theo độ, 0° = tư thế URDF = quy ước CL-0.
* Cảnh báo của bộ chuyển: `origin: Invalid element type … (line 294)`: thẻ `<origin>` đặt sai chỗ trong link giả `gripper_frame_link` của file chính thức; vô hại (link vẫn có, đã kiểm).
* Thêm lúc dựng cảnh (không nằm trong USD): drive góc cho 6 khớp (độ cứng 17,42 N·m/độ, giảm chấn 0,0477, lực tối đa 2,5 N·m: số của người dùng cho STS3215, `[chưa kiểm]` lực 2,5), tắt tự va chạm (bộ chuyển cho NaN nếu bật, theo ghi chú của người dùng 13/10).
* Tay đặt trên bàn cố định, mặt bàn z = −2,4 mm (đáy mesh đế); băng mặt z = −2,4 mm (**ngang mặt bàn/đế, theo yêu cầu của người dùng 29/10 sau báo cáo E1 đầu: "mặt băng nằm cùng mức nền base của arm"**; lần chạy đầu ở −60 mm, lưu ở `arena/runs/e1/archive_belt_z-60/`, các số ở (b), (c) và mục tốc độ băng bên dưới là của lần đó, bản mới ở mục "Cập nhật" cuối E1), rộng 200 mm, dài 600 mm, φ = 90° (chạy theo +y của W), tâm băng cách trục pan 190 mm (x = +190 mm). Mô hình vật lý băng: hộp động học + `PhysxSurfaceVelocityAPI`.

### (a) FK: Isaac so với `SO101Kinematics` (`arena/runs/e1/e1_fk.json`, log `arena/logs/2026-10-29_*_e1_fk_v3.log`)
20 cấu hình ngẫu nhiên (seed 7), mỗi khớp cách giới hạn 8°; dịch thẳng khớp rồi đọc pose `gripper_frame_link`, KHÔNG bước vật lý.
| | lệch vị trí TCP | lệch hướng |
|---|---|---|
| tối đa / trung bình | **0,038 mm** / 0,021 mm | **0,025°** |
| ngưỡng `[đề xuất]` | ≤ 2 mm | ≤ 1° |
⇒ đạt, thừa hai bậc độ lớn. Nghĩa là USD mới có đúng trục, gốc 0° và độ lệch như `kinematics.py`.
* Phép đo động (tham khảo): từ tư thế home của `cl0.toml` (`home_q_deg`) tới mục tiêu ± 12°, giữ 1,5 s dưới trọng lực, 8 cấu hình: 0 NaN, lệch TCP ≤ 0,08 mm, lệch khớp ≤ 0,02° ⇒ không võng. Nhưng **vận tốc khớp đỉnh 430–990 °/s** (servo STS3215 thật nhanh nhất cỡ vài trăm °/s, và CL-0 tự chặn lệnh ở `q_dot_max_deg_s` = 150): tay mô phỏng đáp **nhanh hơn thật** nếu lệnh không bị chặn `[chưa khớp servo thật; đo trễ/độ trễ servo ở E8, có thể thêm giới hạn tốc độ khớp ở E2]`.
* **Cảnh báo (không phải lỗi của USD):** lần chạy đầu dịch tay vào cấu hình ngẫu nhiên rồi bước vật lý ngay: nhiều cấu hình cho sai số hàng chục mm đến NaN (tay đâm vào bàn/đế khi dịch khớp tức thời). Về sau cấu hình NaN làm hỏng mọi phép đo sau nó trong cùng tiến trình (có lần cho lệch 2,4 mm ở phép đo "động học" kế tiếp). Vì thế phép đo động học tách riêng, không bước vật lý. Ở E2: reset tay phải đưa về home bằng lệnh có giới hạn tốc độ, không dịch khớp tức thời; lượt có NaN ⇒ `valid = 0` (luật mục 7).

### (b) Băng: vận tốc vật, lần chạy đầu ở z = −60 mm (bản lưu `arena/runs/e1/archive_belt_z-60/e1_belt.json`, log `…_e1_belt_v3.log`; bản z = −2,4 mm ở mục "Cập nhật")
Một tấm phẳng 40×40×6 mm (ma sát 1,0) trên tâm băng; đặt tốc độ, chờ 1,5 s, đo 4 s; vận tốc = độ dốc hồi quy tuyến tính a(t) (a = toạ độ dọc băng).
| lệnh (mm/s) | đo bằng ground truth | lệch GT | đo bằng ảnh (tâm khối đỏ → mặt băng) | lệch ảnh | không phát hiện |
|---|---|---|---|---|---|
| 20 | 19,999 | −0,01 % | 20,009 | +0,05 % | 0/121 |
| 40 | 39,998 | 0,00 % | 39,265 | −1,84 % | 0/121 |
| 60 | 59,998 | 0,00 % | 60,844 | +1,41 % | 0/121 |
| 80 | 80,000 | 0,00 % | 80,633 | +0,79 % | 0/121 |
Ngưỡng `[đề xuất]` ≤ 3 % ⇒ đạt. Độ lệch khỏi đường thẳng của GT ≤ 0,001 mm. Phần lệch của phép đo ảnh là nhiễu tâm điểm ảnh (1 điểm ảnh ≈ 0,62 mm), không phải sai băng. Hình ảnh theo sát vật lý (không "trễ khung") ở cách bước này: `simulate()+fetch_results()` rồi `update_transformations(False, True, False)` rồi `orchestrator.step(delta_time=0)`.

Hai bẫy đã gặp (vào `arena/arena/scene.py`, `belt.py`):
1. Vận tốc mặt băng khai theo **hệ cục bộ** bị nhân với hệ số scale của hộp băng (hộp đơn vị có scale không đều): lệnh 50 mm/s dọc trục dài scale 0,6 chỉ cho 30 mm/s. Dùng vận tốc theo **hệ thế giới** (vector u·v).
2. Vật nằm yên trên băng đang đứng sẽ **ngủ** (PhysX) và không bị kéo khi băng chạy sau đó (GT = 0 mm/s ở hai lần chạy đầu). Mọi vật động của arena đặt `sleepThreshold = 0` (`scene.make_dynamic`).

### (c) Camera (lần chạy đầu, z = −60 mm)
Ảnh `arena/runs/e1/archive_belt_z-60/e1_camera_belt_object.png` (1280×720, đã mở xem): băng đủ khung (4 góc tại điểm ảnh (153,5; 197,8)…(1126,5; 522,2)), bàn thấy ở mép trên, khối đỏ nhìn rõ; 0,617 mm/điểm ảnh ở mặt băng. Hướng: phải ảnh = chiều băng chạy u.
* **Tay ở q = 0 che băng** (ảnh trên). Tư thế home mặc định của `cl0.toml` (`home_q_deg` = [0, −49, 48, 91, 0]) đặt TCP tại x = 130 mm: vẫn nằm trên mép gần của băng (x từ 90 đến 290 mm). ⇒ E2 phải chọn tư thế home/nền sao cho tay ra khỏi ảnh khi dựng `background.npz` (mình chưa đổi `home_q_deg`, quyết ở E2).

### (d) Tốc độ chạy
Cả phép đo belt (4 tốc độ, 24 s mô phỏng, 484 khung 1280×720): 59,3 s thật = **2,47 giây thật / giây mô phỏng**. Gần hết là render (≈ 70 ms/khung ở E0); vật lý thuần 240 Hz chạy nhanh hơn thời gian thật. Với camera 30 fps một lượt 20 s ≈ 50 s thật chỉ riêng cảnh này, chưa tính tay + CL-0 `[ước lượng; đo thật ở E2]`.

### Độ mở kẹp w (ước lượng từ hình học mesh; `arena/runs/e1/e1_gripper_gap.json`, log `…_e1_gripper_w_v2.log`)
Khe giữa má cố định và má động dọc trục khép (x của `gripper_frame_link`), dải |y| < 6 mm, theo độ sâu z (z = 0 là mũi kẹp, âm là lùi về cổ tay); `gripper.pos` 0–100 ↔ khớp −10…100° tuyến tính `[giả định, E8 phải so với kẹp thật]`.
| gripper.pos | 0 | 10 | 20 | 30 | 40 | 50 |
|---|---|---|---|---|---|---|
| khe tại z = 0…−15 mm (mm) | 2–10 | 17–23 | 31–36 | 45–47 | 59–62 | 74–75 (z ≤ −10) |
Khe lớn dần ≈ **1,45 mm mỗi đơn vị `gripper.pos`**. Đề xuất cho arena: `robot.gripper_open = 40` ⇒ **`perception.grasp.gripper_w_mm` ≈ 60 mm** `[ước lượng hình học; chưa kiểm bằng gắp thật, E4 (ORACLE) sẽ thử]`. Vật đa dạng ⇒ đường kính bao ≲ 70–80 % w ≈ 42–48 mm. Với `gripper_open` mặc định 60 của CL-0 thì khe > 90 mm, không dùng.

### Tốc độ băng theo L (w = 60 mm, τ giả định 0,4 s `[chưa đo]`; công thức §3.1)
v = L·w/τ ⇒ L = 0,25: 38 mm/s; L = 0,5: 75 mm/s; L = 1,0: 150 mm/s. **Ràng buộc với tầm với** (từ E0/SETUP_REPORT, mặt băng −60 mm, rộng 200 mm): đoạn nhặt dài nhất phủ đủ bề rộng = 192 mm, trong khi CL-0 cần ≳ v·(1,8 + 1,0) s = 210 mm ở 75 mm/s và 420 mm ở 150 mm/s. Tức L = 0,5 hơi thiếu, L = 1,0 không khả thi với CL-0 ở hình học này `[tính từ mô hình động học]`. Quyết ở đầu E2: hạ mặt băng xuống −80 mm (đoạn 244 mm ⇒ v ≤ 87 mm/s) hoặc chấp nhận.
**[Thay thế bởi mục "Cập nhật" ngay dưới: người dùng chọn mặt băng ngang đế (−2,4 mm), không hạ xuống −80 mm.]**

### Cập nhật 29/10: mặt băng ngang đế (z = −2,4 mm), theo yêu cầu của người dùng
Người dùng: "mặt băng nằm cùng mức nền base của arm". Đã đổi `configs/scene.toml` `belt.z_mm` −60 → −2,4 (= mặt bàn). Chạy lại phép đo băng: `arena/runs/e1/e1_belt.json`, `arena/runs/e1/e1_camera_belt_object.png` (đã mở xem), log `arena/logs/2026-10-29_145522_e1_belt_flush.log`. Phép đo FK không đổi (không phụ thuộc băng).
| lệnh (mm/s) | GT (mm/s) | lệch GT | ảnh (mm/s) | lệch ảnh | không phát hiện |
|---|---|---|---|---|---|
| 20 | 19,999 | −0,01 % | 19,954 | −0,23 % | 0/121 |
| 40 | 40,001 | 0,00 % | 38,809 | **−2,98 %** | 0/121 |
| 60 | 59,998 | 0,00 % | 60,832 | +1,39 % | 0/121 |
| 80 | 80,000 | 0,00 % | 80,443 | +0,55 % | 0/121 |
* Ngưỡng `[đề xuất]` ≤ 3 % ⇒ đạt, nhưng ở 40 mm/s **chỉ hơn ngưỡng 0,02 %** (lần trước 1,84 %). Độ lệch này lớn hơn nhiễu điểm ảnh (1 điểm ảnh = 0,554 mm; 160 mm đường đi). Khả năng cao là tay (đang ở q = 0, nằm ngang qua băng trong ảnh) che một phần khối khi nó đi dưới tay, làm lệch tâm điểm ảnh `[nghi ngờ, chưa kiểm]`; GT không lệch. Sẽ hết khi tay về tư thế home ngoài khung ở E2.
* Băng vẫn nằm trọn khung (4 góc (98,9; 540,4)…(1181,1; 179,6)); 0,554 mm/điểm ảnh ở mặt băng. Tốc độ chạy 2,68 giây thật / giây mô phỏng (24 s mô phỏng, 484 khung; 64,3 s thật).
* **Hệ quả với tầm với `[tính từ mô hình động học của CL-0, chưa kiểm trên tay thật]`** (cùng script như `cl0/SETUP_REPORT.md`, z = −2,4 mm, φ = 90°, kẹp thẳng đứng, `t_to_grasp_s` + `follow_margin_s` = 2,8 s; script `scratchpad/reach_flush/plan_band.py`):
| bề rộng dải cần phủ | dải x (mm) | đoạn nhặt dài nhất | tốc độ băng tối đa (đoạn / 2,8 s) |
|---|---|---|---|
| 200 mm (cả bề rộng băng) | 20–220 | **58 mm** | 21 mm/s |
| 160 | 20–180 | 98 mm | 35 mm/s |
| 120 | 130–250 | 192 mm | 69 mm/s |
| **100** | **130–230** | **264 mm** | **94 mm/s** |
| 80 | 130–210 | 312 mm | 111 mm/s |
  * Phủ cả 200 mm bề rộng ở mặt băng ngang đế là **không khả thi**: (i) đoạn nhặt chỉ 58 mm; (ii) vị trí tốt nhất đặt mép gần của băng ở x = 20 mm, tức **chồng lên đế tay** (mesh đế rộng ±55,5 mm quanh trục pan). Băng thật cũng không đặt được ở đó.
  * Đề xuất mặc định `[chưa duyệt]`: giữ băng 200 mm đúng như đo, **chỉ đặt vật trong dải x = 130–230 mm** (rộng 100 mm, nằm trong băng x = 90–290), khoá `belt.object_band_x_mm` trong `scene.toml`. Khi đó tốc độ băng tối đa ≈ 94 mm/s: L = 0,25 (38 mm/s) và L = 0,5 (75 mm/s) khả thi với CL-0, **L = 1,0 (150 mm/s) vẫn không** (cần ≳ 420 mm).
  * Dải đặt vật hẹp ⇒ chỉ ảnh hưởng mọi phương pháp như nhau (cùng sắp xếp). Nhưng cần ghi trong báo cáo cuối: kết quả sim ứng với dải 100 mm, không phải cả bề rộng 200 mm của băng thật `[giới hạn]`.

### Chưa làm / chưa kiểm ở E1
* Vật lý kẹp (chạm má–vật), nhiều vật, ma sát thực: E4–E5.
* `isaacsim.asset.gen.conveyor`: không dùng nữa (vận tốc mặt băng đặt trực tiếp qua USD); ROS 2 bridge không dùng.
* Dây chuyền "lockstep" đầy đủ (trễ camera, bộ đếm xung ảo, `wait_tick`): E2.

**Người dùng trả lời (29/10, sau báo cáo cập nhật):** (1) duyệt dải đặt vật x = 130–230 mm ("dc, để trong khoảng đấy đi"); (2) băng thật **đã làm xong**, rộng 200 mm, không đổi được; (3) mặt băng ngang đúng bề mặt gần tay (xác nhận z = −2,4 mm). Ba điều này không còn là mặc định chưa duyệt. Giới hạn cần ghi ở báo cáo cuối: kết quả sim ứng với dải 100 mm, L = 1,0 không khả thi với CL-0 ở hình học này.

## 29/10/2026 — E2: `IsaacPlatform` và chạy CL-0 (đang làm; số SR điền khi lô chạy xong)

Chỉ mô phỏng. Người dùng duyệt dải đặt vật x = 130–230 mm, băng thật rộng 200 mm đã làm, mặt băng ngang đế.

### Mã mới (ngoài `cl0/`; `code_sha256` của CL-0 không đổi)
* `arena/arena/world.py` (`IsaacWorld`: cảnh, bước PhysX, camera, GT), `arena/arena/platform.py` (`IsaacPlatform`, lockstep), `arena/arena/objects.py` (bể vật), `arena/arena/trial.py` (một lượt, ghi GT/video), `arena/calib_from_scene.py`, `arena/scripts/e2_run_cl0.py`, `e2_summary.py`, các script dò `e2_*.py`.
* `configs/arena.toml`: bản sao `cl0.toml` + 11 khác biệt, mỗi cái chú thích "arena:" (đã in diff bằng `load_config`): đường dẫn calib/nền; camera 1280×720, `fourcc` rỗng, `latency_s` 0,098 (đo được); `belt.serial_port` rỗng; `home_q_deg` = [90, −49, 48, 91, 0]; `gripper_open` 40; `gripper_w_mm` 60; `tcp_offset_mm` = [−29, 0, 0]. Mọi thứ khác (executor, track, perception, belt) giữ giá trị của máy thật; CL-0 chưa được tinh chỉnh.

### Thiết kế lockstep (đã kiểm)
* Vật lý 300 Hz (đổi từ 240): 50 Hz điều khiển = 6 bước, 30 fps ảnh = 10 bước, đếm xung 100 Hz = 3 bước; không có đồng hồ thật. `wait_tick` tiến đúng 6 bước.
* Băng là **`cl0.hw.belt.Belt` thật** (kind = counter, không cổng serial): hồ sơ vận tốc thật theo `cmd_delay_s` 0,05 s và dốc 200 mm/s² của chính lớp đó, PhysX bám theo; bộ vi điều khiển ảo báo số xung nguyên (0,05 mm/xung `[mặc định, chưa đo]`) 100 Hz, trễ serial 3 ms.
* Camera: ảnh chụp tại bước chia hết cho 10, giao sau `latency_true_s` = 0,10 s; `Frame.t_capture` = lúc giao − `camera.latency_s`.
* **Đã đo độ trễ ảnh so với GT** (`runs/e2/render_lag/render_lag2.json`, tấm phẳng chạy 150 mm/s): công thức `update_transformations` + `orchestrator.step(delta_time=0)` trễ 0,0015 s (0,04 khung). Đã đo kèm hai bẫy:
  1. `app.update()` trong vòng lặp **bước thêm vật lý** (GT đi 292,5 mm thay vì 195 mm): cấm dùng.
  2. Sau một **teleport khớp** (tensor API), renderer chưa theo cho tới khi có một bước `simulate+fetch_results` (`runs/e2/home_probe`, ba lần dò mới đúng): reset luôn bước vật lý trước khi render.
* GT (vị trí vật, TCP, s thật của băng) đọc qua `world.gt_*`/`GTRecorder`; `IsaacPlatform` không lộ GT cho CL-0. Test chống rò rỉ viết ở E3.

### Hiệu chuẩn từ cảnh (`arena/calib_from_scene.py`; `runs/calib/calib_report.json`, log `logs/2026-10-29_*_e2_calib_from_scene.log`)
Dùng đúng hàm của CL-0 (`fit_plane_homography`, `fit_belt_motion`, `estimate_latency`, `auto_window`, `build_background`) trên dữ liệu mô phỏng. Hiệu chuẩn từ GT là **hoàn hảo**, mạnh hơn thật; tuỳ chọn nhiễu `--noise-px/--noise-mm` có sẵn, mặc định TẮT (giá trị chốt ở E8).
| đại lượng | đo được | đúng | ghi chú |
|---|---|---|---|
| homography (24 điểm) rms / leave-one-out | 0,198 / 0,238 mm | — | |
| kiểm giữ lại (12 điểm mới) | trung bình 0,192 mm, tối đa 0,389 mm | — | độc lập với phép khớp |
| hướng băng φ | 89,998° | 90° | |
| mm/xung | 0,05001 | 0,05 (+0,02 %) | |
| độ trễ camera (3 lượt) | 99,7 / 98,2 / 97,4 ms, trung vị 98,2 | 100 ms | thấp 2 ms: đúng bằng trễ serial 3 ms của bộ đếm |
Cửa sổ nhận thức a ∈ [−220, 220], b ∈ [−305, −75] mm, 881×461 điểm ảnh; nền σ trung vị 3,0 (= sàn), ngưỡng hiệu dụng 18 mức xám. Ảnh nền và cửa sổ đã mở xem: tay ở home nằm ngoài cửa sổ, chỉ có bóng mờ ở mép bàn. Thông số: `runs/calib/background_window.png`, `background_preview.png`.

### Ba phát hiện về mô hình tay/kẹp (mỗi cái làm CL-0 thất bại 100 % cho đến khi sửa)
1. **`gripper_frame_link` nằm trên mặt trong của má cố định, không ở giữa khe** (`runs/e2/tcp_offset.json`): ở `gripper.pos` = 40 khe trải x = −62…0 mm trong khung đó, tâm khe x = −29…−31 mm. Với `tcp_offset_mm` = 0 CL-0 đặt vật sát má cố định, tay hạ xuống chỉ tì lên vật (TCP kẹt ở z = 29 mm, đỉnh vật 22,6 mm). Đặt `tcp_offset_mm` = [−29, 0, 0] (ước lượng từ mesh nhìn thấy). **Nhắc cho tay thật:** `cl0.toml` hiện để `tcp_offset_mm` = [0,0,0]; tay thật cũng cần đo offset này (tâm khe ở `gripper_open` dùng), nếu không G0 sẽ thất bại từ lần đầu.
2. **Bao lồi mỗi link của USD đã chuyển đổi bóp khe thành hình phễu** (`runs/e2/jaw_hull.json`, mặt cắt y = 0 của bao lồi PhysX): khe 60 mm ở mũi, 46 mm ở cao 15 mm, 41 mm ở 20 mm, 30 mm ở 30 mm. Vật cao > 15 mm bị chêm và văng khi khép (`empty_grasp`; quan sát bằng camera chéo, `runs/e2/archive/smoke_debugcam_convexhull`). Đã chuyển ba khối va chạm của kẹp sang `convexDecomposition` (`scene.toml` `robot.gripper_collision`): hai lượt thử cùng vị trí chuyển từ `empty_grasp` sang `picked_hold_complete`, GT nhấc 70,6 mm và giữ 5,58 s (`runs/e2/smoke/`). [chưa kiểm] độ trung thực của phân rã so với má thật; E4 (ORACLE) kiểm.
3. **Bản đồ tầm với của CL-0 bỏ qua ảnh hưởng của roll lên điểm TCP** (docstring `reach.py`: lệch ≈ 8 mm với TCP của URDF). Với offset 29 mm sai số này lên tới ≈ 29 mm theo phương ngang: dải x = 130–230 mm có đoạn nhặt chung không dương theo bảng, còn x = 160–260 mm có 272 mm (bảng `reach_flush/band_fixed.py`). Hệ quả đã thấy: lượt `static` #000 vật ở x = 135 mm → `no_target` (CL-0 coi vật ngoài tầm). Đây là giới hạn của CL-0 gốc; **chưa sửa** (đổi thuật toán phải hỏi).

### Vật lý kẹp (sau lô đầu)
Lô đầu `runs/e2/archive/cl0_dev_run1_force0.5`: SR 5/40 = 12,5 %, 31 lượt `empty_grasp`. Nguyên nhân tách bằng phép thử vật lý thuần, không render, không nhận thức (`scripts/e2_grasp_probe.py`): đặt vật, IK của CL-0, hạ, khép, nhấc 60 mm, giữ.
* Lực kẹp 0,5 N·m (mình tự đoán) thì 0/30 giữ được. Với 2,5 N·m (= `max_force_nm`, số STS3215 người dùng đã dùng) thì 3/3 (`runs/e2/gp_f25`). Tăng ma sát lên 2,0 hay đổi về bao lồi không giúp (`gp_fric2`, `gp_hull`).
* Phải có **giới hạn tốc độ khớp kẹp** (150°/s `[giả định]`). Bỏ đi thì hàm đập vào vật và bắn vật đi với 0,46 m/s (`gp_f25_novel`).
* Kết quả lô đầu **nhạy với lịch sử**: cùng một lượt (#1) thành công khi là lượt đầu của tiến trình, nhưng khi chạy sau lượt #0 thì vật bị bắn lên 66 mm và tay bị hất 45 mm. Cả hai cách đều tái lập đúng y hệt (tất định với cùng lịch sử). Tái dựng bộ điều khiển CL-0 không đổi kết quả, nên nguồn là trạng thái của PhysX chứ không phải CL-0 (`runs/e2/diag_plain`, `diag_rebuild`).
* Sau sửa: quét 6 vật × 5 độ cao kẹp (8–24 mm), **28/30 giữ được**, tốc độ vật tối đa 0,16 m/s (`runs/e2/grasp_probe/grasp_probe.json`). Hai ca hỏng là vật dẹt 14–16 mm kẹp ở 24 mm (má nằm trên đỉnh vật).

### Kết quả E2 (`runs/e2/cl0_dev`, log `logs/2026-10-29_*_e2_batch2.log`, engine = isaac, vật TẠM)
CL-0 không đổi mã, `arena.toml`; mỗi lượt 1 vật trong dải x = 130–230 mm; hạt giống 1.
| Lô | n | thành công (GT) | SR [Wilson 95 %] | kết quả bộ điều khiển |
|---|---|---|---|---|
| băng đứng yên | 20 | 11 | 55 % [34, 74] | 11 `picked_hold_complete`, 6 `dropped_in_hold`, 2 `ik_fail`, 1 `no_target` |
| băng 38 mm/s (L = 0,25) | 20 | 9 | 45 % [26, 66] | 9 thành công, 10 `dropped_in_hold`, 1 `ik_fail` |
| tổng | 40 | 20 | 50 % [35, 65] | lượt không hợp lệ: 0/40 |
Theo vật: `bar50x25` 6/6, `flat45x30` 6/6, `cyl35` 4/7, `cyl28` 2/6, `cube35` 1/8, `disc45` 0/6. Trung bình 37 giây thật mỗi lượt.

Đã xem 3 video (khung chụp ở `runs/e2/cl0_dev/sheet_trial000{2,6}.png`, `sheet_trial0021.png`):
1. **#002 thành công** (`bar50x25`, băng đứng yên, x = 131 mm). Tay từ home quay ra, hạ, khép, nhấc. Vật bị má che trong ảnh từ trên suốt lúc giữ; khi trả về thì vật nằm lại trên băng ở chỗ tay thả.
2. **#021 thất bại `dropped_in_hold`** (`cyl35`, băng 38 mm/s). Tay đuổi theo xi lanh và khép được; lúc nhấc vẫn thấy xi lanh ở đầu má. Vật tuột trong pha `MOVE_HOLD` (GT: `lost_object` ở 3,92 s, đã nhấc 43 mm) và rơi xuống mép bàn gần đế.
3. **#006 thất bại `ik_fail`** (`cube35` xoay 45°, x = 164 mm, a = +60 mm). CL-0 chọn vật, bắt đầu `APPROACH` rồi bỏ ở 1,5 s vì IK hỏng; tay gần như không rời home.

Phân tích 16 lượt `dropped_in_hold` (`trial_*.json` + GT):
- `cube35` xoay: CL-0 coi khối vuông là đẳng hướng (`isotropic_theta_deg`) nên kẹp theo phương 90°, tức kẹp chéo, bề ngang tại điểm kẹp 43–49 mm. Đây là đặc tính của CL-0 gốc.
- Nhiều vật đã nhấc 28–48 mm rồi tuột trong `MOVE_HOLD`, lúc tay vung sang tư thế giữ. Có thể do tiếp xúc hoặc ma sát mô phỏng yếu hơn thật. `[chưa kiểm]`: `ORACLE` ở E4 sẽ phân định.

**Kết luận E2:** đạt tiêu chí "Xong khi" (≥ 20 lượt tĩnh + ≥ 20 lượt băng chậm, không sập, có log, đã xem 3 video, có SR). SR 50 % chưa nói gì về CL-0 trên tay thật: vật tạm, chưa tinh chỉnh, vật lý kẹp mới chỉnh, và còn nghi vấn ở pha `MOVE_HOLD`.

## 29/10/2026 — E3: runner, nhãn lỗi, báo cáo, test

### Mã (gói `arena/arena/`, ngoài `cl0/`)
* `run_arena.py`: phương pháp × ô × tốc độ × sắp xếp (× lặp). Thứ tự: sắp xếp → tốc độ → phương pháp.
  - Ghi một dòng `trials.csv` mỗi lượt (cột `cl0.run_g0.CSV_COLUMNS` + cột arena), `trial_XXXX.json`, `trial_XXXX_log.csv`, `trial_XXXX_gt.npz`, video tuỳ chọn và `manifest.json` (Isaac, hash `arena/`, `code_sha256` của cl0, hash cấu hình/USD/calib/tờ sắp xếp, GPU, VRAM đỉnh).
  - Chạy lại thì tiếp tục từ chỗ dở. Các tuỳ chọn: `--shuffle-seed`, `--hard-reset`, `--scene-set`, `--depth`, `--record-demos`.
  - Từ chối ô `test_*` nếu không có `--allow-locked`.
* `labeler.py` cài đúng `LABEL_RULES.md` (viết trước khi dùng): thành công M1, sạch M2, nguyên nhân M4 trong danh sách đóng, thời gian M5.
  - Đã đổi quy tắc 4 (`calib`) một lần, **trước mọi so sánh**: dùng ước lượng cuối trước `CLOSE` thay vì lúc `select`. Lý do và bằng chứng ghi trong nhật ký đổi quy tắc ở cuối `LABEL_RULES.md`.
* `report.py`: mẫu §6.3 (SR + Wilson, SR sạch, hiệu ghép cặp với McNemar và bootstrap, nguyên nhân, M5, M6, M8, M9, cổng S0). Wilson/McNemar/bootstrap gọi thẳng `dir1/g0_analyze.py`.
* `methods/`: hợp đồng + sổ đăng ký.
  - Phương pháp có sẵn: `CL0` (không đổi mã), `NOOP`, `ORACLE` (đặc quyền), `CL0_YAW` (biến thể **không phải baseline**), `REMOTE` (phương pháp ở môi trường Python khác, `remote_server.py`).
  - Bộ chuyển cho phương pháp phát hiện điểm kẹp trên ảnh (`pixel_grasp.py`) và một ví dụ (`examples/blob.py`).
  - Hướng dẫn: `arena/arena/methods/README.md`.
* Chống rò rỉ GT: đồng hồ băng không còn tham chiếu tới thế giới (`_StepClock`). `ORACLE` nhận GT tại **đúng lúc chụp** khung, qua `GTTap`, chỉ phát cho phương pháp đặc quyền.
* Phương pháp không dùng điểm ảnh (`NOOP`, `ORACLE`) thì bỏ qua render RTX (vật lý không đổi): khoảng 15 s/lượt thay vì 35–60 s.

### Test: `cd arena && env -u PYTHONPATH ~/venvs/cl0/bin/python -m pytest tests -q` → **36 passed**, không cần Isaac (thế giới giả)
Bộ test kiểm:
* lockstep: tick = 6 bước; khung đến sau đúng 0,1 s; `t_capture` đúng; chỉ trả khung mới nhất; bộ đếm băng bám hồ sơ thật trong giới hạn lượng tử hoá + trễ serial; reset bắt được vật bị văng;
* rò rỉ GT: duyệt thuộc tính sâu 6 tầng từ khung, trạng thái và băng mà phương pháp nhận, không tới được thế giới, platform hay GT; chỉ phương pháp đặc quyền nhận `gt`; `ORACLE` thấy vị trí lúc chụp, không phải hiện tại;
* hợp đồng: `CL0`, `CL0_YAW`, `ORACLE`, `NOOP`, ví dụ plug-in nạp theo đường dẫn; exception trong phương pháp = thất bại của phương pháp;
* hình học: `ORACLE` và bộ chuyển điểm ảnh đổi sang hệ băng đúng;
* nhãn: thành công, `slip`, `collision`, `timing` và `grasp_point`, `seg_miss`, `merge`, `calib`;
* metrics: khớp `g0_analyze`; `g0_analyze.read_trials` đọc `trials.csv` không cảnh báo;
* tờ sắp xếp: vật nằm trong dải 130–230 mm, đúng mức clutter;
* cầu nối REMOTE: hai tiến trình thật;
* bộ vật E5.

### Chạy thử đầu tiên (`runs/e3_smoke`, 12 lượt, `metrics_report.md`)
Đường ống trọn vẹn. Hai phát hiện:
1. **Bản đồ tầm với của CL-0 không biết góc kẹp.** Ở `dev_C0_001` (xi lanh, x = 147 mm), cả `CL0` lẫn `ORACLE` bản đầu đều `no_target`.
   - IK cho thấy tư thế nhấc (+60 mm) chỉ giải được khi trục khép xoay 45–135°. CL-0 kẹp vật tròn theo góc cố định (`isotropic_theta_deg` = 90 với φ = 90°, tức trục khép hướng tâm), mà góc này vi phạm biên khớp. Bản đồ dựng với roll = 0 nên CL-0 coi vật là ngoài tầm.
   - Từ đó: `ORACLE` dùng kiểm khả thi bằng IK đúng góc kẹp (`methods/yawfeasible.py`, `reach_yaw.py`) và kẹp vật tròn theo phương tiếp tuyến. `CL0_YAW` = CL-0 + kiểm khả thi đó, để đo cái giá của giới hạn này. **CL-0 không bị sửa.**
2. **Thị sai của vật cao.** CL-0 "đóng băng" ước lượng ở 0,46–0,52 s, khi vật còn ở a = −150 mm, nên đỉnh xi lanh cao 40 mm lệch 8,4–9,8 mm dọc băng và sai số giữ tới lúc kẹp (nhãn `calib`). Đây là giới hạn thật của CL-0: nó không biết chiều cao vật.

### Còn lại của E3
* M8 (tái lập và phụ thuộc thứ tự, có/không `--hard-reset`): `scripts/e3_repeat.sh`, chạy sau khi chốt vật lý ở E4.
* Kiểm tay 30 lượt thất bại so với nhãn tự động.

## 29/10/2026 — E4: `NOOP` / `ORACLE` và vật lý kẹp (đang làm; số cuối ở mục sau khi chuỗi `scripts/run_e4_to_e6.sh` xong)

### `ORACLE` = trần của môi trường
`ORACLE` dùng:
* bộ điều khiển của CL-0 (bộ theo dõi, chọn vật, `BeltExecutor`);
* nhận thức từ GT lúc chụp khung;
* kiểm khả thi bằng IK đúng góc kẹp;
* trục khép tiếp tuyến cho vật tròn.

### Lần chạy đầu (`runs/e4_bounds`, dừng ở 38/80 khi mẫu lỗi đã rõ)
* `NOOP` 0/19: không có thành công giả.
* `ORACLE`: băng đứng yên 8/9; L0.25 6/9. Mọi lượt hỏng đều là `dropped_in_hold` (`slip`): vật tuột lúc nhấc hoặc lúc vung sang tư thế giữ.

### Tìm nguyên nhân (mọi thay đổi là giả định vật lý có ghi chú, không đụng phương pháp)
| thử | kết quả | bằng chứng |
|---|---|---|
| ma sát má 1,0 / 1,5 / 2,0 (6 sắp xếp từng hỏng) | đứng yên 5/6 → 6/6 → 6/6; L0.25 vẫn 4/6 | `runs/e4/or_base`, `or_fric15`, `or_fric20` |
| ma sát xoắn: đệm có diện tích, `torsionalPatchRadius` 5 mm | đứng yên 6/6 | `runs/e4/or_tors5*` |
| 20 lượt L0.25: ma sát 1,5 + ma sát xoắn (B) | **16/20 = 80 %** | `runs/e4/var_B_fric15_tors5` |
| B + tăng vòng lặp bộ giải 32/4 (C) | 15/20 | `runs/e4/var_C_B_iters32` |
| B + khép chậm 90°/s (D) | 11/20 (má chưa siết xong thì CL-0 đã nhấc: CL-0 chỉ chờ 0,7 s) | `runs/e4/var_D_B_grip90` |
| phép thử kẹp + vung không có nhận thức (`scripts/e2_grasp_probe.py --swing`) | 11/12; 10/12 khi tăng vòng lặp | `runs/e4/gp_*` |

**Chọn B làm mặc định** (`scene.toml`: `pad_friction` 1,5; `torsional_patch_radius_mm` 5 cho má và vật). Đây là giả định, E8 phải đo lại trên tay thật.

### Cơ chế hỏng còn lại
1. **Đĩa thấp và rộng** (`disc45`: rộng 45 mm, cao 16 mm) hỏng **3/3** lần ở L0.25.
   - Khe má SO-101 hình chữ V vì má động xoay quanh khớp: 60 mm ở mũi, 46 mm ở cao 15 mm (`runs/e2/jaw_hull.json`). Với TCP ở 10 mm trên băng, má chạm **mép trên** của đĩa thay vì hông đĩa, nên vật bị nêm ra khi nhấc.
   - Đây là giới hạn hình học của tổ hợp vật + kẹp + độ cao kẹp cố định của CL-0, nhiều khả năng cũng đúng trên tay thật `[chưa kiểm trên tay thật]`.
   - Bỏ đĩa ra thì B đạt 16/17 = 94 %.
2. **Băng chạy:** khi khép, má động đẩy vật về phía má cố định (+5,6 mm, cả lúc băng đứng yên). Lúc nhấc trên băng chạy, vật trượt dọc mặt má (−1 → −9 mm trong 0,2 s) rồi rơi. Cặp đối chứng cùng sắp xếp (`dev_C0_009`, băng đứng yên thì thành công) ở `runs/e4/or_tors5f15`.
   - Giả thuyết: má chữ V ép vật xuống băng đang chạy, ma sát băng "nạp" lực tiếp tuyến vào vật. `[chưa kiểm]`

### Xác nhận kẹp (30/10/2026)
Người dùng xác nhận kẹp thật ("yaw gripper") **giống kẹp gốc SO-101 trong sim**: má động xoay quanh trục servo kẹp, quét trong mặt phẳng (trục khép, trục tiến vào). Hình đối chiếu: `runs/e8_gripper/sim_gripper_views.png` (`scripts/e8_gripper_views.py`, vẽ thẳng từ STL và URDF chính thức).

Hệ quả:
* Hình học của sim là của tay thật: khe chữ V (60 mm ở mũi, 46 mm ở cao 15 mm khi `gripper.pos` = 40), `gripper_frame_link` nằm trên má cố định, tâm khe ở x ≈ −29 mm.
* Các con số vật lý (lực, tốc độ khép, ma sát đệm) vẫn là giả định, để E8 đo.

### Kết quả E4 chính thức (29/10 tối, chuỗi `scripts/run_e4_to_e6.sh`, log `logs/2026-10-29_*_chain_e4_e6.log`; vật lý mặc định = biến thể B)
| bộ vật | ô | `NOOP` L0 / L0.25 | `ORACLE` L0 | `ORACLE` L0.25 | bằng chứng |
|---|---|---|---|---|---|
| tạm (6 vật) | dev_C0 | 0/20 / 0/20 | **20/20** | 16/20 = 80 % | `runs/e4_final_interim/metrics_report.md` |
| sinh (36 vật) | dev_C0 | 0/20 / 0/20 | 19/20 = 95 % | **18/20 = 90 %** [70, 97] | `runs/e4_final_sim/metrics_report.md` |
| sinh | dev_C2 | 0/20 / 0/20 | 20/20 | 18/20 = 90 % | như trên |
Lượt không hợp lệ: 0/240.

**Cổng S0a** (ngưỡng `[đề xuất]`): `NOOP` ≈ 0 % **đạt** (0/120). `ORACLE` ≥ 95 % ở C0, L0.25 **chưa đạt** (90 % với bộ vật sinh, 80 % với bộ vật tạm).

Lượt hỏng của `ORACLE`:
* Bộ vật tạm: 3/4 là đĩa `disc45` tuột lúc nhấc (giới hạn hình học, xem trên), 1 là `cyl28` tuột lúc vung.
* Bộ vật sinh:
  * 3/5 là `late`: logic thời gian của bộ thực thi CL-0 bỏ vật vì "vật sắp ra khỏi vùng với tới trước khi nhấc xong".
  * 1 là `ik_fail` khi tiếp cận `cyl22` (trụ cao, mảnh).
  * 1 là `slip`.
* Vậy với bộ vật sinh, phần lớn giới hạn còn lại nằm ở **bộ thực thi của CL-0** (mà `ORACLE` dùng chung theo thiết kế), không ở vật lý hay nhận thức.

### CL-0 và `CL0_YAW` (`runs/e4_cl0_interim`, vật tạm, dev_C0, 20 cặp)
| | L0 | L0.25 |
|---|---|---|
| `CL0` | 14/20 = 70 % | 11/20 = 55 % |
| `CL0_YAW` | 15/20 = 75 % | 12/20 = 60 % |
* `CL0_YAW` hơn 1 cặp ở mỗi tốc độ (+5 %, McNemar p = 1,0). Giới hạn bản đồ tầm với của CL-0 chỉ tốn khoảng 1/20 ở ô này.
* **Cổng S0b** (CL-0 ≥ 80 % ở `dev_C0`): **chưa đạt**, CL-0 **chưa được tinh chỉnh** trong sim.
  * Băng đứng yên: 5 `slip`.
  * L0.25: 4 `grasp_point`, 2 `calib` (thị sai), 3 `slip`.

### M8: tái lập (`runs/e3_repeat`, `ORACLE`, 20 sắp xếp × L0/L0.25)
| so sánh | cùng kết quả |
|---|---|
| thứ tự thường so với xáo trộn, không dựng lại cảnh | 38/40 (2 lượt đổi kết quả) |
| thứ tự thường so với xáo trộn, **dựng lại cảnh PhysX mỗi lượt** | **40/40** |
* Dựng lại cảnh không tốn thêm thời gian (14,4 s/lượt cả hai cách), nên **đã thành mặc định** của `run_arena` (tắt bằng `--no-hard-reset`).
* **Cổng S0c: đạt** (100 % với chế độ mặc định).

## E5: bộ vật (sinh theo thủ tục, không tải gì)
* 36 vật ghép từ khối nguyên thủy (va chạm chính xác): train 20 / dev 6 / test 10. Tập test có lõm/quai (U, vòng, cốc), mỏng (tấm 5–6 mm), tương phản thấp (xám tối).
  * `configs/objects_sim.csv` + `.json`, sinh bằng `python -m arena.objects_gen --seed 5`.
  * Ảnh: `runs/e5/objects_sheet.png` (đã mở xem).
* Tờ sắp xếp: `arrangements/sim/{train,dev}_C0..C3.csv`. **Test ở `locked/`** (`test_C0`, `test_C2`, `test_C3`); `run_arena` từ chối nếu không có `--allow-locked`.
* Ổn định C3 (vật chạm nhau, băng đứng yên, 1 s): **train 60/60, dev 60/60**, trôi tối đa 0,45 mm (ngưỡng 2 mm) (`runs/e5/c3_stability.json`). Tờ test **không kiểm** vì đang khoá.
* Mesh quét thật (Google Scanned Objects, CC-BY 4.0, khoảng 13 GB toàn bộ): **chờ người dùng duyệt**, chưa tải.

## E6: demo của chuyên gia (`ORACLE`) → LeRobotDataset
* `run_arena --record-demos`: ghi ở 30 fps ảnh 640×360 JPEG, `observation.state` = 6 khớp đo được, `action` = 6 đích đã ra lệnh. Tên đặc trưng giống `lerobot-record` của SO-101 (`shoulder_pan.pos … gripper.pos`).
* 60 lượt ở `train_C0`, `train_C2`, L0 và L0.25 → **51 tập thành công** được giữ (`runs/e6_demos/episodes`).
* Chuyển đổi bằng `to_lerobot.py` trong venv riêng **`~/venvs/lerobot_data`**: dùng lại LeRobot 0.6.1 và torch của `~/venvs/cl0` qua một file `.pth`, chỉ cài thêm `datasets` 4.8.5, `pandas` 2.3.3, `pyarrow` 26, `av` 15.1 (LeRobot ghim < 16), `torchcodec` 0.11.1, `jsonlines`. **Venv `cl0` không bị đổi.**
* Kết quả: `runs/e6_demos/lerobot` (`local/arena_so101_oracle`).
  * 51 tập, 13 471 khung, 30 fps, độ dài 244–313 khung (trung bình 264), 31,9 MB.
  * `LeRobotDataset` nạp lại không lỗi, ảnh 3×360×640 (`runs/e6_demos/dataset_summary.json`). Đã xem khung mẫu (`runs/e6_demos/episode_check.png`).
* **Chưa huấn luyện gì** (GPU, chờ người dùng).

## 30/10/2026 — E7: cắm phương pháp (đã kiểm trong Isaac)
* **Ảnh độ sâu** (`--depth`, `scripts/e3_depth_check.py`, `runs/e3_depth/depth_check.json`): mặt băng 512,4 mm, đỉnh hộp 25 mm 487,4 mm, đỉnh trụ 40 mm 472,4 mm, **sai 0,0 mm** so với hình học. Căn đúng điểm ảnh với ảnh màu.
* **Plug-in theo đường dẫn module** (`arena.methods.examples.blob:make_method`, bộ phát hiện theo vết màu qua `pixel_grasp.py`): chạy trọn trong Isaac, 4/6 thành công (`runs/e7_plugins`). Đây là ví dụ, **không phải baseline**.
* **Cầu nối REMOTE** (`remote_server.py`; phục vụ CL-0 từ tiến trình khác bằng `arena/methods/examples/remote_cl0.py`):
  * Băng đứng yên: `REMOTE:CL0` **trùng từng bit** với CL-0 trong tiến trình (`runs/e7_plugins`).
  * Băng chạy: cùng outcome, cùng `t_end`, nhãn khớp 3/3 sau khi server nhận **toàn bộ lịch sử bộ đếm** và tính `s_at`/`speed_at` bằng đúng thuật toán `cl0.hw.belt._History` (`runs/e7_remote_check`). Quỹ đạo vẫn lệch 0,16–0,32 mm từ tick đầu của pha tiếp cận.
  * Nguyên nhân của độ lệch còn lại **không** nằm ở cầu nối, đã tách được: chạy CL-0 **hai lần trong cùng tiến trình** trên cùng sắp xếp cũng lệch y như vậy (`runs/e7_det_check`, có md5 của từng khung).
* **Renderer RTX không tất định từng bit** (`scripts/e7_render_noise.py`, `runs/e7_render_noise.json`).
  * Ảnh khác nhau ngay từ khung đầu giữa hai lần chạy, trong khi vật lý trùng khớp tới khi lệnh dựa trên ảnh bắt đầu.
  * Với cảnh tĩnh, hai khung liên tiếp chênh **trung bình 0,08–0,36 mức xám**; 0,3–2,5 % số điểm ảnh lệch quá 2 mức (đa số ở mép). Mức này tương đương hoặc nhỏ hơn nhiễu cảm biến của camera thật.
  * Đã thêm 8 lần render bỏ đi lúc reset để xả bộ đệm thời gian (`camera.warm_renders`), nhưng việc này không làm ảnh tất định.
  * Kết luận: **phương pháp không dùng ảnh** (`ORACLE`, `NOOP`) lặp lại trùng từng bit (40/40, M8). **Phương pháp dùng ảnh** có ngẫu nhiên nhỏ như máy thật: M8 đo bằng thống kê (`--reps`), và so sánh dùng ≥ 3 lần lặp (§7 S0c). `report.py` báo "nhóm lặp cùng kết quả" cho mỗi phương pháp.

### 31/10/2026 — M8 của CL-0 và sửa `report.py`
* `runs/e3_repeat_cl0` (`CL0`, vật tạm, `dev_C0`, 20 sắp xếp × L0/L0.25 × 2 lần lặp, có nhiễu render): **40/40 nhóm lặp cùng kết quả**. SR 15/20 = 75 % (L0) và 12/20 = 60 % (L0.25), chưa tinh chỉnh; vẫn dưới ngưỡng S0b. Số này cao hơn lần chạy trước (70 %, 55 %) 1 sắp xếp mỗi tốc độ; lần trước chưa có `warm_renders`.
* **Sửa lỗi:** `report.py` từng tính mỗi lần lặp là một lượt độc lập (n bị thổi, Wilson và McNemar hẹp giả). Nay gộp theo sắp xếp, đa số thắng, hoà tính thất bại và báo `n_ties`. Có test. Báo cáo của lần này được sinh lại từ `trials.csv`; dữ liệu thô không đổi. `dir1/g0_analyze.py g2` vẫn ghép theo từng lần lặp, nên khi có `--reps` thì dùng `arena.report`.
* Lời khuyên `--reps 3` trước đây đã bỏ: với CL-0 lần lặp không thêm thông tin, thêm sắp xếp mới thêm thông tin.

## 31/10/2026 — Quyết định của người dùng và GG-CNN
Người dùng ("theo ý m đi") chọn theo đề xuất:
* **S0a:** chấp nhận `ORACLE` 90 % ở L0.25 (bộ vật sinh) là trần của môi trường + bộ thực thi CL-0, ghi rõ trong báo cáo cuối. Ngưỡng 95 % không bị đổi: cổng ghi là chưa đạt, có lý do.
* **CL-0:** chưa tinh chỉnh trong sim; giờ tinh chỉnh dành cho tay thật.
* **GG-CNN:** cắm vào arena làm ứng viên CL-2.

### GG-CNN (`arena/methods/ggcnn.py`, tên `GGCNN`, cần `--depth`)
* Trọng số Cornell từ release v0.1 của `dougsm/ggcnn` (BSD-3), zip 476 kB, sha256 `465ef506…`, `third_party/ggcnn_weights`. Chỉ giải nén file state dict.
* **Không chạy mã của repo:** lần đầu định nạp `models/ggcnn.py` thì bị bộ phân loại an toàn của Claude Code chặn. Mạng được khai báo lại trong `ggcnn.py` theo kiến trúc đã công bố; `load_state_dict` khớp đủ khoá, nạp bằng `weights_only=True`. Bản clone `third_party/ggcnn` chỉ để đọc.
* Lựa chọn của mình, không có trong paper: cắt theo cửa sổ băng, cổng độ cao 3 mm so với mặt băng, tìm cực đại địa phương, thang 1,2 mm/điểm ảnh đầu vào `[ước lượng, chưa kiểm]`, và **chặn bề rộng ở 56 mm thay vì loại**. Lý do: bề rộng dự đoán theo kẹp của bộ Cornell, lần đầu cả 598 khung đều bị loại (`runs/e2/archive/e7_ggcnn_try_width_reject`).
* Chạy thử băng đứng yên, vật tạm: 3/3 thành công (`runs/e7_ggcnn_try`; lệnh bị hết giờ trước khi xong lượt 4, không có dòng nào bị sửa). Kể cả vật ở x = 147 mm mà CL-0 `no_target`.
* So sánh đầy đủ: `runs/e7_cl0_vs_ggcnn` (đang chạy).

### Sửa lỗi: độ sâu không tới bộ chuyển `pixel_grasp`
`pixel_grasp` đọc `depth_mm` trên mảng ảnh còn platform chỉ gắn vào `Frame`, nên phương pháp dùng độ sâu qua bộ chuyển này luôn nhận `None`. Nay ảnh là `ImageWithDepth` mang theo `depth_mm`; có test. 40 test đều qua.

## Bố trí thật do người dùng gửi (sơ đồ `docs_input/layout_sketch_user.png`), CHƯA đưa vào `scene.toml`
Mình đọc sơ đồ như sau `[chờ người dùng xác nhận, đơn vị giả định là cm]`:
* Băng 91 × 20 cm (sim đang 60 × 20).
* Tấm đế tay 28 × 28 cm, sát cạnh dài của băng, trải từ 36 đến 64 cm tính từ đầu trái băng.
* Camera ở cạnh băng phía đối diện tay, cách đầu trái 22 cm, cao **50 cm so với mặt băng** (người dùng nói rõ).

Tính từ mô hình động học, chưa kiểm trên tay thật (`scripts/e8_real_layout_reach.py`, offset TCP −29 mm, kẹp 10 mm trên băng, nhấc 60 mm, trục khép tiếp tuyến):
| khoảng cách tới trục pan (mm) | 100 | 140 | 180 | 200 | 220 | 240 trở đi |
|---|---|---|---|---|---|---|
| đoạn nhặt dài nhất dọc băng (mm) | 420 | 380 | 300 | 240 | 160 | 0 |

Camera thẳng đứng ở 50 cm thấy 692 × 389 mm trên mặt băng. Còn phải biết: khoảng cách trục pan tới mép băng, camera có nghiêng không, chiều chạy băng.

### Trạng thái `runs/e7_cl0_vs_ggcnn` (hình học cũ của sim)
Phiên trước kết thúc ở 82/160 lượt. `dev_C0` đủ 20 sắp xếp mỗi ô: L0: CL0 17/20, GGCNN 18/20 (p = 1,0); L0.25: cả hai 18/20 (p = 1,0). Chưa đủ để kết luận khác nhau. Trên bộ 36 vật, CL-0 đạt ≥ 80 % ở `dev_C0` (bộ vật tạm chỉ 75 %, 60 %). `dev_C2` chạy tiếp từ chỗ dở.

### Trả lời của người dùng về bố trí (sau sơ đồ)
* Muốn đặt tay "sát rìa, không kề với băng"; camera nhìn thẳng xuống, lệch vào phía trong băng (chưa có số); băng chạy từ trái sang phải trong sơ đồ (khớp φ = 90°).
* Tính từ URDF và STL (`scripts/e8_real_layout_edge.py`, kinematics, chưa kiểm trên tay thật): đế tay trải từ 69,8 mm sau trục pan tới 25,8 mm trước trục pan, rộng 111 mm. Tầm với xa nhất thẳng phía trước, offset TCP −29 mm: nhấc 60 mm được 236 mm (trục khép tiếp tuyến), 258 mm (hướng tâm); nhấc 30 mm được 262, 284 mm; chỉ kẹp ở 10 mm được 272, 294 mm.
* Hệ quả nếu lưng đế sát cạnh xa của tấm 28 cm: trục pan cách mép băng khoảng 210 mm, tay chỉ với tới khoảng 26 mm bề rộng băng. Chưa đổi `scene.toml`, chờ người dùng chọn.

## 31/10/2026 — Bố trí thật đưa vào sim
Người dùng sửa sơ đồ: cạnh tấm đế là **18 cm**, không phải 28; camera lệch vào trong băng khoảng 10 cm; tay sát cạnh xa băng; băng chạy trái sang phải.
* `configs/scene.toml` (bản cũ: `configs/archive_scene_simlayout_v1.toml`, hiệu chuẩn cũ: `runs/calib_simlayout_v1`): băng 91 × 20 cm, mép gần cách trục pan 110 mm, tâm băng x = 249 mm; camera thẳng xuống tại (249, −280, 497,6) mm tức trên đường giữa băng, cách đầu trái 22 cm, cao 50 cm so với mặt băng.
* `[giả định, chờ xác nhận]`: 18 cm là cạnh vuông góc băng; tấm vuông 18 × 18; tay nằm giữa tấm và cách đầu trái băng 50 cm.
* Dải đặt vật chuyển theo băng: x = 155–255 mm (116–216 mm từ trục pan), đoạn nhặt chung 200 mm, băng tối đa ≈ 71 mm/s (L ≈ 0,48), tính từ động học. Khi băng đứng yên, sắp xếp đặt quanh a = −40 mm. **Dải 10 cm giờ nằm ở nửa băng gần tay.**
* Hiệu chuẩn từ cảnh (`runs/calib`): homography rms 0,206 mm, kiểm giữ lại tối đa 0,165 mm; hướng băng 90,031°; mm/xung 0,05000; độ trễ 97,9 ms. Ảnh `background_window.png` đã xem.
* Phương án so sánh, không phải bố trí của người dùng: camera tại (205, −100) mm (`configs/scene_cam_near.toml`, `runs/calib_cam_near`).
* So sánh đang chạy: `scripts/e8_camera_compare.sh` → `runs/e8_real`, `runs/e8_cam_near`.

### Kết quả `runs/e7_cl0_vs_ggcnn` (bố trí cũ của sim, bộ 36 vật, 20 sắp xếp mỗi ô, engine = isaac)
| ô | L | CL0 | GGCNN | McNemar p |
|---|---|---|---|---|
| dev_C0 | 0 | 17/20 | 18/20 | 1,0 |
| dev_C0 | 0,25 | 18/20 | 18/20 | 1,0 |
| dev_C2 | 0 | 17/20 | 14/20 | 0,51 |
| dev_C2 | 0,25 | 15/20 | 18/20 | 0,45 |
Chưa thấy khác biệt có ý nghĩa; n = 20 chỉ phát hiện được chênh lớn. Cần chạy lại trên bố trí thật trước khi dùng.

### Xác nhận tấm đế (31/10/2026)
Người dùng: cạnh vuông góc với băng = 18 cm; tay nằm trên tấm đế. Vậy tấm 18 cm × 28 cm (cạnh 28 dọc băng theo sơ đồ, 36–64 cm từ đầu trái). `scene.toml` và `scene_cam_near.toml`: `table.half_width_mm` 90 → 140. Vị trí tay dọc băng chưa đo, giả định giữa tấm (trục pan cách đầu trái 50 cm).
* Lần chạy dở với tấm 18 × 18 lưu ở `runs/archive/e8_real_plate18x18` (65 lượt), hiệu chuẩn ở `runs/archive/calib*_plate18x18`; không dùng cho kết luận.
* Hiệu chuẩn lại `runs/calib`: rms 0,231 mm, kiểm giữ lại tối đa 0,228 mm, độ trễ 98,1 ms. `runs/calib_cam_near`: rms 0,281 mm, tối đa 0,150 mm, 98,3 ms.

### E6 lần 2: 400 demo trên bố trí thật (người dùng chọn 31/10)
`scripts/e6_record_400.sh` → `runs/e6_demos_real`: `ORACLE`, vật TRAIN, `train_C0..C3` (60 sắp xếp mỗi ô), L0 và L0.25, 480 lượt, chỉ giữ tập thành công, mục tiêu ≥ 400. Chạy sau `e8_camera_compare.sh`. 51 tập cũ (`runs/e6_demos`) theo bố trí cũ, chỉ để thử. Dùng camera của người dùng; nếu sau này dời camera thì phải ghi lại.

**E6 lần 2, sự cố treo chậm (1/11).** 254 lượt đầu 40 giây/lượt. Từ giữa lượt #0254 (khoảng 23:17:46 ngày 31/10), thời gian dựng hình tăng từ 0,07 lên khoảng 50 giây/khung, GPU gần như rảnh, không có lỗi trong log; 4 lượt mất 8.192 đến 13.275 giây. Log hệ thống ghi `systemd-journald: Time jumped backwards` lúc 23:17:42, trùng thời điểm; nguyên nhân gốc chưa chứng minh. Khung hình của các lượt chậm đã kiểm (0256, 0257): không đen, không có khung trùng, số liệu như lượt thường; giữ lại. Tiến trình bị dừng lúc 13:52 ngày 1/11 và chạy tiếp bằng `scripts/e6_record_400_resume.sh`; 5 lượt đầu sau khởi động lại 45 đến 48 giây/lượt. Script có watchdog: 5 phút không có lượt mới thì giết và chạy tiếp. Lệnh gốc trong `manifest.json` vẫn là `--n 60`; phần chạy tiếp dùng `--n 70 --arrangements-dir arrangements/sim_ext` (cùng seed, 60 sắp xếp đầu giống hệt đã so) vì `ORACLE` chỉ đạt khoảng 76% trên vật train, 480 lượt không đủ 400 tập.

**So sánh camera (`runs/e8_real`, `runs/e8_cam_near`), CL0, cùng sắp xếp, n = 20.** dev_C0 L0: thật 12, gần 20 (p = 0,008; 6 lỗi `cyl22` `empty_grasp`, 2 lỗi `mug24`). dev_C0 L0.25: 17 và 18 (p = 1). dev_C2 L0.25: 17 và 14 (p = 0,51). ORACLE trên camera thật dev_C0: 20/20 và 20/20; NOOP: 0/40. Giả thuyết cho `cyl22`: thị sai của vật cao 36,7 mm ở xa tâm camera (khoảng 19 mm với camera thật, khoảng 5 mm với camera gần, tính hình học), [chưa kiểm] bằng sai số gắp đo trực tiếp.

**Quyết định camera (người dùng, 1/11):** giữ camera hiện tại `[249, -280, 497.6]`; không ghi lại demo. Mục tiêu người dùng nêu: tốt và ổn định trong môi trường nhiều vật. Đã biết và chấp nhận: CL0 `dev_C0` L0 = 12/20, dưới ngưỡng S0b. `scripts/e9_clutter_real.sh` → `runs/e9_clutter_real`: CL0 và ORACLE trên `dev_C1..C3`, L0 và L0.25, n = 20, rồi lần lặp thứ hai của CL0 để đo độ lặp lại (360 lượt); chạy sau khi ghi demo xong.

**E6 lần 2, kết quả (1/11).** `runs/e6_demos_real`: 560/560 lượt, 444 tập thành công, 0 lượt không hợp lệ, không có lần treo nào sau khi khởi động lại. `runs/e6_demos_real/lerobot`: đọc lại bằng LeRobot được 444 tập, 115.908 khung, khớp số khung thô; tập cuối khớp trạng thái thô ở khung đầu (sai 0,0). Chuyển đổi hết 51 phút. `engine=isaac`, chỉ dùng cho sim. `runs/e9_clutter_real` bắt đầu 18:36.

**E9 nhiều vật trên bố trí thật (`runs/e9_clutter_real`, 1/11, DEV, n = 20).** CL0 lần 1/lần 2, ORACLE: C1 L0 15/14, 20; C1 L0.25 14/14, 20; C2 L0 12/12, 20; C2 L0.25 16/17, 18; C3 L0 2/2, 18; C3 L0.25 13/14, 14. Lặp lại 113/120 nhóm; 0/360 lượt không hợp lệ. Theo vật (CL0): `cyl22` 4/20, `mug24` 13/30; ORACLE trên hai vật đó 11/12 và 18/19. `scripts/e9_detect_probe.py` → `runs/e9_detect_probe`: ở dev_C3 tĩnh tâm a = -40, 16/20 đống vật dính thành một khối chạm mép cửa sổ camera và bị loại `edge`. Thử điều kiện tâm a = -70: `scripts/e9_static_center.sh` → `runs/e9_static70`; `scene.toml` không đổi.

**Treo dựng hình lặp lại:** watchdog giết 7 lần trong 18:36–22:00; 7 dòng `Time jumped backwards` trong cùng khoảng, 5 lần giết rơi gần một dòng; hai lần còn lại (21:04, 21:30) không có dòng tương ứng ngay lúc đó. Lượt bị giết không ghi kết quả và được chạy lại. Nguyên nhân gốc chưa chứng minh.

**E9 tâm đống vật a = -70 (`runs/e9_static70`, 2/11, L0, n = 20, 0/160 không hợp lệ).** CL0 từ -40 sang -70: C0 12 → 10 (p = 0,5), C1 15 → 11 (p = 0,125), C2 12 → 15 (p = 0,45), C3 2 → 10 (p = 0,039; 10 tốt lên, 2 xấu đi). ORACLE: 20 → 19, 20 → 20, 20 → 20, 18 → 19. `cyl22` 0/11, `mug24` 4/13 với CL0; ORACLE 13/13 và 11/11. `scene.toml` không đổi; a = -70 chưa áp dụng làm mặc định. Tiêu chí S0b CL0 dev_C0 L0 vẫn chưa đạt (10/20).

**Thị sai đã đo (`scripts/e9_parallax_probe.py`, `runs/e9_parallax_probe`).** Sai số phát hiện của bộ phát hiện thật, vật đơn, băng đứng yên, tăng dần từ tâm camera a = -280 và theo chiều cao vật: `cyl22` (cao 36,7 mm) 3–4,5 mm ở a = -280, 12–13 mm ở -70, 14–15 mm ở -40, 16–17 mm ở 0; `cyl26` (22,1 mm) 6 mm ở -40; `box25` (27,3 mm) 5 mm ở -40; `mug24` (34,4 mm) 7 mm ở -40. Sai số chủ yếu dọc băng. Xác nhận giả thuyết thị sai; ước tính 19 mm trước đó cao hơn số đo 14–15 mm. Chưa đo camera gần và chưa đo đường đi thực của lượt băng chạy.

**E10 thử hai núm không thuộc CL-0 gốc (`scripts/e10_knobs.sh`, 2/11 12:42–19:08, DEV, n = 20, CL0, 0/440 không hợp lệ, không lần nào watchdog phải khởi động lại).** So cặp theo từng sắp xếp với CL0 gốc (`runs/e8_real` cho C0, `runs/e9_clutter_real` lượt lặp 0 cho C1–C3, `runs/e10_base_L05` cho C2 L0.5, `runs/e9_static70` cho a = -70), kiểm định McNemar chính xác hai phía.

| Ô | gốc | `yaw_mode="local"` | `split="watershed"` |
|---|---|---|---|
| C0 L0 | 12 | 11 (p = 1) | 11 (p = 1) |
| C0 L0.25 | 17 | 14 (p = 0,25) | 16 (p = 1) |
| C1 L0 | 15 | 13 (p = 0,5) | 15 (p = 1) |
| C1 L0.25 | 14 | 15 (p = 1) | 15 (p = 1) |
| C2 L0 | 12 | 15 (p = 0,38) | 13 (p = 1) |
| C2 L0.25 | 16 | 16 (p = 1) | 17 (p = 1) |
| C2 L0.5 | 6 | 7 (p = 1) | 7 (p = 1) |
| C3 L0 | 2 | 1 (p = 1) | 4 (p = 0,5) |
| C3 L0.25 | 13 | 13 (p = 1) | 14 (p = 1) |
| Tổng /180 | 107 | 105 | 112 |
| a = -70: C2 L0 / C3 L0 | 15 / 10 | — | 15 / 11 |

Không núm nào cải thiện có ý nghĩa; đề xuất giữ CL-0 gốc (cả hai núm tắt), người dùng quyết. C2 L0.5 (75 mm/s, vượt giới hạn dải ≈ 71 mm/s của mặt bằng): CL0 gốc 6/20, ORACLE 16/20; lỗi CL0 gốc: va chạm 8, trượt 4, thời gian 2; ORACLE: va chạm 2, thời gian 2.

**E11 ACT trên demo sim (bắt đầu 2/11 19:25).** Lần chạy kiểm tra đường ống, **không** phải chính sách của hồ sơ: hành động theo khớp (mặc định LeRobot), kế hoạch §3.3 chốt hành động EE. Huấn luyện `runs/act_j0_s1000`: ACT mặc định LeRobot 0.6.1, 100 000 bước, batch 8, hạt giống 1000, 444 tập của `runs/e6_demos_real/lerobot`; đo tốc độ trên RTX 3070 Ti: 12,4 bước/s, 1,8 GB VRAM (`runs/act_smoke`, 300 bước). Đã cài `accelerate 1.15.0` (+ `psutil`) vào `~/venvs/lerobot_data` (LeRobot đòi khi huấn luyện; venv `cl0` không đổi). Cắm vào arena: `arena/methods/act_lerobot.py` qua `remote_server.py` (cách C). Chấm: `scripts/e11_act_eval.sh`, hai làn Isaac song song (lần đầu), làn B chạy trước ORACLE dev_C1 L0.25 n = 10 để kiểm chạy song song cho kết quả trùng `runs/e9_clutter_real`. Ô vật quen mới: `arrangements/sim_seen/seen_C0.csv`, `seen_C1.csv` (hạt giống 40, 41, n = 20, 0 trùng với sắp xếp demo; `scripts/e11_seen_sheets.py`).

**E11 kết quả (2/11 21:40 → 3/11 01:25, 0/250 không hợp lệ, không lần nào watchdog phải khởi động lại).** Huấn luyện: loss 13,9 → 0,038 sau 100 000 bước, 2 giờ 15 phút (`logs/2026-11-02_192528_act_j0_s1000.log`). Chạy song song hai làn: ORACLE dev_C1 L0.25 10/10 trùng `runs/e9_clutter_real` (success, outcome, t_end, t_success, vật) → chạy song song an toàn; mỗi lượt ACT ≈ 142 s thật (20 s mô phỏng + chuyển ảnh qua cầu nối). ACT so cặp với CL0 gốc và ORACLE (n = 20 mỗi ô):

| Ô | ACT | CL0 | ORACLE | ACT hơn / CL0 hơn | p |
|---|---|---|---|---|---|
| dev_C0 L0 | 15 | 12 | 20 | 6 / 3 | 0,51 |
| dev_C0 L0.25 | 19 | 17 | 20 | 3 / 1 | 0,63 |
| dev_C1 L0 | 14 | 15 | 20 | 4 / 5 | 1 |
| dev_C1 L0.25 | 14 | 14 | 20 | 3 / 3 | 1 |
| seen_C0 L0 | 16 | — | 18 | | |
| seen_C0 L0.25 | 15 | — | 18 | | |
| seen_C1 L0 | 14 | — | 18 | | |
| seen_C1 L0.25 | 10 | — | 18 | | |

Tương tự G1a (vật quen, C0/C1, L0.25): 25/40 = 62,5 %, dưới ngưỡng 70 %, trên mức 50 % (không phải lỗi kỹ thuật). Vật quen khó hơn vật lạ ở đây (ORACLE 72/80 so với 80/80): `l14` 1/4, `box04` 3/6, `ring20` 2/4 với ACT (trong demo `l14` chỉ 7/27 tập thành công). Nhãn lỗi của ACT kém tin: ACT không phát pha `CLOSE`, nên quy tắc `collision` (vật bị xô > 10 mm trước `CLOSE`) xét tới hết lượt; 40/43 thất bại mang nhãn `collision`. Hành động theo khớp, không phải chính sách của hồ sơ; số sim, không mang sang máy thật.

Lệnh huấn luyện E11 (để chạy lại trên máy khác): `env -u PYTHONPATH ~/venvs/lerobot_data/bin/python -m lerobot.scripts.lerobot_train --dataset.repo_id=local/e6_demos_real --dataset.root=runs/e6_demos_real/lerobot --policy.type=act --policy.device=cuda --policy.push_to_hub=false --output_dir=runs/act_j0_s1000 --job_name=act_j0_s1000 --steps=100000 --batch_size=8 --log_freq=500 --save_freq=20000 --wandb.enable=false --seed=1000`.

**Đưa lên git (3/11).** `cl0/`, `dir1/` và hai file kế hoạch không nằm trong repo nào; bản sao để trong `deps/` (`setup_workspace.py --collect`), hash đóng băng CL-0 của bản sao = bản gốc = `006af1c9686621e93249f7b2d17cf3e5cfd60ee96862213e13d000ddce63ab12`. `.gitattributes` tắt đổi CRLF. Không đưa lên: demo thô + bộ LeRobot E6 (một file video 136 MB > giới hạn 100 MB của GitHub), checkpoint ACT, `*_gt.npz` từ 1/11 (xem `.gitignore`).

**Video (3/11, chỉ để xem, không phải số đánh giá).** `runs/e12_video_{cl0,act}` (dev_C1_011 L0.25) và `runs/e13_video_c3_{cl0,act}` (dev_C3_001–004 L0.25, 4–5 vật sát nhau): CL0 3/4, ACT_J0 3/4. Video `.mp4` không vào git (`runs/**/videos/`).

**E14 ACT giao diện I2 (5/11, người dùng: "demo đi").** Chính sách của hồ sơ theo §3.2–3.3: hành động EE trong hệ băng, tương đối so với EE lúc chụp ảnh. Thành phần:
- `arena/i2.py`: vector 6 chiều `[x_b, y_b, z, cos 2yaw, sin 2yaw, kẹp]`, p_b = p_w − s(t)·u. Yaw mã hoá bằng (cos 2yaw, sin 2yaw) vì yaw là mod 180 (89° và −89° là hai góc gần nhau); góc chúc cố định `robot.tilt_deg`. Đầu vào của mạng: ảnh + vector này của EE đo được (không có góc khớp).
- Kiểm trước (`runs/e6_demos_real`, 23 tập, 6 048 khung): góc chúc của hành động demo nằm trong 1° quanh 90° ở 99,4 % khung; FK → IK ở góc chúc cố định sai ≤ 0,016 mm, nên đổi nhãn không mất thông tin.
- `to_lerobot_i2.py`: đổi 444 tập E6 sang `runs/e6_demos_real/lerobot_i2`; s(t) lấy từ GT `belt_s_gt` của lượt, nội suy theo thời điểm khung; thống kê hành động tính lại ở dạng tương đối (chunk 100) bằng `recompute_stats` của LeRobot.
- `train_act_i2.py`: `lerobot-train` nguyên bản, chỉ thay bộ tiền/hậu xử lý của ACT bằng thứ tự của pi0 (thô → `RelativeActionsProcessorStep` trên x_b, y_b, z → chuẩn hoá → mô hình → bỏ chuẩn hoá → `AbsoluteActionsProcessorStep`). Mô hình ACT không đổi. Hai bước này có sẵn trong LeRobot 0.6.1 nhưng chỉ nối cho pi0/pi05/groot.
- `arena/methods/act_i2.py`: mỗi lần lập kế hoạch dùng trạng thái đo ĐÚNG lúc chụp ảnh (như demo ghi) và s = `belt.s_at(t_chụp)`; mỗi tick 50 Hz lấy mục tiêu nội suy theo (t − t_chụp)·30 trong chunk, đổi về W bằng `belt.s_at(t)`, IK ở góc chúc cố định, giới hạn tốc độ khớp và z ≥ băng + `min_z_above_belt_mm` như `BeltExecutor`. Lập kế hoạch lại mỗi `n_action_steps` (100) khung như ACT_J0.
- Kiểm không cần học (`arena/methods/replay_i2.py`, `runs/e14_replay_i2`): phát lại hở nhãn I2 của 4 tập demo qua đúng bộ thực thi này, trên đúng ô/sắp xếp/tốc độ của lượt ORACLE gốc: 3/4 gắp thành công (C0 L0.25, C2 L0.25, C3 L0.25 năm vật). Tập hỏng (ep 240, C2 L0): quỹ đạo TCP và tư thế vật trùng lượt gốc trong ≈ 1 mm và 2° tới 2,7 s; lượt gốc vốn sát nút (má kẹp chạm `t17` khi hạ ở cả hai lượt), lượt phát lại kẹp kẹt trên vật khi khép. Đọc là độ nhạy vật lý, không phải lỗi nhãn `[suy luận]`.
- Chạy thử đường ống: checkpoint 300 bước trên 3 tập (thư mục tạm), 1 lượt qua `remote_server.py`: 2 lần lập kế hoạch, không lỗi.
- Chuỗi `scripts/e14_act_i2.sh` (bắt đầu 5/11 17:53): chờ đổi nhãn xong → huấn luyện `runs/act_i2_s1000` (cùng ngân sách ACT_J0: 100 000 bước, batch 8, hạt giống 1000) → hai làn Isaac: A = ACT_I2 dev_C0, dev_C1 × L0, L0.25 (so cặp với ACT_J0, CL0, ORACLE); B = ACT_I2 dev_C2 × L0, L0.25, L0.5 rồi ACT_J0 dev_C2 L0.5. L0.5 nằm ngoài tốc độ của demo (chỉ có L0 và L0.25).

**E14 kết quả (5/11 18:35 → 6/11 00:25, 0/140 không hợp lệ, không lần nào watchdog phải khởi động lại).** Đổi nhãn 444 tập (115 908 khung, s cuối tập tới 351 mm): 18:35. Huấn luyện `runs/act_i2_s1000`: loss 4,44 (bước 500) → 0,053 (100 000), 2 giờ 27 phút (`logs/*_e14_train_act_i2.log`); loss không so được với ACT_J0 (khác không gian hành động và chuẩn hoá). Mỗi lượt ≈ 144 s thật. So cặp theo sắp xếp, McNemar chính xác hai phía, n = 20 mỗi ô (CL0/ORACLE: `runs/e8_real`, `runs/e9_clutter_real` lượt lặp 0, `runs/e10_base_L05`; ACT_J0: `runs/e11_act_dev`, `runs/e14_act_j0_dev2`):

| Ô | ACT_I2 | ACT_J0 | CL0 | ORACLE | I2 vs J0 (hơn/kém, p) | I2 vs CL0 (hơn/kém, p) |
|---|---|---|---|---|---|---|
| dev_C0 L0 | 11 | 15 | 12 | 20 | 2/6, 0,29 | 3/4, 1 |
| dev_C0 L0.25 | 19 | 19 | 17 | 20 | 1/1, 1 | 3/1, 0,63 |
| dev_C1 L0 | 9 | 14 | 15 | 20 | 2/7, 0,18 | 1/7, 0,070 |
| dev_C1 L0.25 | 11 | 14 | 14 | 20 | 4/7, 0,55 | 3/6, 0,51 |
| dev_C2 L0 | 11 | — | 12 | 20 | | 5/6, 1 |
| dev_C2 L0.25 | 16 | — | 16 | 18 | | 3/3, 1 |
| **dev_C2 L0.5** | **13** | **4** | **6** | 16 | **11/2, 0,022** | 10/3, 0,092 |

- Ở L0.5 (75 mm/s, ngoài tốc độ của demo: demo chỉ có L0 và L0.25), I2 hơn J0 có ý nghĩa (13 so với 4, p = 0,022) và gần ORACLE (16); hơn CL0 (13 so với 6, p = 0,092, chưa có ý nghĩa). Đúng hướng H4 (giao diện hệ băng chịu băng nhanh) nhưng chưa phải phép thử H4: J0 khác I2 cả giao diện lẫn không gian hành động (khớp so với EE), và L = 0,5 chứ không phải 1,0.
- Ở L0, I2 kém J0 và CL0 (C0 + C1: 20/40 so với 29/40 và 27/40), chưa có ý nghĩa từng ô. Nguyên nhân chưa rõ `[chưa kiểm]`; giả thuyết: mạng không thấy góc khớp, mã hoá yaw, lập kế hoạch lại chỉ mỗi 3,3 s.
- Lỗi của I2: `collision` 39, `other` 11 (nhãn `collision` của ACT kém tin như E11).
- IK hỏng ở mọi lượt (`diag.ik_fail_ticks`), nhưng chạy lại 4 lượt với chẩn đoán (`runs/e14_diag_c0`, `runs/e14_diag_c1`): 0 tick hỏng trong 6 s đầu, lần hỏng đầu ở 9,2–10 s, gần tư thế nhà, IK có nghiệm nhưng bị biên an toàn của `wrist_flex` (92,4°) từ chối. Không phải nguyên nhân thất bại. Trong lần chạy lại, `dev_C0_004` thành công (lần chính: thất bại): kết quả ACT có dao động giữa các lần chạy `[chưa đo mức dao động]`.
- Số sim (`engine=isaac`), một hạt giống huấn luyện; không mang sang máy thật.

**E15 băng nhanh × nhiều vật (6/11, người dùng: "tiếp tục củng cố ở tốc độ cao và có nhiều vật").** Chỉ ô DEV; ô TEST không chạy. `scripts/e15_fast_clutter.sh` (bắt đầu 6/11 17:26):
1. Hai làn Isaac. A: demo ORACLE ở L0.5 trên train_C2, train_C3 (60 sắp xếp mỗi ô, giữ lượt thành công, `runs/e15_demos_fast`), rồi đổi nhãn toàn bộ demo (E6 + mới) chạy nền; CL0 + ORACLE dev_C3 L0.5 (`runs/e15_base_c3_l05`, ô còn thiếu); ACT_I2 lập kế hoạch lại mỗi 100 khung trên dev_C3 L0.25, L0.5 (`runs/e15_i2_r100`). B: ACT_I2 lập kế hoạch lại mỗi 10 khung (`ACT_REPLAN=10`) trên dev_C2, dev_C3 × L0.25, L0.5 (`runs/e15_i2_r10`).
2. Huấn luyện `runs/act_i2f_s1000` trên toàn bộ demo, cùng ngân sách với `act_i2_s1000` (100 000 bước, batch 8, hạt giống 1000): chỉ khác dữ liệu.
3. Quy tắc chọn trước khi xem pha 3: lập kế hoạch lại mỗi 10 khung nếu tổng thành công của nó ≥ của mỗi 100 khung trên dev_C2 L0.5, dev_C3 L0.25, dev_C3 L0.5; ngược lại 100. Rồi chính sách mới trên dev_C2, dev_C3 × L0.25, L0.5 (`runs/e15_i2f`, `runs/e15_i2f_c3`).
Lưu ý: demo ORACLE ở L0.5 chỉ có trong sim; trên máy thật, thu demo bằng tay leader ở 75 mm/s khó (§3.2), nên phần cải thiện nhờ dữ liệu nhanh không mang sang cách thu dữ liệu thật; phần nhờ lập kế hoạch lại thì mang sang được.

**E15 pha 1 (6/11 17:26 → 21:42, 0/280 không hợp lệ, không lần nào watchdog phải khởi động lại).** Demo ORACLE ở L0.5: train_C2 41/60, train_C3 35/60 → 76 tập mới (`runs/e15_demos_fast/episodes`); đổi nhãn toàn bộ 444 + 76 = 520 tập vào `runs/e15_demos_fast/lerobot_i2_all`. So cặp (n = 20, McNemar chính xác; CL0/ORACLE: `runs/e9_clutter_real` lượt lặp 0, `runs/e10_base_L05`, `runs/e15_base_c3_l05`; ACT_I2 lập kế hoạch lại mỗi 100 khung: `runs/e14_act_i2_dev2`, `runs/e15_i2_r100`; mỗi 10 khung: `runs/e15_i2_r10`):

| Ô | ACT_I2 /100 khung | ACT_I2 /10 khung | CL0 | ORACLE | /10 vs /100 (hơn/kém, p) | /100 vs CL0 (hơn/kém, p) |
|---|---|---|---|---|---|---|
| dev_C2 L0.25 | 16 | 14 | 16 | 18 | 0/2, 0,50 | 3/3, 1 |
| dev_C2 L0.5 | 13 | 6 | 6 | 16 | 4/11, 0,12 | 10/3, 0,092 |
| dev_C3 L0.25 | 10 | 16 | 13 | 14 | 7/1, 0,070 | 5/8, 0,58 |
| dev_C3 L0.5 | 9 | 3 | 8 | 13 | 1/7, 0,070 | 6/5, 1 |

Lập kế hoạch lại mỗi 10 khung giúp ở C3 L0.25 (16 so với 10) nhưng hại ở L0.5 (C2 6 so với 13, C3 3 so với 9); chưa ô nào có ý nghĩa. Nguyên nhân ở L0.5 chưa rõ `[chưa kiểm]`. Theo quy tắc ghi trước: tổng ba ô /10 = 25 < /100 = 32 → chính sách mới dùng 100 khung. dev_C3 L0.5 (75 mm/s, 4–5 vật sát nhau) là ô khó nhất đến giờ: ORACLE chỉ 13/20.

**E15 pha 2–3 (6/11 21:42 → 7/11 01:40, 0/80 không hợp lệ).** Huấn luyện `runs/act_i2f_s1000` trên 520 tập (135 660 khung; 444 E6 + 76 L0.5): loss 0,054 ở 100 000 bước (5,9 epoch), 2 giờ 14 phút (`logs/*_e15_train_act_i2f.log`). Đánh giá với lập kế hoạch lại 100 khung (theo quy tắc). So cặp n = 20 (ACT_I2 cũ = 100 khung, `runs/e14_act_i2_dev2` + `runs/e15_i2_r100`):

| Ô | ACT_I2F (thêm demo L0.5) | ACT_I2 cũ | CL0 | ORACLE | mới vs cũ (hơn/kém, p) | mới vs CL0 (hơn/kém, p) |
|---|---|---|---|---|---|---|
| dev_C2 L0.25 | 16 | 16 | 16 | 18 | 2/2, 1 | 2/2, 1 |
| dev_C2 L0.5 | 14 | 13 | 6 | 16 | 4/3, 1 | **9/1, 0,021** |
| dev_C3 L0.25 | 12 | 10 | 13 | 14 | 4/2, 0,69 | 5/6, 1 |
| dev_C3 L0.5 | 8 | 9 | 8 | 13 | 3/4, 1 | 5/5, 1 |
| Tổng /80 | 50 | 48 | 43 | 61 | 13/11, 0,84 | 21/14, 0,31 |

- Thêm 76 demo L0.5 không đổi kết quả (50 so với 48). Lợi thế ở L0.5 đến từ giao diện I2, không cần demo nhanh; khớp với ý H4b (demo chậm dùng được cho băng nhanh) nhưng chưa phải phép thử H4b.
- dev_C2 L0.5: ACT_I2F 14 so với CL0 6 (p = 0,021, một ô trong nhiều phép so; chưa hiệu chỉnh đa so sánh).
- dev_C3 L0.5 là nút thắt của mọi phương pháp: ORACLE 13/20 (thất bại: `collision` 5, `slip` 1, `timing` 1), CL0 8 (`collision` 7, `grasp_point` 3), ACT_I2F 8 (`collision` 11, nhãn ACT kém tin). Với 4–5 vật cách 0–3 mm ở 75 mm/s, ngay cả nhận thức hoàn hảo cũng va vào vật bên cạnh trong 7/20 lượt `[suy luận: giới hạn hình học của kẹp/ thời gian, chưa kiểm]`.

**E16 vì sao ACT_I2 hỏng (8/11, người dùng: "làm sao để cải thiện model").** Phân tích chỉ từ GT của các lượt đã chạy (`scripts/e16_failure_modes.py`, kết quả `logs/2026-11-08_*_e16_failure_modes_before.txt`), không chạy Isaac. Chế độ lỗi do mình định nghĩa từ GT (ACT không phát pha CLOSE nên nhãn `fail_cause_auto` của nó vô nghĩa): lần đóng kẹp đầu = độ mở đo được < 30 (mở = 40).
- **Bằng chứng 1, lỗi chính là đóng kẹp vào chỗ trống.** ACT_I2 lập kế hoạch lại mỗi 100 khung (`/100`), 62 lượt hỏng trên sáu ô dev: 37 đóng kẹp hẳn (< 3) mà không có vật (60 %), 16 "nhấc một phần" (26 %), 8 nhấc ≥ 25 mm nhưng không giữ đủ 2 s (13 %), 1 kẹt không nhấc, 0 lượt không đóng kẹp. 29/62 lượt có vật bị xô > 10 mm trước lần đóng đầu. "Nhấc một phần" đếm bất kỳ vật nào, bất kỳ lần thử nào trong 20 s (ACT thử lại nhiều lần: ≥ 4 lần đóng ở 92/180 lượt), nên không đồng nghĩa với "gắp đúng vật rồi tuột".
- **Bằng chứng 2, lệch ngang cố định ≈ −9 mm.** Độ lệch của TCP so với tâm vật gần nhất lúc đóng kẹp đầu, theo hướng ngang băng (db), trung vị: `/100` −9,2 mm (lượt thành công −7,9, thất bại −15,1; độ lệch chuẩn 13,6); CL0 +2,3 (6,9); ORACLE +0,1 (6,1); ACT_J0 +0,7 (12,8). **Cùng mô hình, lập kế hoạch lại mỗi 10 khung (`/10`): +0,6 (7,8)**: lệch biến mất và độ phân tán giảm một nửa. Độ lệch không tỉ lệ với vị trí ngang của vật (hệ số 0,05) hay chiều cao vật (0,15 mm/mm) nên không phải co về trung bình hay thị sai. Thêm 76 demo L0.5 (I2F) không đổi (−7,2).
- **Bằng chứng 3, `/10` hỏng theo cách khác: nhấc quá sớm.** Từ lúc đóng đến lúc tay nhấc lên 15 mm: ORACLE 0,72 s (thành công), `/100` 0,80 s, nhưng `/10` ở lượt thất bại chỉ **0,20 s** (trung vị). Hai lượt `/10` dev_C3_001 và 002 L0.5: kẹp đo 34 → 0 trong khi z tăng 10 → 48 mm trong 0,4 s. Tỉ lệ "kẹp rỗng lúc nhấc": `/100` 45 % lượt hỏng, ACT_J0 59 %, `/10` 18 %.
- **Suy ra, chưa kiểm:** (a) độ lệch ngang đến từ kế hoạch đầu của mô hình, không phải bộ thực thi: phát lại nhãn demo qua cùng bộ thực thi cho TCP trùng lượt gốc ≈ 1 mm lúc đóng kẹp (`runs/e14_replay_i2`), và `/10` dùng cùng bộ thực thi mà không lệch; (b) `/10` nhấc sớm vì mỗi lần lập kế hoạch lại thấy kẹp đo ở trạng thái đang khép, khác phân bố demo với vật dev có bề rộng khác `[chưa kiểm]`.
- **Kế hoạch E16 (chưa huấn luyện lại, `scripts/e16_commit.sh`):** "COMMIT" = lập kế hoạch lại mỗi 10 khung khi lệnh kẹp của chính sách còn MỞ; khi nó ra lệnh ĐÓNG thì chạy hết đoạn đó (100 khung). Ô dev, n = 20: làn A dev_C2, dev_C3 × L0.25, L0.5; làn B dev_C0, dev_C1 × L0 (nơi `/100` kém ACT_J0 và CL0: 20/40 so với 29/40 và 27/40), rồi **chạy lại `/100` trên dev_C2 L0.5** để đo độ dao động giữa các lần chạy của ACT (một lượt dev_C0_004 đã đổi kết quả khi chạy lại ở E14; chưa có số). **Quy tắc chọn, ghi trước lượt đầu:** COMMIT thành chế độ suy luận mặc định của ACT-I2 khi và chỉ khi tổng thành công trên bốn ô dev_C2/dev_C3 × L0.25, L0.5 ≥ `/100` + 5 (48 + 5 = 53/80) **và** ≥ `/10` (39); không thì giữ `/100`. `scripts/e16_pair.py` chấm quy tắc. COMMIT là quy tắc đặt lên trên chính sách (dựa vào lệnh kẹp của chính sách), nên báo cáo là biến thể "ACT-I2 + commit", không phải ACT thuần. Cải thiện ở phía suy luận nên mang sang được robot thật, khác với demo L0.5 chỉ ghi được trong sim.

**E16 sự cố 8/11 15:17 (không phải lỗi mô phỏng, không có lượt `valid=0`).** Isaac của làn B (`runs/e16_commit_c01`) hết bộ nhớ GPU khi cấp phát ảnh (`Out of GPU memory allocating 'Synthetic Image Data Color (LDR)'`, `VK_ERROR_OUT_OF_DEVICE_MEMORY`), lỗi phân đoạn, mã thoát 139, sau 20/40 lượt (`logs/2026-11-08_143008_e16_commit_c01.log`; Ubuntu cũng báo `/var/crash/_usr_bin_python3.12.1000.crash`). Lúc đó trên GPU 8 GB có thêm Xorg, gnome-shell, Steam và các cửa sổ bạn mở sau khi cài lại VS Code (≈ 0,8 GB). Hậu quả dây chuyền: máy chủ ACT của làn đó thoát vì `EOFError` khi Isaac sập giữa lượt, nên lần thử lại 15:19:39 bị từ chối kết nối nhưng `run_arena` vẫn trả mã 0, bộ canh tưởng đã xong và chuyển sang bước sau; hai ô dev_C1 L0 thiếu. Sửa: `remote_server.py` giờ phục vụ tiếp khi `--repeat` và arena ngắt đột ngột; `scripts/e16_resume_c01.sh` (đơn vị systemd `arena-e16b`) chạy 20 lượt thiếu cùng cấu hình, đếm đủ 40 mới dừng. Khi cài lại VS Code cũng đã chuyển chuỗi sang đơn vị systemd `arena-e16` (14:28): mất 2 lượt dở, các lượt xong được giữ. Bài học: khi chạy hai làn Isaac, đừng mở thêm ứng dụng dùng GPU (trình duyệt, game, Steam).

## E16 kết quả (8/11, engine=isaac, 140 lượt, 0 lượt không hợp lệ)
Bằng chứng: `logs/2026-11-08_175431_e16_pair_final.txt`, `logs/2026-11-08_175431_e16_failure_modes_after_final.txt`; `runs/e16_commit_c23` (80), `runs/e16_commit_c01` (40/40 sau khi chạy bù), `runs/e16_repeat_r100` (20).
- Quy tắc đăng ký trước: COMMIT cần ≥53/80 và ≥39 trên C2/C3 × L0.25/L0.5. Kết quả COMMIT 41/80 (/100 = 48, /10 = 39, CL0 = 43, ORACLE = 61); COMMIT vs /100 hơn/kém 16/23, p=0.337. → **KHÔNG nhận COMMIT, giữ /100 làm mặc định.**
- L0 (C0+C1, n=40): COMMIT 22, /100 20, J0 29, CL0 27 (không khác biệt có ý nghĩa).
- Sàn nhiễu: lặp /100 trên dev_C2 L0.5 (tiến trình máy chủ mới): 13 → 14, 3/20 lượt đổi kết quả. Nghĩa là chênh ±3 giữa hai lần chạy trên một ô n=20 chưa phân biệt được với nhiễu.
- Cơ chế (chỉ GT): COMMIT sửa lệch ngang (db trung vị −9.2 → +1.8 mm, sd 13.6 → 9.3) nhưng lệch dọc băng mới xuất hiện (da trung vị −6.6 mm), thời gian giữ trước khi nhấc giảm (fail 0.80 → 0.42 s), và `partial_lift` tăng rõ ở C3 L0.5 (2 → 11). Giả thuyết [chưa kiểm]: chunk cam kết sau khi ra lệnh đóng đi theo lệch pha với băng đang chạy nhanh.
- Kết luận cho luận văn: cải thiện chỉ từ phía suy luận không đủ; cần thay đổi ở mô hình (dữ liệu/huấn luyện) nếu muốn vượt /100.
