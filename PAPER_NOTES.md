# PAPER_NOTES (nhánh paper-dev; không thuộc bản đồ án đóng băng `thesis-freeze-2026-11-14`)

## P1. Chẩn đoán trần ORACLE (14/11/2026, sheet không khóa `arrangements/sim/train_C2.csv`, ORACLE, n = 60)
ORACLE = bộ thực thi CL-0 + nhận thức hoàn hảo. Ghép cặp trên cùng 60 cảnh, mỗi lần đổi một thứ (`scripts/p1_oracle_diag.sh`, `p1_slip_mech.sh`, `p1_slip_mech2.sh`; cấu hình sao chép `configs/arena_p1_*.toml`, không sửa file gốc).

| Biến thể (L0.5 nếu không ghi) | Thành công | Lỗi chính | Ghép cặp vs gốc (mất/được), McNemar chính xác |
|---|---|---|---|
| Gốc (`runs/p1_oracle_train_c2_l05`) | 41/60 | `dropped_in_hold` 11, `ik_fail` 3, `late` 2 | |
| A ma sát đệm 1,5 → 3,0 | 39/60 | `dropped_in_hold` 10 | 4/2, p = 0,69 |
| B kẹp cao 10 → 16 mm | 41/60 | `dropped_in_hold` 12 | 3/3, p = 1,0 |
| C nhấc chậm `vmax_z` 150 → 60 | 40/60 | `dropped_in_hold` 9, `ik_fail` 6 | 3/2, p = 1,0 |
| E ma sát xoắn đệm 5 → 12 mm | 41/60 | `dropped_in_hold` 10 | 2/2, p = 1,0 |
| **D băng đứng yên (L0)** | **50/60** | `dropped_in_hold` 4, `picked_hold_complete` 5 | 4/13, p = 0,049 |

Kết luận (thăm dò, hậu nghiệm, một lần chạy mỗi biến thể): thông số vật lý của kẹp (ma sát, ma sát xoắn, độ cao kẹp, tốc độ nhấc) **không** cải thiện trần; chuyển động của băng làm trần giảm (83% → 68%). Cơ chế cụ thể **chưa xác định**: sai số bám tại thời điểm kẹp có trung vị như nhau giữa lượt đạt và lượt hỏng (0,1 mm), chỉ vài lượt hỏng có sai số lớn. Vật nghiêng 18–25° ngay khi nhấc ở cả lượt đạt lẫn lượt hỏng (`runs/p1_oracle_train_c2_l05/trial_*_gt.npz`).
Chưa kiểm: đáp ứng theo tốc độ (L0.25), vận tốc tương đối của đệm kẹp và vật lúc đóng kẹp, ảnh hưởng của gia tốc băng.

## P1b. Cơ chế (14/11, video + log 50 Hz; người dùng nhận ra va chạm và khớp giật trong video)
- **A. Khớp cổ tay xoay (wrist roll) chạm biên khi bám băng (8/19 lượt hỏng, 1/41 lượt đạt; 0/60 khi băng đứng yên).** Bám theo băng làm khớp quay đế (pan) xoay ~20°; để giữ góc kẹp, cổ tay xoay bù và đi tới −154,2° = giới hạn −157,2° + biên 3° (`joint_margin_deg`). `cl0/executor.py` `_ik_cmd`: IK nhanh (1 hạt giống) bị loại vì ngoài biên → giữ nguyên lệnh cũ; mỗi 0,2 s chạy IK đầy đủ, nghiệm mới bị `_rate_limit` (150°/s × 0,02 s = 3°) → lệnh khớp **đứng yên 10 nhịp rồi nhảy 3° ở mọi khớp** (độ giật thấy trong video). Trong lúc đó tay ngừng bám, vật đi tiếp 30–50 mm → kéo/xoay vật trong kẹp, hoặc hủy `ik_fail` (t17 ×2, box06). Lượt: train_C2_003, 013, 015, 018, 028, 030, 042, 058. Gốc: nhánh góc kẹp (θ hay θ+180°) chọn theo tính liên tục (`th_ref`), không tính khoảng trống của cổ tay cho đoạn bám sắp tới.
- **B. Vật rộng (44–49 mm trong khe 60 mm), hàm kẹp chạm vật khi hạ (3/19: cyl12 ×3).** Vật dịch 3,2–3,7 mm trước khi đóng, bị đẩy 10–17 mm lúc đóng.
- **C. Còn lại (8/19)**: cyl09 ×2 (giữ ở mép, rơi khi chuyển), cyl08 ×2, cyl11, l13, l14, box04 (`late`). Chưa phân loại kỹ.
- Mở kẹp rộng hơn (F: `gripper_open` 50, TCP −37) **xấu hơn**: 27/57 lúc kiểm (`runs/p1_slip_F_open50`).

