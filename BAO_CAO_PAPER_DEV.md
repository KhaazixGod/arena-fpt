# Báo cáo: kết quả nhánh `paper-dev` (14–18/11/2026)

Ngày 18/11/2026, 14:30.
- Mọi số là mô phỏng (`engine=isaac`, Isaac Sim 6.0.0.1, RTX 3070 Ti 8 GB). Không có số của robot thật.
- Các số dưới đây lấy trên sheet huấn luyện và DEV, **không phải kết quả TEST**. TEST mới đang chạy (mục 8).
- Mỗi số được tính lại từ `trials.csv` lúc viết báo cáo. Đường dẫn tương đối với `arena/`.

## 1. Kết luận

1. **Tìm ra một lỗi của bộ thực thi CL-0 trên băng chuyển động và đã sửa nó (W1).**
   - Khi tay bám vật, khớp cổ tay xoay quay theo khớp đế đúng 1:1 rồi chạm biên khớp. Lệnh khớp bị giữ đứng yên rồi giật từng nấc 3°, nên tay ngừng bám vật.
   - W1 chọn trước nhánh góc kẹp (θ hay θ + 180°) sao cho cổ tay còn khoảng trống cho cả đoạn bám.
2. **W1 tăng thành công rõ ở L0,5 trên mọi sheet đã thử:**
   - ORACLE: 41 → 49/60 (`train_C2`), 35 → 44/60 (`train_C3`), 45 → 58/60 (`dev_C2`), không mất lượt nào.
   - CL0: 25 → 52/60 (`dev_C2`), mất 2, được 29.
3. **Hiệu quả phụ thuộc tốc độ băng.**
   - L0,25: nhỏ, +2/30.
   - L0,5: lớn.
   - L1,0: mọi phương pháp đều 0/60, vì vật ra khỏi tầm với trước khi kịp kẹp. Đây không phải lỗi cổ tay.
4. **Sau khi sửa, pipeline mô-đun ngang hoặc hơn chính sách học trên DEV** (20 cảnh): CL0_W 17/20, ACT 13–15/20, Diffusion Policy 13–16/20. ACT và DP thất bại chủ yếu do va chạm và gần như không gặp lỗi cổ tay.
5. **Thầy đã sửa không giúp học sinh trên DEV (H2).** ACT_W được 15/15/13 (3 hạt giống), ACT_old được 15/20.
6. **Kết quả G2 của đồ án (ACT ≈ CL0) có thể bị lẫn bởi lỗi này** [suy luận]. Trên DEV, lỗi chạm CL0 rất nặng nhưng hầu như không chạm ACT. TEST mới sẽ kiểm điều này.
7. **TEST mới đã khóa tiền đăng ký và đang chạy** từ 14:12 ngày 18/11, khoảng 25 giờ.

## 2. Bối cảnh và thuật ngữ

- **Đồ án đóng băng ở tag `thesis-freeze-2026-11-14`.** G2 (TEST có tiền đăng ký, `test_C2`, L0,5, n = 60) cho ACT_I2 35% / 30% (hạt giống 1000 / 2000), CL0 37%, ORACLE 47% → NO-GO (`logs/2026-11-10_210822_g2_decision.txt`).
- **Khung bài báo (b), bạn chốt 16/11.** Kết quả chính là lỗi cổ tay và W1. ACT và DP là baseline học. H2 (thầy tốt hơn có giúp học sinh không) là câu hỏi phụ.
- **Tốc độ băng.** L = v·τ/w. L0,25 = 37,5 mm/s, L0,5 = 75 mm/s, L1,0 = 150 mm/s.
- **Các phương pháp:**

| Tên | Nghĩa |
|---|---|
| CL0 | Baseline mô-đun gốc: nhận thức từ ảnh + bộ thực thi CL-0 (đóng băng). |
| ORACLE | Cùng bộ thực thi, nhận thức bằng sự thật mô phỏng (GT). Là trần của pipeline mô-đun. |
| `_W` | Thêm W1 (`CL0_W`, `ORACLE_W`). |
| ACT_old | ACT_I2 của G2: thầy ORACLE, demo chỉ ở L0 và L0,25. |
| ACT_W | Cùng công thức ACT, demo của ORACLE_W, có thêm L0,5. |
| ACT_W_slow | Ablation: ACT_W chỉ học demo L0 và L0,25. |
| DP_W | Diffusion Policy, cùng dữ liệu với ACT_W. |

## 3. Cơ chế lỗi

