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