## P2. W1: chọn nhánh góc kẹp theo khoảng trống của cổ tay (15/11; `arena/wrist_branch.py`, `arena/methods/oracle_w.py`)
**Cơ chế, đo lại chính xác.** Với kẹp thẳng đứng, yaw của trục khép = −q1 + q5 + 177,21° (q1 = pan, q5 = wrist roll), đúng tuyệt đối theo FK (sai lệch 0,0000° trên 1026 tư thế ngẫu nhiên; `WristModel` kiểm lại khi khởi tạo). Khi bám vật trên băng, yaw trong hệ băng cố định nên cổ tay xoay **đúng bằng** góc quay của đế: 20–50° trong một lượt L0,5, tới ~134° nếu tính hết cửa sổ 4 s. IK của CL-0 khớp yaw theo mod 180° và khởi động ấm từ lệnh trước, nên nhánh (θ hay θ+180°) do tính liên tục quyết định. Khi cổ tay chạm biên, IK nhanh hội tụ vào nhánh vi phạm biên, IK đầy đủ (mỗi 0,2 s) tìm ra nhánh kia → giữ lệnh 10 nhịp rồi nhảy 3°. Sửa P1b: ở L0 không có lượt hỏng do cơ chế này, nhưng 9/60 lượt có nhánh gần nhất **không với tới** ở vị trí vật; executor gốc lật sang nhánh kia giữa đường (mất ~0,7 s, `runs/p1_slip_D_l0` lượt 001).

**W1** (một thay đổi; `ORACLE_W` = ORACLE + W1, `CL0_W` = CL0 + W1). Lúc chọn vật, dự báo các khớp trên cửa sổ bám (vị trí vật từ 0,5 s tới 4,0 s sau, ở độ cao chờ tới 1,0 s rồi độ cao kẹp/nhấc) cho mọi nhánh θ + 180k mà bộ lọc yaw quay tới được (≤ 270°), bằng IK có cổ tay không chặn. Giữ nhánh gần nhất của CL-0 trừ khi cổ tay dự báo vào trong 10° quanh biên (ngoài biên 3° sẵn có); khi đó lấy nhánh có vi phạm đầu tiên muộn nhất. `BranchExecutor` bám nhánh đã chọn (th_ref gần kế hoạch nhất; IK gieo hạt và chỉ nhận nghiệm trên nhánh đó). Lượt không đổi nhánh chạy đúng mã CL-0. Mỗi lượt ghi sự kiện `w1_branch`.
Tham số lấy từ log sheet không khóa `train_C2` L0,5 (`runs/p1_oracle_train_c2_l05`): chọn → nhấc xong tối đa 3,84 s (cửa sổ 4,0 s); TCP tới gần vật sau 0,46–0,54 s (bắt đầu 0,5 s); chọn → DESCEND trung vị 1,12 s (đổi độ cao ở 1,0 s); khoảng an toàn cổ tay 10° [đề xuất, chưa chỉnh].

