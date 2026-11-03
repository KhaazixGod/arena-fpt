# KẾ HOẠCH ĐẤU TRƯỜNG (ARENA): Isaac Sim để chạy và so sánh các phương pháp

Cập nhật 28/10/2026 · bản nháp để bạn chỉnh · dành cho Claude Code trên máy bạn · gắn với `KE_HOACH_HUONG_1.md` §3.6 · **chưa có dòng mã Isaac nào được viết hay chạy**

Chú thích: `[đã kiểm]` = mình đã đọc mã/trang nguồn · `[chưa kiểm]` = chưa đọc/đo · `[đề xuất]` = số/ngưỡng mình đặt, bạn duyệt trước khi dùng · `[ước lượng]` = mình đoán.

---

## 0. Mục tiêu và ranh giới

**Mục tiêu:** một môi trường Isaac Sim (tay SO-101 từ mô hình USD của bạn, băng chuyền, camera cố định, vật và clutter) mà ở đó **mọi phương pháp chạy qua cùng một giao diện** và **trả về metrics** theo cùng định dạng với `dir1/g0_analyze.py`. Phương pháp đầu tiên là CL-0; sau đó cắm được CL-KF, ACT, DP, MIP khi chúng được viết.

**Không làm trong kế hoạch này:**
- Không chạm robot thật, băng thật hay camera thật.
- Không chạy ô TEST của sim, không tuyên bố "số sim = số thật". Số sim luôn gắn nhãn `engine=isaac`.
- Không viết CL-KF, chính sách học hay bộ chuyển nhãn I2; chỉ chừa chỗ cắm và test hợp đồng (§5, giai đoạn E7).
- Không sửa `cl0/*.py` nếu chưa hỏi bạn (lý do ở §3, mục 2).

**Xong cả kế hoạch khi:** `python -m arena.run_arena --methods CL0,NOOP,ORACLE --cells dev_C0,dev_C2 ...` chạy trọn, ra `trials.csv` + `metrics_report.md` đúng §6, và các cổng S0 (§7) đạt hoặc báo rõ vì sao chưa.

---

## 1. Việc bạn cần điền trước (ô trống không chặn giai đoạn không liên quan)

| # | Cần | Dùng cho | Điền |
|---|---|---|---|
| 1 | Đường dẫn Isaac Sim đã cài, phiên bản; có Isaac Lab không | E0 | |
| 2 | Đường dẫn file USD SO-101 của bạn; tên prim gốc robot | E1 | |
| 3 | Tên khớp trong USD ↔ tên LeRobot (`shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper`); khớp kẹp là khớp nào; "0°" trong USD ở đâu | E1 | |
| 4 | Băng: bề rộng, chiều dài (mm), tốc độ cần quét (mm/s), mm/xung thật (nếu đã đo) | E1 | |
| 5 | Camera: vị trí/hướng dự kiến (ngoại tham số), độ phân giải/fps/độ trễ thật nếu đã đo; chưa đo thì dùng giá trị trong `cl0.toml` | E1, E2 | |
| 6 | Độ mở kẹp hữu dụng w (mm); tải tối đa | E5 | |
| 7 | Chấp nhận các ngưỡng `[đề xuất]` ở §6 và §7, hoặc sửa | E1, E3, E4 | |

---

## 2. Kiến trúc

```
arena/run_arena.py ──► IsaacPlatform (cài cl0.runner.Platform) ──► Isaac Sim (lockstep)
      │                   ├─ camera ảo: khung bị trễ = camera.latency_s
      │                   ├─ băng: BeltLike (s_at, speed_at) + bộ đếm xung ảo
      │                   └─ tay: state()/send(), PD trong USD
      ├─ Method (bộ điều khiển) ◄─ CL0 | CL-KF | Policy | ORACLE | NOOP
      └─ metrics: trials.csv + trial_*.json + metrics_report.md + manifest.json
```

