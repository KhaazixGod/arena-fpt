# Cắm một phương pháp vào arena

Arena chạy mọi phương pháp qua **cùng một giao diện**, trên **cùng các tờ sắp xếp**, rồi trả metrics theo định dạng của `dir1/g0_analyze.py`. Tài liệu này dành cho phương pháp của bạn và phương pháp lấy từ paper khác.

**Phải biết trước khi đọc số:** mọi số là `engine=isaac`, vật đang là **vật tạm** (6 khối và trụ, E5 sẽ thay), và tay mô phỏng có các giả định vật lý chưa đo trên tay thật. Danh sách giả định ở cuối file.

## 1. Hợp đồng

Một phương pháp là đối tượng có các thành phần sau. Đây cũng là giao diện CL-0 dùng (`cl0.runner.run_controller`).

```python
reset(t0: float, state: RobotState) -> None
step(t: float, frame: Frame | None, belt, state: RobotState) -> Command     # gọi 50 lần mỗi giây mô phỏng (thời gian ảo)
finished: bool;  outcome: str;  events: list[TrialEvent];  log: list[dict];  diag: dict
close() -> None    # tuỳ chọn
phase: str         # tuỳ chọn, hiện trên video
```

**Quan sát.** Chỉ những thứ tay thật cũng có, không gì khác:

| | nội dung |
|---|---|
| `frame` | khung camera mới nhất kể từ bước trước, hoặc `None` |
| `frame.img` | BGR uint8, 1280×720, camera cố định nhìn thẳng xuống băng |
| `frame.t_capture` | thời điểm chụp ước lượng = lúc nhận − độ trễ đã hiệu chuẩn (≈ 0,1 s) |
| `frame.depth_mm` | chỉ khi chạy với `--depth`: độ sâu lý tưởng, mm, cùng điểm ảnh với `img`, không nhiễu cảm biến |
| `belt.s_at(t)`, `belt.speed_at(t)` | quãng băng đã đi (mm) và tốc độ, từ bộ đếm xung |
| `state.q_deg` | 5 khớp, độ, thứ tự LeRobot |
| `state.gripper` | 0–100 |

**Hành động.** `Command(q_deg=5 góc đích (độ) hoặc None, gripper=0–100 hoặc None, phase="…")`. Lệnh được áp làm đích cho servo ngay ở bước đó.

**Kiến thức dùng chung** qua `ctx: MethodContext`, mọi phương pháp đều được dùng:

| trường | nội dung |
|---|---|
| `ctx.cfg` | `arena.toml` |
| `ctx.kin` | FK/IK SO-101, đã có `tcp_offset` (tâm khe kẹp) |
| `ctx.calib` | `calib.json`: homography điểm ảnh → mặt băng, hướng băng, mm/xung, độ trễ |
| `ctx.background_path` | ảnh nền băng trống |
| `ctx.extra` | các cặp `--method-arg key=value` |

**Luật:**
- Không phương pháp nào được đọc ground truth. Chỉ `ORACLE` (đặc quyền) có `ctx.gt`, và có test kiểm.
- Lỗi (exception) trong phương pháp được tính là thất bại của chính phương pháp đó (`outcome = method_exception:<loại>`), không làm sập lô.
- Thời gian tính của phương pháp không làm chậm mô phỏng (lockstep), nhưng được đo và báo ở cột `ms/bước`.

## 2. Ba cách cắm

### A. Phương pháp đầy đủ, trong cùng tiến trình
Phù hợp khi thư viện của phương pháp chạy được trong Python của Isaac: Python 3.12, numpy 2.3, torch 2.11 + CUDA, OpenCV. Viết một hàm tạo:

```python
# mypkg/mymethod.py
def make_method(ctx):          # ctx: arena.methods.MethodContext
    return MyController(ctx)    # cài hợp đồng ở mục 1
```

```bash
cd ~/Projects/dir1_tools/arena
~/env_isaac/bin/python -m arena.run_arena --methods CL0,mypkg.mymethod:make_method --cells dev_C0,dev_C2 --speeds L0,L0.25 --n 20 --out runs/<tên> --report
```

### B. Bộ phát hiện điểm kẹp trên ảnh
Phù hợp với phần lớn paper "grasp detection", kiểu GG-CNN hay GR-ConvNet: chỉ cần viết hàm `ảnh → [PixelGrasp(u, v, góc, bề rộng mm, điểm)]`.
- Bộ chuyển `pixel_grasp.py` đổi sang hệ băng bằng `calib.json`, rồi dùng chung bộ theo dõi, logic chọn vật và bộ thực thi bám băng của CL-0. Vì vậy hai phương pháp kiểu này chỉ khác nhau ở **nhận thức**: so sánh công bằng nhất.
- Góc là phương của **trục khép** trong ảnh, độ, ngược chiều kim đồng hồ từ trục +u (sang phải), lấy mod 180.
- Ví dụ chạy được: `arena/methods/examples/blob.py` (bộ phát hiện theo vết màu, rất đơn giản, **không** phải baseline).

```python
from arena.methods.pixel_grasp import PixelGrasp, pixel_grasp_method
def make_method(ctx):
    def detect(img_bgr, depth_mm):          # depth_mm = None nếu không chạy --depth
        return [PixelGrasp(u, v, angle_deg, width_mm, score)]
    return pixel_grasp_method(ctx, detect)  # feasibility="yaw" (IK đúng góc, mặc định) | "cl0" (bản đồ tầm với của CL-0)
```