- **Thông số vật lý của kẹp không phải nguyên nhân.** Trần của ORACLE trên `train_C2` L0,5 là 41/60. Đã đổi ma sát, ma sát xoắn, độ cao kẹp, tốc độ nhấc và độ mở kẹp, mỗi lần một thứ: không thông số nào làm tăng tỉ lệ thành công. Băng đứng yên thì đạt 50/60 (`PAPER_NOTES.md` P1).
- **Hình học.** Với kẹp thẳng đứng, góc trục khép = −q1 + q5 + 177,21° (q1 = khớp đế, q5 = cổ tay xoay). Công thức đúng tuyệt đối theo FK, đã kiểm trên 1026 tư thế.
- **Lỗi xảy ra thế nào:**
  1. Khi bám vật ở L0,5, khớp đế quay 20–50° mỗi lượt và cổ tay quay đúng bằng chừng đó.
  2. IK của CL-0 khớp góc theo mod 180°. Nhánh góc kẹp do lệnh trước quyết định, không tính đoạn bám sắp tới.
  3. Cổ tay tới biên −157,2° (cộng 3° an toàn) thì IK nhanh thất bại.
  4. Lệnh bị giữ 10 nhịp rồi nhảy 3°. Tay ngừng bám, vật trôi thêm 30–50 mm.
- **Bằng chứng.** Lỗi có ở 8/19 lượt hỏng của ORACLE (`train_C2` L0,5), chỉ 1/41 lượt đạt, và 0/60 lượt khi băng đứng yên (`PAPER_NOTES.md` P1b).
- **CL0 chịu nặng hơn ORACLE nhiều.** CL0 nhắm góc 90–130°, nên nhánh gần nhất đẩy cổ tay về phía âm. Trên `dev_C2` L0,5, 37/60 lượt có lệnh bị giữ ở biên cổ tay, `ik_fail` 18.
- **ACT gần như không gặp lỗi này.** Chỉ 2/100 lượt DEV có cổ tay chạm biên khi IK hỏng (`PAPER_NOTES.md` P2).

## 4. W1

- **Cách làm.** Lúc chọn vật, W1 dự báo các khớp trên cửa sổ bám 0,5–4,0 s.
  - Vị trí vật được dự báo theo tốc độ lệnh của băng và dốc tăng tốc 200 mm/s².
  - Dự báo cho mọi nhánh θ + 180k (quay tối đa 270°), dùng IK không chặn cổ tay.
  - W1 giữ nhánh gần nhất của CL-0, trừ khi cổ tay dự báo vào trong 10° quanh biên. Khi đó nó chọn nhánh vi phạm muộn nhất, và bộ thực thi bám đúng nhánh đã chọn.
- **Những gì không đổi.** Không đổi nhận thức, cách chọn vật hay thông số nào. Lượt không đổi nhánh chạy đúng mã CL-0.
- **Mã và chi phí.** Mã ở `arena/wrist_branch.py` và `arena/methods/oracle_w.py`. Lập kế hoạch mất trung vị 195 ms mỗi lượt.
- **Nguồn tham số.** Tham số (4,0 s; 0,5 s; 10°) đọc từ log `train_C2`, không chỉnh thêm. Vì vậy p trên `train_C2` chỉ là bằng chứng thăm dò. `train_C3` và `dev_C2` là các sheet xác nhận.
- **Lỗi đã sửa trong lúc làm.** Bản v1 dùng tốc độ băng đo được lúc chọn vật, khi băng còn đang tăng tốc (khoảng 25/75 mm/s). Vì thế nó chỉ đổi nhánh 1 lượt thay vì 16. Bản v2 dùng tốc độ lệnh cộng dốc tăng tốc.

## 5. Kết quả của W1 (ghép cặp trên cùng cảnh, McNemar chính xác hai phía)