**Hợp đồng đã kiểm trong mã** `[đã kiểm]`:
- `cl0/runner.py` định nghĩa `Platform` (Protocol): `belt: BeltLike`, `now()`, `poll_frame() -> Optional[Frame]`, `robot_state() -> RobotState`, `send(cmd: Command)`, `wait_tick() -> float`, `start_belt(v_mm_s)`, `stop_belt()`. `BeltLike`: `s_at(t)`, `speed_at(t)`. Kiểu dữ liệu ở `cl0/types.py`: `Frame(img BGR uint8, t_capture)`, `RobotState(q_deg[5], gripper 0–100, t)`, `Command(q_deg|None, gripper|None, phase, note)`.
- `run_controller(ctrl, platform, t_limit_s)` chỉ cần ở bộ điều khiển: `reset(t, state)`, `step(t, frame, belt, state) -> Command`, `finished`, `outcome`, `events`, `log`, `diag`. **Đó chính là hợp đồng phương pháp**: ai cài đủ các thành phần này thì cắm được.
- `cl0/sim/platform.py` (`SimPlatform`) là bản động học của đúng giao diện này (thời gian ảo, camera trễ, tick cố định); `IsaacPlatform` làm tương tự nhưng thế giới là Isaac. `cl0/sim/harness.py::run_trial` cho thấy trình tự: tạo thế giới → `start_belt` → `run_controller` → đọc kết quả.
- Tờ sắp xếp: `cl0.arrangements.read_arrangements` (`arrangement_id, first_method, idx, object, x_mm, y_mm, yaw_deg`; `x_mm` dọc băng, `y_mm` từ mép trái nhìn theo chiều băng).
- CSV kết quả: `cl0/run_g0.py::CSV_COLUMNS` và `dir1/g0_analyze.py` (đọc theo tên cột, bỏ qua cột thừa). `cl0.run_g0.suggest_cause(outcome, grasp_reason)` đã ánh xạ outcome → nguyên nhân thất bại.
- FK: `cl0/kinematics.py::SO101Kinematics` dựa URDF chính thức `so101_new_calib.urdf`, góc khớp theo LeRobot `use_degrees=True` (0° = giữa tầm chuyển động đã hiệu chuẩn). USD của bạn phải khớp quy ước này, nếu không FK, IK và mọi hiệu chuẩn lệch theo.

**Tiến trình:** LeRobot 0.6.1 cần Python ≥ 3.12 `[đã kiểm]`; Python của Isaac Sim bản bạn cài `[chưa kiểm]`. Nếu lệch, Isaac chạy ở tiến trình riêng, client nối bằng socket hoặc bộ nhớ chung, vẫn **lockstep** (client gửi lệnh và số bước → Isaac chạy đúng số bước vật lý → trả khung, trạng thái, bộ đếm). Quyết định ở E0, ghi `ARENA_SETUP_REPORT.md`.

**Chặn rò rỉ thông tin:** phương pháp chỉ nhận `Frame`, `RobotState`, `BeltLike`. Ground truth (pose vật, mask thật) chỉ có trong `labeler` và `ORACLE`. `IsaacPlatform` không đưa đối tượng world cho bộ điều khiển; có test kiểm.

---

## 3. Luật cho Claude Code (chép vào `arena/CLAUDE.md`; có hiệu lực cùng `cl0/CLAUDE.md`)