**Kiểm ngoại tuyến** (phát lại bộ dự báo tại thời điểm chọn của 60 lượt đã ghi, không chạy Isaac): ở L0,5 W1 đổi nhánh 16/60 lượt, gồm **cả 10/10** lượt có ≥ 20 nhịp giữ lệnh (003, 004, 013, 015, 016, 018, 028, 030, 042, 058) và 6 lượt cổ tay vào sát biên 0–4° ở cuối lượt (005, 006, 010, 012, 041, 049); 9 lượt nhánh gần nhất có nguy cơ nhưng nhánh kia còn tệ hơn → giữ nguyên. Ở L0 đổi 11/60: 9 lượt trùng đúng nhánh mà executor gốc lật sang (q5 lúc DESCEND quan sát 15,1 / dự báo 16,5; −13,9 / −13,5; …), 2 lượt cổ tay còn cách biên 6,6° và 1,7°.
**Mô phỏng động học** (servo lý tưởng, không vật lý; `BeltExecutor` gốc vs `BranchExecutor`, cùng điểm chọn của lượt đã ghi): gốc 49–125 nhịp giữ lệnh, sai số bám trung vị 17–68 mm (lớn nhất 60–129 mm); W1 0 nhịp giữ lệnh, sai số ≤ 1,7 mm (lượt 003, 005, 013, 042, 058). Lượt không đổi nhánh (002) giống hệt gốc.
**Học sinh (ACT_I2) và cổ tay.** Hành động I2 mã hóa yaw bằng (cos 2ψ, sin 2ψ), tức là mod 180°, nên chính sách học **không** chọn nhánh. Bộ thực thi I2 (`arena/methods/act_i2.py::_ik`) dùng cùng kiểu IK (khởi động ấm, mod 180°, biên 3°, chặn 150°/s), nên về nguyên tắc cũng gặp được cơ chế A. Trên log DEV ở L0,5 (`e16_repeat_r100`, `e16_commit_c23`, `e14_act_i2_dev2`, `e15_i2_r100`; 100 lượt, không dùng log TEST), chỉ 2 lượt có cổ tay chạm biên khi IK hỏng (dev_C2_003 vẫn đạt; dev_C3_011 hỏng, kẹp lật 175° trong 1,5 s). Phần lớn lần IK hỏng của ACT là khớp gập cổ tay (q4 ≈ 92°) ở khoảng 5,9 s, sau lúc kẹp. **Quyết định [đề xuất]:** giữ nguyên bộ thực thi I2 như G2 cho mọi chính sách học (ACT_old, ACT_W, DP_W), để H2 chỉ khác ở dữ liệu huấn luyện. Ghi là giới hạn: W1 chưa áp cho bộ thực thi I2.
**Lỗi ở lần chạy Isaac đầu (v1, 15/11 16:32, dừng ở 19 + 20 lượt, giữ lại `runs/p2_oraclew_train_c2_l0{5,}`).** Mỗi lượt khởi động băng từ đứng yên (dốc 200 mm/s², đủ tốc độ ở ~0,45 s); lúc chọn vật (0,18 s) tốc độ đo được chỉ ~25/75 mm/s. Bộ dự báo v1 dùng nguyên tốc độ đo nên đoán thiếu quãng đi và chỉ đổi nhánh 1 lượt (004: `late` → đạt) thay vì 16. Bản phát lại ngoại tuyến không thấy lỗi này vì dùng tốc độ danh định. **v2:** quãng đi dự báo = tốc độ đo, tăng theo dốc firmware (`cfg.belt.accel_mm_s2`) tới tốc độ do chính máy tính ra lệnh (`cl0.hw.belt.Belt._segs`, không phải GT). Phát lại với đầu vào như chạy thật: vẫn đúng 16/60 (L0,5) và 11/60 (L0).