| Sheet, tốc độ | Phương pháp | Gốc → W1 | Mất / được | p | Bằng chứng |
|---|---|---|---|---|---|
| `train_C2` L0,5 | ORACLE | 41 → **49**/60 | 0 / 8 | 0,0078 | `runs/p1_oracle_train_c2_l05`, `runs/p2_oraclew2_train_c2_l05` |
| `train_C2` L0 | ORACLE | 50 → 52/60 | 0 / 2 | 0,50 | `runs/p1_slip_D_l0`, `runs/p2_oraclew2_train_c2_l0` |
| `train_C3` L0,5 | ORACLE | 35 → **44**/60 | 0 / 9 | 0,0039 | `runs/p2_oracle_train_c3_l05`, `runs/p2_oraclew_train_c3_l05` |
| `dev_C2` L0,5 | ORACLE | 45 → **58**/60 | 0 / 13 | 0,0002 | `runs/p5_oracle_dev_c2_l05`, `runs/p5_woracle_dev_c2_l05` |
| `dev_C2` L0,5 | CL0 | 25 → **52**/60 | 2 / 29 | 5·10⁻⁷ | `runs/p2_cl0_dev_c2_l05`, `runs/p2_cl0w_dev_c2_l05` |
| `dev_C2` L0,25 | ORACLE | 27 → 29/30 | 0 / 2 | 0,50 | `runs/p5_oracle_dev_c2_l025`, `runs/p5_woracle_dev_c2_l025` |
| `dev_C2` L0,25 | CL0 | 24 → 26/30 | 0 / 2 | 0,50 | `runs/p5_cl0_dev_c2_l025`, `runs/p5_wcl0_dev_c2_l025` |
| `dev_C2` L1,0 | ORACLE | 0 → 0/60 | 0 / 0 | 1 | `runs/p5_oracle_dev_c2_l10`, `runs/p5_woracle_dev_c2_l10` |
| `dev_C2` L1,0 | CL0 | 0 → 0/60 | 0 / 0 | 1 | `runs/p5_cl0_dev_c2_l10`, `runs/p5_wcl0_dev_c2_l10` |

- **Lệnh khớp bị giữ khi bám (tổng số nhịp):**
  - ORACLE `train_C2` L0,5: 1055 → 0.
  - ORACLE `train_C3`: 1563 → 72, trong đó không nhịp nào ở biên cổ tay.
  - CL0 `dev_C2`: 5053 → 188; số lượt bị giữ ở biên cổ tay 37 → 0.
  - Log: `logs/2026-11-15_171325_p2_gate_compare.txt`, `logs/2026-11-15_184802_p2_confirm_compare.txt`, `logs/2026-11-16_143831_p5_sweep_compare.txt`, `logs/2026-11-17_014138_p6_oracle_dev_l05_compare.txt`.
- **Trên `train_C2` và `train_C3`, mọi lượt ORACLE mà W1 không đổi nhánh cho kết quả giống hệt bản gốc**, vì mô phỏng tất định. Phần tăng chỉ đến từ các lượt W1 đổi nhánh.
- **Ở L1,0 thất bại là `late`.** Vật đi khoảng 315 mm trước khi tay kịp hạ nên ra khỏi tầm. Điều này giải thích H4 của G2 (0/30 ở L1,0 cho mọi phương pháp).

## 6. Demo và huấn luyện

- **Demo ORACLE_W.** 840/840 lượt hợp lệ, 677 tập thành công: L0 229/280, L0,25 233/280, L0,5 215/280 (`runs/p3_demos_w_a`, `runs/p3_demos_w_b`). Dữ liệu ở `runs/p3_demos_w/lerobot_i2`, 171 834 khung. So với E6 của G2: 444 tập, không có tập L0,5 nào.

| Mô hình | Dữ liệu | Công thức | Thời gian |
|---|---|---|---|
| ACT_W s1000, s2000, s3000 | 677 tập | ACT I2, 100 000 bước, batch 8, chunk 100 | ~2,25 giờ / hạt giống |
| ACT_W_slow s1000 | 462 tập L0/L0,25 | như trên | ~2,25 giờ |
| DP_W s1000, s2000, s3000 | 677 tập | Diffusion Policy I2, UNet (256, 512, 1024), batch 16, 82 000 bước, DDPM 100 bước | ~4 giờ / hạt giống |

- **Kích thước UNet của DP.** UNet mặc định (512, 1024, 2048) hết 8 GB VRAM ở batch 16, nên dùng bản nhỏ hơn. Đây là quyết định do phần cứng, chốt trước khi có kết quả DP nào.
- **Log và băm.** Log huấn luyện ở `logs/*_train_act_w_*.log` và `logs/*_train_dp_w_*.log`. Băm checkpoint ở `PREREGISTRATION_PAPER.md` mục 7.

## 7. Tất cả phương pháp trên DEV (`dev_C2_001..020`, L0,5, cùng 20 cảnh)

| Phương pháp | Thành công | Lỗi | Bằng chứng |
|---|---|---|---|
| CL0 | 7/20 | collision 7, timing 3, slip 3 | `runs/p2_cl0_dev_c2_l05` |
| ACT_old s1000 | 15/20 | collision 5 | `runs/p4_dev_act_old_s1000_dev_c2_l05` |
| ACT_W s1000 / s2000 / s3000 | 15 / 15 / 13 | collision 4 / 5 / 6, other 1 / 0 / 1 | `runs/p4_dev_act_w_s*_dev_c2_l05` |
| ACT_W_slow s1000 | 15/20 | collision 5 | `runs/p4_dev_act_w_slow_s1000_dev_c2_l05` |
| DP_W s1000 / s2000 / s3000 | 16 / 13 / 16 | collision 3 / 7 / 4, other 1 / 0 / 0 | `runs/p4_dev_dp_w_s*_dev_c2_l05` |
| ORACLE | 16/20 | timing 2, collision 2 | `runs/p5_oracle_dev_c2_l05` |
| **CL0_W** | **17/20** | collision 2, timing 1 | `runs/p2_cl0w_dev_c2_l05` |
| **ORACLE_W** | **19/20** | timing 1 | `runs/p5_woracle_dev_c2_l05` |