1. **An toàn.** Kế hoạch này chỉ chạy mô phỏng. Không mở `LeRobotArm`, `Belt` thật hay camera thật. Isaac chạy không giao diện (headless) trừ khi bạn nhờ xem. Không `sudo`; việc cần quyền thì đưa lệnh cho bạn. Không chạy Isaac song song với huấn luyện (tranh VRAM 8 GB).
2. **Vị trí mã.** Mã đấu trường nằm ở `arena/`, **ngoài** `cl0/`. Lý do: `cl0.system.code_sha256()` băm mọi `*.py` trong `cl0/` trừ `sim/` và `tests/` `[đã kiểm]`; thêm hay sửa file trong `cl0/` làm vỡ dấu đóng băng. Cần sửa `cl0/*.py` (ví dụ chỗ nào gọi `time` thay vì đồng hồ chèn vào): **dừng và hỏi bạn**, ghi `CODE_CHANGES.md`, chạy lại `pytest -m "not slow"` (204) và `run_g0 --sim`, và việc đó phải xong **trước** khi bạn đóng băng CL-0.
3. **Cấu hình riêng.** `arena/configs/arena.toml` (bản sao từ `cl0.toml`, chú thích lý do mỗi khác biệt). Không sửa `cl0.toml` của máy thật.
4. **Tinh chỉnh CL-0 trong sim** `[đề xuất]`: chỉ trên vật DEV và sắp xếp DEV của sim, tối đa 16 giờ làm việc (bạn báo giờ), mỗi lần một thông số, ghi `ARENA_TUNING_LOG.md` (ngày, thông số, cũ → mới, lý do, bằng chứng, giờ đã dùng). Đổi logic nhận thức/chọn vật/điều khiển của CL-0 là đổi thuật toán: **hỏi bạn trước**. Tham số tinh chỉnh trong sim **không** mang sang robot thật.
5. **Ô TEST của sim:** sinh sẵn, để trong `arena/locked/`, **không chạy** khi bạn chưa ra lệnh.
6. **Trung thực.** Không nói "chạy được / xong" khi chưa có log, ảnh hay con số kèm đường dẫn. Điều chưa kiểm ghi `[chưa kiểm]`. Không sửa tay CSV/JSON kết quả, không xoá lượt hay log. Mọi số sim ghi `engine=isaac`; không trộn với số thật.
7. **Lượt không hợp lệ** (`valid=0`) **chỉ** vì lỗi mô phỏng (Isaac sập, NaN vật lý, vật xuyên băng, mất đồng bộ lockstep). Thất bại của phương pháp luôn được tính. Tỉ lệ `valid=0` > 10% thì dừng và sửa.
8. **Dừng và hỏi bạn khi:** FK của USD lệch ngưỡng; cần tải dữ liệu lớn hoặc giấy phép chưa rõ (mesh vật); phải đổi thuật toán baseline; VRAM không đủ; số ngoài ngưỡng ở §7.
9. **Báo cáo bằng tiếng Việt, ngắn:** kết luận trước, rồi bảng metrics (§6.3) kèm đường dẫn bằng chứng, rồi việc bạn cần làm.

---

## 4. Giai đoạn

Thời gian là `[ước lượng]`, Claude Code báo số thực tế sau mỗi giai đoạn.

### E0. Môi trường và khả thi (≈ nửa ngày)
- Đọc `cl0/CLAUDE.md`, `cl0/README_CL0.md`, `KE_HOACH_HUONG_1.md` §3.4–§3.6, §4.2–§4.3 và tài liệu này.
- Ghi phiên bản Isaac Sim, Python của nó, GPU/VRAM trống, các extension có sẵn (băng chuyền, cầu nối ROS 2, Replicator). Chạy một script không giao diện: cảnh trống, một camera 640×480 (hoặc cỡ trong `cl0.toml`), render một khung, đo ms/bước vật lý và ms/khung render.
- Quyết định tiến trình (cùng Python hay tách).
- **Xong khi:** `ARENA_SETUP_REPORT.md` có: phiên bản, Python, VRAM, ms/bước, ms/khung, quyết định tiến trình, và một ảnh render mở xem được.

### E1. Cảnh tối thiểu (≈ 1–2 ngày)
- Nhập USD SO-101, ánh xạ tên khớp, cài PD sao cho tay bám lệnh góc. Dựng băng (vận tốc bề mặt PhysX hoặc tiện ích băng chuyền của Isaac `[chưa kiểm trên bản bạn cài]`), một vật, camera cố định.
- **Kiểm FK:** 20 cấu hình khớp ngẫu nhiên trong giới hạn → vị trí/hướng TCP trong Isaac so với `SO101Kinematics`. **Ngưỡng `[đề xuất]`: lệch ≤ 2 mm và ≤ 1°.** Lệch lớn: dừng, báo (nghi dấu hoặc "0°" của USD khác LeRobot).
- **Kiểm băng:** đặt vật, chạy các tốc độ (tính từ L = 0,25 / 0,5 / 1,0 theo §3.1 của kế hoạch chính), đo vận tốc vật bằng GT và bằng ảnh.
- **Xong khi:** (a) FK trong ngưỡng hoặc nguyên nhân lệch đã giải thích và bạn duyệt; (b) vận tốc vật lệch ≤ 3% so với lệnh `[đề xuất]`; (c) ảnh camera mở xem được, băng trọn khung; (d) báo tốc độ: giây thật mỗi giây mô phỏng.