### C. Phương pháp ở môi trường Python khác
Dùng khi phương pháp cần LeRobot, một phiên bản torch khác, hay repo riêng của paper.

```bash
# terminal 1, trong venv của phương pháp (chỉ cần numpy):
python ~/Projects/dir1_tools/arena/remote_server.py --factory mypkg.mymethod:make_method --name MYMETHOD --port 6001 --path /đường/dẫn/repo
# terminal 2:
~/env_isaac/bin/python -m arena.run_arena --methods CL0,REMOTE --method-arg remote=localhost:6001 --cells dev_C0 --speeds L0.25 --n 20 --out runs/<tên> --report
```

- `make_method(info)` nhận `info` gồm cỡ ảnh, `control_hz`, `calib` (dict của `calib.json`), `cfg` (dict của `arena.toml`) và đường dẫn ảnh nền.
- Ảnh đi qua socket cục bộ (khoảng 2,7 MB mỗi khung). Tên trong `trials.csv` là `REMOTE:<name>`.
- Arena gửi sang toàn bộ mẫu bộ đếm băng, và `belt.s_at` / `belt.speed_at` ở phía server tính bằng **đúng** thuật toán của `cl0.hw.belt`.
- Đã kiểm: CL-0 phục vụ qua REMOTE cho cùng kết quả với CL-0 chạy trong tiến trình. Băng đứng yên trùng từng bit; băng chạy thì phần lệch nhỏ còn lại đến từ nhiễu render, không từ cầu nối.
- Chính sách học (ACT/DP của LeRobot) cắm theo cách này: LeRobot đã có trong `~/venvs/cl0`, không có trong Python của Isaac.

## 3. Phương pháp có sẵn

| tên | là gì | đặc quyền |
|---|---|---|
| `CL0` | baseline CL-0, không đổi mã | không |
| `NOOP` | không làm gì: chặn dưới, bắt thành công giả do môi trường | không |
| `ORACLE` | bộ điều khiển và bộ thực thi của CL-0 + nhận thức từ GT + kiểm khả thi đúng góc kẹp: trần của môi trường | **có** |
| `CL0_YAW` | **không phải baseline**: CL-0 + kiểm khả thi đúng góc kẹp, để đo cái giá của bản đồ tầm với roll = 0 của CL-0 | không |
| `REMOTE` | phương pháp từ tiến trình khác (cách C) | không |

## 4. Kết quả và cách đọc

- `runs/<tên>/trials.csv`: một dòng mỗi lượt. Cột của G0 (`g0_analyze.py cells trials.csv` đọc được nguyên trạng) cộng cột arena: `L, clean, fail_cause_auto, t_detect_s, t_lift_s, ms_step_p50/p95, wall_s, …`.
- `metrics_report.md`, `metrics.json`: theo mẫu §6.3 (SR + Wilson, SR sạch, hiệu ghép cặp so với `--ref` có McNemar và bootstrap, nguyên nhân thất bại, thời gian, cổng S0).
- `trial_XXXX.json` (sự kiện, pha, nhãn), `trial_XXXX_log.csv` (log riêng của phương pháp), `trial_XXXX_gt.npz` (GT từng tick), `videos/` (khi có `--video` / `--debug-video`).
- Thành công: một vật nhấc ≥ 25 mm, giữ ≥ 2 s, và nằm trong má kẹp. Nguyên nhân thất bại gán tự động theo `arena/LABEL_RULES.md`.
- Chạy lại đúng lệnh cũ thì **tiếp tục** từ chỗ dở (bỏ qua các lượt đã có dòng hợp lệ).
- **Lặp lại:**
  - Mặc định, mỗi lượt dựng lại cảnh PhysX, nên vật lý không phụ thuộc lượt trước.
  - Ảnh render có nhiễu ngẫu nhiên nhỏ (trung bình 0,1–0,4 mức xám, như nhiễu cảm biến). Vì vậy phương pháp **dùng ảnh** không lặp lại trùng từng bit.
  - Khi so sánh, chạy `--reps 3`. Báo cáo có dòng "nhóm lặp cùng kết quả" cho mỗi phương pháp.
  - Phương pháp không dùng ảnh (`ORACLE`, `NOOP`) lặp lại trùng từng bit.
- Tốc độ:
  - phương pháp dùng ảnh: khoảng 35–60 giây thật mỗi lượt (render 30 fps chiếm phần lớn);
  - `NOOP`/`ORACLE`: khoảng 15 s, vì không render ảnh. Vật lý và thời gian vẫn như nhau.

## 5. Giả định của môi trường (đọc trước khi tin số)

| giả định | giá trị | trạng thái |
|---|---|---|
| lực kẹp | 2,5 N·m | `[chưa đo trên tay thật]` |
| tốc độ khớp kẹp | ≤ 150°/s | `[chưa đo trên tay thật]` |
| ma sát má | 1,0 | `[chưa đo trên tay thật]` |
| vật | 20–35 g, ma sát 0,8 | |
| va chạm của kẹp | phân rã lồi của mesh | |
| tay mô phỏng | đáp nhanh hơn servo thật (E1) | |
| hiệu chuẩn | sinh từ GT nên **hoàn hảo** (nhiễu tuỳ chọn, mặc định tắt) | |
| độ sâu (khi `--depth`) | lý tưởng, không nhiễu | |
| camera | một camera cố định, không có camera cổ tay | |

Sai khác với tay thật chốt ở E8, khi có số đo thật. Chi tiết và bằng chứng: `arena/ARENA_SETUP_REPORT.md`.