### P2 kết quả cổng (15/11 17:13; `logs/2026-11-15_171325_p2_gate_compare.txt`; `scripts/p2_compare.py`)
| `train_C2`, 60 cảnh ghép cặp, engine=isaac | ORACLE | ORACLE_W (W1 v2) | mất / được | McNemar chính xác |
|---|---|---|---|---|
| L0,5 (`runs/p1_oracle_train_c2_l05` vs `runs/p2_oraclew2_train_c2_l05`) | 41/60 (68,3%) | **49/60 (81,7%)** | 0 / 8 | p = 0,0078 |
| L0 (`runs/p1_slip_D_l0` vs `runs/p2_oraclew2_train_c2_l0`) | 50/60 (83,3%) | 52/60 (86,7%) | 0 / 2 | p = 0,50 |
- L0,5: nhịp giữ lệnh khi bám 1055 (10 lượt ≥ 10 nhịp, 13 lượt có nhịp ở biên cổ tay) → **0**. W1 đổi nhánh 16 lượt (đúng 16 lượt bản phát lại dự báo): 8 hỏng → đạt, 6 đạt → đạt, 2 hỏng → hỏng (028 t17: `ik_fail` → `empty_grasp`; 041). 44 lượt không đổi nhánh cho kết quả **giống hệt** bản gốc (mô phỏng tất định với cùng đường mã).
- Được: 003, 004, 013, 015, 018, 030, 042, 058 = 7/8 lượt nhóm A + 004 (`late`, 126 nhịp giữ lệnh). Lỗi còn lại (11): `slip` 7, `timing` 2, `grasp_point` 2.
- L0: đổi nhánh 11 lượt, được 006 và 030 (hai lượt cổ tay chỉ còn cách biên 6,6° và 1,7°), không mất lượt nào.
- **Cổng [đề xuất trước khi chạy]: đạt cả ba**: 0 lượt đóng băng vì biên cổ tay; L0,5 49/60 ≥ 45/60; L0 không giảm (+2).
- Lưu ý: tham số W1 (cửa sổ 4 s, bắt đầu 0,5 s, 10°) lấy từ log chính sheet này, nên p ở đây là bằng chứng thăm dò. Sheet xác nhận là `train_C3` (chuỗi `scripts/p2p3_chain.sh`, đang chạy).
- Thời gian lập kế hoạch: trung vị 195 ms mỗi lượt (một lần, lúc chọn vật).

## P4 chuẩn bị: Diffusion Policy với giao diện I2 (15/11, chưa huấn luyện thật)
- Mã: `arena/dp_i2.py` (bước tương đối `relative_actions_last_obs`: với lô huấn luyện của DP, state là (B, n_obs, D), bước gốc của LeRobot 0.6.1 sẽ trừ sai/không broadcast; bước mới lấy state **khung cuối** làm mốc), `train_dp_i2.py` (như `train_act_i2.py`, chỉ thay factory processor), `arena/methods/diffusion_i2.py` (cùng bộ thực thi I2 như ACT_I2; đẩy MỌI khung vào hàng đợi 2 quan sát, lấy mẫu chuỗi mỗi `DP_REPLAN` khung).
- Môi trường: cài `diffusers==0.38.0` (LeRobot 0.6.1 cần ≥0.38,<0.40) + `regex==2026.9.29`, `importlib_metadata`, `lazy-importer` 0.1.0 (Apache-2.0, chỉ là tiện ích import, không gọi mạng/tiến trình), `zipp` vào **site-packages riêng của `~/venvs/lerobot_data`** (không nâng cấp gói nào; venv `cl0` không đổi). Gỡ: `~/venvs/lerobot_data/bin/pip uninstall diffusers lazy-importer`.
- Kiểm trên CPU (dữ liệu E6, mô hình thu nhỏ, 3 bước): huấn luyện chạy (loss 1,2–1,3), checkpoint nạp lại bằng `make_pre_post_processors` gốc (bước tương đối được nối lại), kiểm đơn vị bước tương đối (trừ đúng state khung cuối trên x, y, z; yaw/gripper giữ nguyên), suy luận 2 khung → chuỗi (8, 6) tuyệt đối; phương thức DP_I2 với băng/camera giả: 6 kế hoạch trong 1,5 s, lệnh khớp mọi nhịp.
- Chưa làm: đo tốc độ huấn luyện trên GPU, chọn siêu tham số trên DEV (horizon, n_action_steps, kích thước UNet, số bước khử nhiễu khi suy luận).