### E2. `IsaacPlatform` và chạy CL-0 (≈ 2–4 ngày)
- Cài `Platform` (§2): lockstep; trễ camera đúng `camera.latency_s` (CL-0 gán `t_capture = lúc nhận − giá trị đã cấu hình`); bộ đếm xung ảo (mm/xung, lượng tử hoá, nhiễu tuỳ chọn); `wait_tick` ứng với số nguyên bước vật lý; reset giữa lượt (tay về home, xoá vật, đặt vật theo tờ sắp xếp, chờ ổn định rồi chạy băng).
- **Hiệu chuẩn cho sim:** các lệnh `cl0.calibrate` là cho phần cứng nên không dùng. Viết `arena/calib_from_scene.py` sinh `calib.json` (camera → mặt băng, hướng băng trong hệ robot, mm/xung, độ trễ) và `background.npz` (băng trống) từ chính cảnh, theo định dạng CL-0 đọc `[chưa kiểm: đọc cl0/calib_tools.py và cl0/system.py để biết định dạng]`. Lưu ý: hiệu chuẩn từ GT là **hoàn hảo**, mạnh hơn thật; thêm tuỳ chọn nhiễu hiệu chuẩn, mặc định TẮT, chốt giá trị ở E8 từ sai số đo thật.
- **Xong khi:** CL-0 chạy ≥ 20 lượt `dev_C0` (băng đứng yên) và ≥ 20 lượt băng chậm không sập; log từng lượt; xem 3 video (một thành công, hai thất bại) và mô tả bằng lời; ghi SR kèm số lượt.

### E3. Runner, metrics, nhãn lỗi tự động (≈ 1–2 ngày)
- `arena/run_arena.py`: chọn phương pháp, ô, tốc độ, hạt giống, tờ sắp xếp; mỗi lượt ghi một dòng CSV + `trial_XXXX.json` + `trial_XXXX_log.csv`; `manifest.json` (phiên bản Isaac, hash `arena/`, `cl0` (`code_sha256`), cấu hình, USD, hạt giống, ngày).
- `arena/labeler.py`: nhãn thành công từ GT và nguyên nhân thất bại tự động trong danh sách đóng (`merge, seg_miss, grasp_point, timing, calib, slip, collision, other`). Quy tắc gán **viết trước** vào file, dựa trên `suggest_cause` cộng GT (ví dụ `merge` = một vùng phát hiện phủ ≥ 2 vật thật; `seg_miss` = vật mục tiêu không có phát hiện nào phủ; `grasp_point` = lệch tâm vật lúc má chạm vượt ngưỡng `[đề xuất]`). Xem tay 30 lượt thất bại, báo tỉ lệ đồng ý.
- `arena/report.py`: tính §6 (gọi hàm trong `g0_analyze.py` cho Wilson, McNemar, bootstrap; **không viết lại** công thức thống kê).
- Test: `pytest arena/tests` gồm: metrics khớp `g0_analyze` trên dữ liệu giả; hợp đồng phương pháp; chặn rò rỉ GT; đọc/ghi CSV.
- **Xong khi:** test xanh; `report` ra bảng từ CSV thật của E2; **kiểm độ lặp lại**: chạy 30 lượt hai lần cùng hạt giống và cấu hình, báo số lượt kết quả khác nhau (nếu có, nguồn nhiễu là gì `[chưa kiểm: tái lập của PhysX]`).