- **20 cảnh nên khoảng tin cậy rộng** (khoảng ±20 điểm). Chênh lệch giữa các hạt giống (13–16) cỡ chênh lệch giữa các phương pháp học. Bảng này dùng để kiểm pipeline; quyết định nằm ở TEST.
- **Thầy đã sửa và demo L0,5 không tạo khác biệt trên DEV.** ACT_W s1000 so với ACT_old s1000: mất 3, được 3. ACT_W_slow cũng 15/20. Điều này khớp với E15 trước đây.
- **Không có lượt `valid=0` nào** trong mọi lần chạy của `paper-dev` (P1–P5).

## 8. TEST mới (đang chạy)

- **Tiền đăng ký.** `PREREGISTRATION_PAPER.md`, khóa ở commit `248c7e8`. Bạn duyệt nguyên bản ngày 18/11.
  - Sheet mới `locked/paper/test_C2.csv`: 60 cảnh, hạt giống 1611, 10 vật TEST cũ.
  - Mã, checkpoint và sheet đều có băm. Mã TEST trùng mã của mọi lượt DEV từ 16/11.
- **Giả thuyết.** Holm trên 3 phép kiểm, α = 0,05.

| | Giả thuyết | Ngưỡng |
|---|---|---|
| H1 (chính) | CL0_W > CL0 ở L0,5 | McNemar một phía, và hiệu ≥ +15 điểm |
| H1b | ORACLE_W > ORACLE ở L0,5 | McNemar một phía, và hiệu ≥ +5 điểm |
| H2 (phụ) | ACT_W khác ACT_old | hoán vị dấu hai phía trên trung bình hạt giống |

  DP, ablation, so sánh học với mô-đun và ô L0,25 chỉ để mô tả.
- **Đang chạy.** Unit `arena-p6test`, bắt đầu 14:12 ngày 18/11, dự kiến xong khoảng 15:00 ngày 19/11.
  - Lúc 14:24 đã có CL0 11/60 và ORACLE 20/60 lượt hợp lệ, 0 lượt `valid=0`. Chỉ đếm số lượt, chưa xem tỉ lệ thành công.
  - Khi xong, quyết định tự in ra `logs/*_p6_decision.txt`.

## 9. Sự cố và cách xử lý

- **Isaac treo khi ghi demo hai làn song song.** Bộ render của Replicator (`orchestrator.step`) treo, GPU 0%.
  - Cách xử lý: chạy một Isaac mỗi lúc. Bộ canh giữ lấy stack rồi chạy lại. Không sửa đường render.
  - Các chuỗi DEV ngày 16–17/11 không có lượt treo nào.
- **Chuỗi P3 lỡ chuyển 146 tập demo dở dang.** Đã dừng và để riêng các tập đó, không dùng. Đã thêm bước kiểm đủ số lượt trước khi chuyển.

## 10. Hạn chế

- **Chỉ có mô phỏng**, chưa có robot thật.
- **W1 chỉ áp cho bộ thực thi CL-0.** Bộ thực thi của ACT và DP giữ nguyên như G2.
- **DEV của chính sách học chỉ có 20 cảnh**, và ACT_old trên DEV chỉ có 1 hạt giống.
- **Ở L1,0 mọi phương pháp thất bại do tầm với và thời gian.** Một cách sửa ứng viên (W2, kiểm khả thi lúc chọn vật khi băng còn tăng tốc) chưa làm. Đó là thay đổi logic chọn vật nên cần bạn duyệt.
- **"G2 bị lẫn bởi lỗi cổ tay" vẫn là suy luận** từ DEV, chờ TEST mới.

## 11. Việc bạn cần làm

1. Không cần làm gì cho TEST. Tôi sẽ báo quyết định khi chạy xong (~15:00 ngày 19/11).
2. Nếu muốn tiền đăng ký có dấu thời gian kiểm chứng được, hãy bảo tôi đẩy `paper-dev` lên `origin`. Nên làm trước khi có kết quả TEST. Hiện chưa đẩy.
3. Sau TEST: chọn hội nghị hoặc tạp chí đích (hiện chưa có), để bản thảo viết theo đúng khuôn.