### P2 xác nhận trên `train_C3` (sheet không dùng khi thiết kế W1; 15/11 17:43; chuỗi `scripts/p2p3_chain.sh`)
| `train_C3` L0,5, 60 cảnh ghép cặp | ORACLE (`runs/p2_oracle_train_c3_l05`) | ORACLE_W (`runs/p2_oraclew_train_c3_l05`) | mất / được | McNemar chính xác |
|---|---|---|---|---|
| Thành công | 35/60 (58,3%) | **44/60 (73,3%)** | 0 / 9 | p = 0,0039 |
- Nhịp giữ lệnh 1563 (17 lượt có nhịp ở biên cổ tay) → 72 (0 lượt ở biên cổ tay). W1 đổi nhánh 19 lượt: 9 hỏng → đạt, 8 đạt → đạt, 2 hỏng → hỏng; 41 lượt không đổi nhánh giống hệt bản gốc. Lỗi `collision` 10 → 6, `slip` 10 → 8, `grasp_point` 3 → 0.
- Còn 2 lượt `ik_fail` (013, 060, ở cả hai bản): khớp gập cổ tay q4 ≈ 91° (biên 92°) khi hạ ở xa và thấp; không phải cổ tay xoay.
- **Ứng viên W2 (chưa làm, chỉ ghi):** kiểm khả thi lúc chọn vật của CL-0 (`_pick_a_grasp`, `_lift_feasible`) cũng dùng tốc độ băng đo được khi băng còn tăng tốc (~8–25/75 mm/s ở 0,18 s), nên đoán vật đi ~15 mm thay vì ~120 mm tới lúc kẹp và có thể chọn vật sẽ ra khỏi tầm. Ảnh hưởng ≤ 4 lượt mỗi sheet (`ik_fail`/`late`). Đây là đổi logic chọn vật → cần người dùng duyệt nếu muốn áp cho `CL0_W`.

### P2 `CL0_W` trên DEV (15/11 18:48; `logs/2026-11-15_184802_p2_confirm_compare.txt`)
| `dev_C2` L0,5, 60 cảnh ghép cặp, engine=isaac | CL0 (`runs/p2_cl0_dev_c2_l05`) | CL0_W (`runs/p2_cl0w_dev_c2_l05`) | mất / được | McNemar chính xác |
|---|---|---|---|---|
| Thành công | 25/60 (41,7%) | **52/60 (86,7%)** | 2 / 29 | p < 10⁻⁶ |
- CL0 chịu cơ chế A **nặng hơn ORACLE nhiều**: 37/60 lượt có nhịp giữ lệnh ở biên cổ tay (ORACLE `train_C2`: 13/60), `ik_fail` 18. Lý do: CL0 nhắm yaw 90–130° trong hệ băng (vật tròn dùng 90° cố định, `isotropic_theta_deg`); từ tư thế nhà (−2,8°), nhánh gần nhất là θ − 180°, cổ tay đi về phía âm rồi chạm −157° khi đế quay theo vật. W1 đổi nhánh 48/60 lượt.
- CL0_W: `ik_fail` 18 → 2, nhịp giữ lệnh 5053 → 188, lượt có nhịp ở biên cổ tay 37 → 0. Mất 2 lượt (021, 034; đều là lượt đổi nhánh). Trong 12 lượt không đổi nhánh có 1 lượt khác kết quả: CL0 dùng ảnh render, nên khác ORACLE là không hoàn toàn tất định.
- **Hệ quả cho bài báo.** (1) So sánh G2 (ACT ≈ CL0, 35% / 37%) bị lẫn bởi lỗi bộ thực thi: lỗi này gần như không chạm ACT (2/100 lượt DEV) nhưng chạm CL0 nặng [suy luận cho TEST: chưa kiểm, không chạy TEST]. (2) Baseline mô-đun công bằng (`CL0_W`) đạt 87% trên DEV L0,5, cao hơn mọi kết quả ACT trên DEV L0,5 đã có (`e14_act_i2_dev2` 13/20, `e15_i2f` 14/20). H1 ("ACT_W hơn baseline mô-đun mạnh nhất ≥ 15 điểm") **rất khó đạt**. Cần người dùng chọn lại khung bài báo trước khi viết tiền đăng ký.