### E4. Chặn dưới và chặn trên: `NOOP` và `ORACLE` (≈ nửa ngày)
- `NOOP`: không làm gì (kiểm không có "nhặt nhầm" do vật rơi hay va).
- `ORACLE`: dùng pose thật của vật, đi qua **cùng** bộ thực thi hệ băng (`BeltExecutor`). Đây là trần mà môi trường cho phép.
- **Xong khi:** bảng `NOOP`/`ORACLE` theo L và mức clutter. **`[đề xuất]`:** `NOOP` ≈ 0%; `ORACLE` ≥ 95% ở C0, L = 0,25. `ORACLE` thấp hơn thì lỗi nằm ở vật lý/kẹp/thời gian của môi trường, **điều tra trước khi so bất kỳ phương pháp nào**.

### E5. Vật, clutter, sắp xếp (≈ 3–5 ngày)
- Bể mesh công khai (ví dụ YCB, Google Scanned Objects; giấy phép, định dạng, cỡ vừa kẹp `[chưa kiểm]`: **hỏi bạn trước khi tải**). Lọc theo w; xấp xỉ va chạm lồi; khối lượng và ma sát mặc định có chú thích.
- Chia train/dev/test của sim với hạt giống cố định, tách rời nhau; test gồm ba dạng khó (lõm/quai, mỏng/dẹt, tương phản thấp với mặt băng; kế hoạch §3.5). Ghi `objects_sim.csv` (`name,diameter_mm,split,hard_type`) và ảnh tổng hợp.
- Sinh sắp xếp C0–C3 bằng `dir1/make_arrangements.py` (cùng ràng buộc mm, chỉnh theo bề rộng băng và w của sim). DEV chạy được; TEST vào `arena/locked/`.
- **Xong khi:** bảng vật + ảnh; 0 vi phạm ràng buộc trên các sắp xếp sinh; **kiểm ổn định C3** (vật chạm nhau không trôi quá 2 mm sau 1 s ở băng đứng yên `[đề xuất]`, báo tỉ lệ sắp xếp đạt).

### E6. Chuyên gia và ghi demo (≈ 2–3 ngày)
- Chuyên gia = `ORACLE`. Ghi từng tập: ảnh camera, góc khớp, hành động, s(t), thời gian, theo §4.2 của kế hoạch chính. Chuyển sang định dạng LeRobot dataset với tên đặc trưng **giống bộ ghi `lerobot-record` thật** để dùng chung script huấn luyện `[chưa kiểm: đọc LeRobotDataset 0.6.1 và so với dữ liệu bộ ghi thật]`.
- **Xong khi:** 50 tập ghi, nạp lại bằng `LeRobotDataset` không lỗi, bảng thống kê (độ dài tập, fps, kích thước). Không huấn luyện gì ở bước này trừ khi bạn nói (GPU).

### E7. Cắm phương pháp (≈ 1–2 ngày)
- `arena/methods/base.py` (hợp đồng §2) + `cl0.py` (bọc `CL0Controller`) + `noop.py` + `oracle.py`; chỗ trống có tài liệu cho `clkf` (chờ bạn duyệt thiết kế) và `policy` (chờ bộ chuyển nhãn I2). **Chưa viết** hai phương pháp này; nói rõ trong báo cáo.
- Test hợp đồng cho mọi phương pháp đăng ký: reset/step/finished, không truy cập GT, thời gian suy luận được đo.
- **Xong khi:** `run_arena --methods CL0,NOOP,ORACLE --cells dev_C0,dev_C2 --speeds L0.25,L0.5` chạy trọn và `report` ra bảng §6.3.

### E8. Khớp sim–thật (CHỜ, không làm bây giờ)
Cần số đo thật (`calib.json` thật, vận tốc vật trên băng thật, độ trễ, tiếp xúc kẹp). Làm theo bảng "Khớp sim–thật" ở `KE_HOACH_HUONG_1.md` §3.6; chốt ngưỡng S1 và giá trị nhiễu hiệu chuẩn ở E2.

---

## 5. Cấu trúc thư mục đề nghị (Claude Code chỉnh được, ghi lý do)

```
~/thesis/arena/
  CLAUDE.md                  # §3 của tài liệu này
  ARENA_SETUP_REPORT.md  ARENA_TUNING_LOG.md  CODE_CHANGES.md
  configs/arena.toml
  arena/                     # gói Python: platform.py, scene.py, belt.py, camera.py, arm.py,
                             #   calib_from_scene.py, labeler.py, report.py, run_arena.py,
                             #   objects.py, arrangements.py, record.py, methods/{base,cl0,noop,oracle}.py
  tests/
  locked/                    # sắp xếp và vật TEST của sim, chưa được chạy
  runs/<run_id>/             # trials.csv, trial_*.json, trial_*_log.csv, video/, metrics.json, metrics_report.md, manifest.json
```

Lệnh chính (tên đề nghị):
```
python -m arena.run_arena --methods CL0,NOOP,ORACLE --cells dev_C0,dev_C2 --speeds L0.25,L0.5 --seed 0 --out runs/<run_id>
python -m arena.report runs/<run_id>/trials.csv --ref CL0 --out runs/<run_id>/metrics_report.md
```

---

## 6. Metrics trả về

### 6.1 Định nghĩa (viết vào `arena.toml`/`labeler.py` và đóng băng trước khi so phương pháp)

| Mã | Metric | Định nghĩa | Báo cáo |
|---|---|---|---|
| M1 | **Tỉ lệ thành công (SR)** | thành công / lượt hợp lệ, theo (phương pháp, ô, L). **Thành công** = một vật nhấc cao ≥ 25 mm so với mặt băng và giữ ≥ 2 s liên tục (khớp `TrialResult.success` của mô phỏng động học và §4.3 của kế hoạch) `[đã kiểm]`; vật phải ở trong má kẹp (lệch tâm vật–TCP ≤ w/2) `[đề xuất]` | n, k, Wilson 95% |
| M2 | **SR sạch** | M1 và không vật nào khác bị xô quá 10 mm (từ GT) | như M1 |
| M3 | **Hiệu ghép cặp** | so với `--ref` (mặc định CL0) trên cùng sắp xếp: hiệu SR, số cặp bất đồng (chỉ-chal-thắng b, chỉ-base-thắng c), McNemar chính xác p, bootstrap 95% theo sắp xếp | như `g0_analyze.py g2` |
| M4 | **Nguyên nhân thất bại** | đếm theo danh sách đóng (§4 E3), gán tự động từ GT + outcome | bảng phương pháp × nguyên nhân |
| M5 | **Thời gian nhấc** | từ lần phát hiện hợp lệ đầu tới lúc bắt đầu nhấc; thời gian cả lượt | trung vị, p95 (giây mô phỏng) |
| M6 | **Chi phí tính toán** | ms mỗi bước điều khiển của phương pháp; số tick trễ; VRAM đỉnh; giây thật mỗi lượt | trung vị, p95 |
| M7 | **Chi phí dữ liệu/tinh chỉnh** | số demo, bước và giờ GPU huấn luyện, giờ tinh chỉnh (nhập tay vào `manifest.json`) | giá trị |
| M8 | **Độ lặp lại** | chạy lại cùng hạt giống và cấu hình: tỉ lệ lượt cho cùng kết quả | % |
| M9 | **Chặn dưới/trên** | SR của `NOOP` và `ORACLE` cùng ô, cùng L | % |

### 6.2 Tệp đầu ra
- `trials.csv`: cột của `CSV_COLUMNS` (`trial_id, method, cell, arrangement_id, success, valid, fail_cause, ...`) cộng `engine, seed, speed_mm_s, L, split, clean, fail_cause_auto, t_detect_s, t_lift_s, ms_step_p50, ms_step_p95, wall_s`. `g0_analyze.py cells trials.csv` đọc được file này nguyên trạng (cột thừa bị bỏ qua) `[đã kiểm]`; tên ô giữ `seen_C0 / novel_C0 / novel_C2 / novel_C3` cho bộ chính thức và `dev_C0…dev_C3` khi tinh chỉnh. `fail_cause` điền bằng `fail_cause_auto`.
- `metrics.json` (mọi số của §6.1) và `metrics_report.md` (bảng tiếng Việt, mẫu §6.3).
- `manifest.json`: phiên bản Isaac Sim, hash `arena/` và `code_sha256` của `cl0`, hash `arena.toml` và USD, hạt giống, ngày, GPU.