## P3 sự cố (15/11 19:42–21:00)
- Hai làn ghi demo (`scripts/p3_demos_w.sh`, ORACLE_W, render 640×360) chạy bình thường ~60 s/lượt, rồi **cả hai cùng ngừng** lúc 19:42; bộ canh giữ diệt và chạy lại; các lần sau ngừng sớm dần (một lượt 310 s cho 8 s ảo; hai lần cuối không tiến được lượt nào) → bỏ cuộc ở 83/420 và 93/420 lượt (0 lượt `valid=0`; các lượt đã ghi giữ nguyên). Không có lỗi trong log Isaac; đĩa 54 GB trống, RAM đủ. Giả thuyết [chưa kiểm]: hai tiến trình render tranh VRAM 8 GB. Đang kiểm bằng log VRAM (`logs/2026-11-15_210250_p3_vram.log`).
- Lỗi script: `p3_demos_w.sh` không kiểm số lượt trước khi chuyển dữ liệu, nên chuỗi đã bắt đầu đổi 146 tập dở dang (đã dừng; thư mục dở dang để riêng ở `runs/p3_demos_w/lerobot_i2_PARTIAL_killed_2026-11-15`, không dùng). Đã sửa: chỉ chuyển khi đủ 420/420 mỗi làn; chuỗi chỉ huấn luyện khi có `meta/stats.json`.
- Chạy lại 21:02 với **một Isaac mỗi lúc** (`scripts/p3_seq_chain.sh`, unit `arena-p3seq`): tiếp tục từ các lượt đã có, rồi chuyển dữ liệu, rồi `ACT_W` ×3.
- **Nguyên nhân treo (stack qua SIGUSR1, 22:04):** luồng chính kẹt trong `omni.replicator.core ... orchestrator.step` (gọi từ `arena/world.py::_grab` khi chụp khung), GPU 0%: bộ điều phối render của Isaac chờ một khung không tới. Không phải mã W1. Lỗi này có từ trước (chuỗi E9: 7 lần, E18: 1, G2: 1; bộ canh giữ xử lý), tối nay dày hơn (~25 phút/lần) khi ghi demo; một làn cũng bị. Không sửa đường render (giữ nền tảng như các lần chạy trước); chỉ cho bộ canh giữ thử tới 60 lần và kết luận treo sau 200 s (`RUN_UNTIL_ATTEMPTS`, `RUN_UNTIL_STALL_S`, mặc định cũ không đổi). Kiểm: số dòng CSV = số JSON, số tập demo = số lượt thành công ở cả hai làn (không có tập mồ côi).

## P3 kết quả (16/11 04:59; `runs/p3_demos_w_a`, `runs/p3_demos_w_b`; engine=isaac)
ORACLE_W trên các sheet của E6 (`arrangements/sim_ext`, `train_C0..C3`, 70 sắp xếp đầu mỗi ô) × L0, L0,25, L0,5: **840/840 lượt hợp lệ, 677 tập thành công (80,6%)** → demo.
| Tốc độ | Tập / lượt | | Ô | Tập / lượt |
|---|---|---|---|---|
| L0 | 229/280 (81,8%) | | train_C0 | 167/210 |
| L0,25 | 233/280 (83,2%) | | train_C1 | 170/210 |
| **L0,5** | **215/280 (76,8%)** | | train_C2 | 178/210 |
| | | | train_C3 | 162/210 |
- So với E6 (ORACLE cũ, 444 tập từ 560 lượt, chỉ L0/L0,25): thêm 215 tập L0,5; phần L0+L0,25 có 462 tập (≈ cỡ E6), dùng cho ablation `ACT_W_slow` (tách hiệu ứng thầy đã sửa khỏi hiệu ứng thêm L0,5).
- Lỗi treo của Replicator: 1 lần sau khi chạy một làn với ngưỡng 200 s (23:42), bộ canh giữ tự chạy lại.