### 6.3 Mẫu báo cáo (Claude Code in ra trong chat sau mỗi lần chạy, và lưu `metrics_report.md`)

```
Lần chạy <run_id> · engine=isaac · <ngày> · hash arena <8 ký tự> · Isaac <phiên bản>

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p) | t nhấc p50/p95 (s) | ms/bước p50/p95 |

Nguyên nhân thất bại (đếm):
| Phương pháp | Ô | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |

Chặn dưới/trên: NOOP = …%, ORACLE = …% (ô, L)
Độ lặp lại: …/… lượt cùng kết quả
Tốc độ: … giây thật/lượt · lượt không hợp lệ: …/…
Việc bạn cần làm: …
```

Bạn có thể gửi `trials.csv` (hoặc `metrics_report.md`) cho mình trong chat để mình phân tích tiếp (khoảng tin cậy, ghép cặp, công suất, so với kế hoạch).

---

## 7. Cổng của sim (không nằm trong GO/PIVOT của G0–G2; xem `KE_HOACH_HUONG_1.md` §3.6)

| Cổng | Điều kiện | Ghi chú |
|---|---|---|
| **S0a – môi trường đúng** | E1 (a)–(c) đạt; `ORACLE` ≥ 95% ở C0, L = 0,25; `NOOP` ≈ 0% `[đề xuất]` | không đạt = lỗi môi trường, chưa so được gì |
| **S0b – CL-0 chạy được** | CL-0 trên `dev_C0` ≥ 80% (cùng ngưỡng kiểm hệ thống của G0 `[đã kiểm: SANITY_MIN = 0,80]`) sau tối đa 16 giờ tinh chỉnh trong sim. Khi bạn duyệt, chạy `seen_C0` một lần để chính thức hoá S0 ở `KE_HOACH_HUONG_1.md` §3.6 | dưới 80%: báo nguyên nhân theo bảng M4, không nới ngưỡng |
| **S0c – tái lập** | M8 báo cáo; nếu < 100% thì nêu nguồn nhiễu và dùng ≥ 3 hạt giống khi so | |
| **S1, S2** | E8 và sau khi có số thật | chưa làm |

---

## 8. Rủi ro

| Rủi ro | Cách giảm |
|---|---|
| USD của bạn lệch quy ước khớp so với `SO101Kinematics` | kiểm FK ở E1; dừng và hỏi nếu vượt ngưỡng |
| Isaac nặng trên 8 GB VRAM (render + vật lý + huấn luyện) | đo ở E0; không chạy song song với huấn luyện; giảm số vật/độ phân giải nếu cần, ghi lại |
| Python của Isaac ≠ Python của LeRobot | tiến trình riêng, lockstep |
| Hiệu chuẩn từ GT hoàn hảo làm CL-0 trông mạnh hơn thật | nhiễu hiệu chuẩn tuỳ chọn, chốt ở E8; luôn nêu trong báo cáo |
| Chuyên gia `ORACLE` biết thông tin CL-0 không có | báo riêng; chính sách huấn luyện trong sim không phải chính sách của hồ sơ (§3.6) |
| Tiếp xúc kẹp–vật nhỏ (SO-101) không ổn định trong PhysX | `ORACLE` ở E4 phát hiện sớm; chỉnh ma sát/lực kẹp có ghi chú, chỉ dùng vật TRAIN/DEV |
| C3 (vật chạm nhau) rung hoặc trôi | kiểm ổn định ở E5; nếu không đạt, báo và đề xuất đổi ràng buộc |
| Sửa `cl0/*.py` phá dấu đóng băng | luật §3 mục 2 |
| Mất thời gian nếu G0 = PIVOT | đã được bạn chọn làm trước (28/10); các giai đoạn E0–E4 vẫn dùng được cho bài đối chứng |