## P4 checkpoint (sha256, để điền vào tiền đăng ký mới)
```
act_w_s1000: abd7cb0a154dc8a541fbb6a9bb03ce803e37e0abb1a8703ded41e9aa43f8115f  (16/11 08:31; 100 000 bước, batch 8, loss ~0,05; logs/2026-11-16_061648_train_act_w_s1000.log)
act_w_s2000: c07a917d9d125bca4f2e0585368c04d24400ca2b1743fb3bd2590894bf3cbb6c  (16/11 10:46; 2026-11-16_083151_train_act_w_s2000.log)
act_w_s3000: 37d2e0d9e1ebf46a74e253696ddb8ae89ab1657386e786c9919be3324ec145a5  (16/11 13:02; 2026-11-16_104643_train_act_w_s3000.log)
act_w_slow_s1000: 97fec9039fc7d79f4c31a52bd69e5df4b89a11fdb307ea9edfe989bbd0a5b695  (16/11 ~19:45; ablation, 462 tập L0/L0,25; 2026-11-16_172750_train_act_w_slow_s1000.log)
dp_w_s1000: 737d09ccd963a151b6be4ca4a1161f27c74372602a834389582e3b22153d0d3e  (17/11 ~00:35; UNet 256-512-1024, batch 16, 82 000 bước, loss ~0,003; 2026-11-16_203501_train_dp_w_s1000.log)
dp_w_s2000: 88b47f6aea835c4f9077f45dbbc58a1b2c7f16388c5c8567b76ddd948fed997a  (17/11 ~05:40; cùng công thức; 2026-11-17_014139_train_dp_w_s2000.log)
```

## P5 bước 1: W1 theo tốc độ trên DEV (16/11 13:02–14:38; `logs/2026-11-16_143831_p5_sweep_compare.txt`; `scripts/p5_queue.sh`)
| `dev_C2`, ghép cặp, engine=isaac | ORACLE → ORACLE_W | CL0 → CL0_W | lượt có nhịp giữ ở biên cổ tay (gốc → W1) |
|---|---|---|---|
| L0,25 (n = 30) | 27 → 29 (mất 0 / được 2, p = 0,50) | 24 → 26 (0 / 2, p = 0,50) | ORACLE 5 → 0; CL0 11 → 1 |
| L0,5 (n = 60) | **45 → 58** (0 / 13, p = 0,0002; `runs/p5_*oracle_dev_c2_l05`, 17/11) | **25 → 52** (2 / 29, p < 10⁻⁶) | ORACLE 20 → 0; CL0 37 → 0 |
| L1,0 (n = 60) | 0 → 0 | 0 → 0 | ORACLE 0 → 0; CL0 3 → 0 |
- L1,0 (150 mm/s) là sàn cho mọi phương pháp: ORACLE `late` 50 + `ik_fail` 10; ORACLE_W `late` 60; CL0 `late` 36 + `ik_fail` 24; CL0_W `late` 59. `late` = phép kiểm khả thi của CL-0 trước khi hạ (vật đi ~315 mm trong `t_after_settle_s` = 2,1 s → ra khỏi tầm). W1 đổi `ik_fail` thành `late`; giới hạn ở L1,0 là tầm với và thời gian, không phải cổ tay. Giải thích kết quả H4 của G2 (0/30 mọi phương pháp ở L1,0).
- L0,25: cổ tay vẫn chạm biên (CL0 11/30 lượt) nhưng tay kịp bắt lại, ít khi thành thất bại → hiệu ứng nhỏ (+2/30).
- Kết luận cho H3: hiệu ứng của W1 lớn nhất ở tốc độ trung bình (L0,5): đủ nhanh để đế quay nhiều mỗi lượt, chưa nhanh tới mức vật ra khỏi tầm. Bảng DEV đã đủ ô (ORACLE/ORACLE_W L0,5 chạy 17/11 01:12–01:41, `logs/2026-11-17_014138_p6_oracle_dev_l05_compare.txt`).

## P5 bước 2: ACT trên DEV (16/11 14:38–17:25; `runs/p4_dev_*_dev_c2_l05`; cùng 20 cảnh `dev_C2_001..020`, L0,5; suy luận như G2)
| Phương pháp | Thành công | Lỗi |
|---|---|---|
| CL0 (`runs/p2_cl0_dev_c2_l05`, 20 cảnh đầu) | 7/20 | collision 7, timing 3, slip 3 |
| ACT_old s1000 (`act_i2_s1000`, chạy lại với mã hiện tại; E14 cũ: 13/20) | 15/20 | collision 5 |
| ACT_W s1000 / s2000 / s3000 | 15 / 15 / 13 (trung bình 14,3/20 = 72%) | collision 4 / 5 / 6, other 1 / 0 / 1 |
| CL0_W (`runs/p2_cl0w_dev_c2_l05`, 20 cảnh đầu) | **17/20** | collision 2, timing 1 |
- ACT_W s1000 vs ACT_old s1000: mất 3, được 3, p = 1,0. **H2 (thầy đã sửa + demo L0,5 giúp học sinh) không được ủng hộ trên DEV**, giống E15 (I2F).
- Lỗi của ACT gần như toàn `collision` (kẹp chạm vật/vật bên cạnh), không phải cổ tay; nên sửa thầy không chạm vào điểm yếu của học sinh.
- Sau khi sửa bộ thực thi, pipeline mô-đun (CL0_W 17/20) ≥ chính sách học (14–15/20) trên DEV. Khớp khung (b).
- **Ablation ACT_W_slow s1000** (demo ORACLE_W chỉ L0/L0,25, 462 tập ≈ cỡ E6; `runs/p4_dev_act_w_slow_s1000_dev_c2_l05`): **15/20** (collision 5) = ACT_old = ACT_W s1000/s2000. Trên 20 cảnh DEV này, ACT không nhạy với thầy (ORACLE hay ORACLE_W) lẫn với demo L0,5; giới hạn của nó là va chạm.

## P5 bước 3: Diffusion Policy trên DEV (17/11 00:34–01:11; `runs/p4_dev_dp_w_s1000_dev_c2_l05`)
- DP_W s1000 (UNet 256-512-1024, batch 16, 82 000 bước ≈ 4 h; đo tốc độ 0,174 s/bước; VRAM 4,45 GB; `DP_REPLAN` = 32, DDPM 100 bước khi suy luận): **16/20** (collision 3, other 1), 111 s/lượt (ACT 136 s).
- So ACT_W s1000: mất 3, được 4, p = 1,0. So CL0_W (17/20): mất 3, được 4, p = 1,0.
- Bảng DEV `dev_C2` L0,5 (20 cảnh): CL0 7 < ACT 13–15 ≤ DP 16 ≤ CL0_W 17. Sau khi sửa bộ thực thi, pipeline mô-đun ngang chính sách học tốt nhất.
- Tiếp (`scripts/p6_queue.sh`, unit `arena-p6q`): ORACLE/ORACLE_W trên `dev_C2` L0,5 (n = 60), rồi DP_W s2000, s3000 (cùng công thức) + DEV.
- DP_W s2000 (cùng công thức): **13/20** (collision 7; `runs/p4_dev_dp_w_s2000_dev_c2_l05`). DP s1000 16, s2000 13 → trung bình 14,5/20, cùng mức ACT (13–15). Chênh giữa hạt giống (±1,5 lượt) cỡ chênh giữa phương pháp học.
