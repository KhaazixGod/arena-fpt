# KE_HOACH_PAPER: từ G2 NO-GO đến bài báo (nhánh `paper-dev`)

**Trạng thái.** Kế hoạch, 14/11/2026. Ngày 14/11 người dùng đồng ý hướng: sửa thầy → sinh demo mới → huấn luyện ACT và Diffusion Policy → TEST mới có tiền đăng ký.
Ngày 15/11 người dùng quyết (mục 5): duyệt `CL0_W`; chưa có hội nghị/tạp chí đích; TEST dùng lại tập vật TEST cũ; máy này chạy toàn bộ (robot thật dùng máy khác). P2 bắt đầu 15/11.
Bản đồ án đóng băng ở tag `thesis-freeze-2026-11-14`. Không sửa gì trong bản đó, không sửa `cl0/`.
Nhật ký chẩn đoán: `PAPER_NOTES.md`.

## 0. Vì sao (bằng chứng đã có)

| Sự kiện | Số | Bằng chứng |
|---|---|---|
| G2 (TEST, có tiền đăng ký): `test_C2`, L0,5 | ACT_I2 35% / 30% (hạt giống 1000 / 2000), CL0 37%, ORACLE 47% → NO-GO | `logs/2026-11-10_210822_g2_decision.txt` |
| Thầy của ACT_I2 là ORACLE, nhưng demo **chỉ ở L0 và L0,25** | 444 tập, `train_C0..C3` (`arrangements/sim_ext`), không có tập nào ở L0,5 | `runs/e6_demos_real/manifest.json` |
| Nhưng đã thử thêm demo L0,5 (E15, ACT_I2F: +76 tập ORACLE L0,5) | DEV: 50 so với 48 trên 80 lượt, p = 0,84 → **không khác**. Thêm demo tốc độ cao một mình không đủ | `PREREGISTRATION_G2.md` mục 2, `ARENA_SETUP_REPORT.md` E15 |
| Trần ORACLE trên vật huấn luyện | L0,5: 41/60 (68%); băng đứng yên: 50/60 | `runs/p1_oracle_train_c2_l05`, `runs/p1_slip_D_l0` |
| Cơ chế A: khớp cổ tay xoay chạm biên khi bám băng | 8/19 lượt hỏng, 1/41 lượt đạt, 0/60 ở L0 | `PAPER_NOTES.md` (P1b) |
| Cơ chế B: vật rộng, hàm kẹp va vào vật khi hạ | 3/19 lượt hỏng (`cyl12`) | `PAPER_NOTES.md` (P1b) |
| Thông số vật lý của kẹp không phải nguyên nhân | ma sát, ma sát xoắn, độ cao kẹp, tốc độ nhấc, mở rộng kẹp: không cải thiện | `PAPER_NOTES.md` (P1) |
| E18: thầy tốt (95%) → ACT đa nhiệm 72–76% | băng đứng yên | `PREREGISTRATION_E18.md`, `logs/2026-11-12_204650_e18_decision.txt` |

**Câu chuyện bài báo [đề xuất].** Trên băng chuyển động, học bắt chước bị chặn bởi chất lượng của thầy: một lỗi động học trong bộ thực thi cổ điển, và việc thiếu demo ở tốc độ kiểm tra. Ta sửa thầy, sinh lại demo, rồi so ACT và Diffusion Policy với baseline mô-đun trên một TEST mới có tiền đăng ký.

## 1. Luật

1. Không sửa tag đóng băng, `cl0/`, các sheet `locked/` cũ, các file tiền đăng ký đã commit.
2. Mã mới chỉ nằm trong `arena/` trên `paper-dev`. Phương pháp mới đăng ký tên mới (`ORACLE_W`, `CL0_W`, `DP_I2`), không thay các tên cũ.
3. Chỉ chỉnh trên sheet không khóa (`train_*`, `dev_*`), mỗi lần một thay đổi, ghép cặp với bản gốc, ghi vào `PAPER_NOTES.md`.
4. TEST mới dùng sheet hạt giống mới, băm và commit trong `PREREGISTRATION_PAPER.md` trước lượt TEST đầu tiên. Chỉ chạy khi người dùng ra lệnh (luật 5).
5. Mỗi chính sách học có ≥ 3 hạt giống. Báo cáo mọi kết quả, kể cả xấu.
6. Luật 1 vẫn áp dụng: không chạy Isaac song song với huấn luyện. Máy này dành cho sim và huấn luyện cả ngày lẫn đêm; robot thật dùng máy khác (người dùng, 15/11).

## 2. Các bước

### P2. Sửa thầy: `ORACLE_W` (và `CL0_W`)

- **W1** (thay đổi thuật toán; người dùng đã đồng ý hướng này ngày 14/11). Khi chọn mục tiêu, chọn nhánh góc kẹp θ hay θ+180° sao cho khớp cổ tay xoay còn khoảng trống lớn nhất trên cả đoạn bám dự kiến (APPROACH → HOLD, dự đoán góc quay đế theo tốc độ băng), rồi buộc bộ thực thi dùng nhánh đó. Mã ở `arena/methods/oracle_w.py`: lớp con của `YawFeasibleController` cộng một lớp con của `BeltExecutor` đặt trong `arena/`.
- **Kiểm:** `ORACLE_W` trên `train_C2`, 60 cảnh, L0,5, ghép cặp với bản gốc (41/60). Thêm L0 (gốc 50/60) để chắc không tụt.
- **Cổng [đề xuất]:** không còn lượt nào bị đóng băng lệnh khớp vì biên cổ tay; SR ở L0,5 ≥ 75% (45/60); SR ở L0 không giảm quá 2 lượt.
- **Nếu không đạt cổng:** thêm W3 cho vật rộng (chỉ hạ khi sai số bám nhỏ hơn khoảng hở còn lại của vật). Mỗi lần một thay đổi, tối đa 2 vòng. Sau đó dùng bản tốt nhất và ghi lại.
- **Xác nhận một lần** trên một sheet không dùng để chỉnh (`train_C3`, L0,5).
- **`CL0_W`** [người dùng duyệt 15/11, luật 8]: nhận thức của CL0 cộng đúng sửa W1. Đây là baseline mô-đun công bằng: chính sách học được hưởng thầy đã sửa thì baseline mô-đun cũng phải được. CL0 gốc vẫn giữ để nối với G2.
- **Thời gian:** viết mã 3–4 giờ; mỗi lần kiểm 60 cảnh khoảng 25 phút mỗi làn.
- **Kết quả 15/11 (`PAPER_NOTES.md` P2): đạt cổng.** `train_C2` L0,5: ORACLE 41/60 → ORACLE_W 49/60 (mất 0, được 8, p = 0,0078); L0: 50 → 52; nhịp giữ lệnh 1055 → 0. Chuỗi qua đêm `scripts/p2p3_chain.sh`: xác nhận `train_C3` + `CL0_W` trên `dev_C2` → chốt tự động → P3 demo → `ACT_W` ×3.

### P3. Demo mới

- `ORACLE_W` trên cùng sheet với E6 (`arrangements/sim_ext`, `train_C0..C3`, n = 70), ở L0, L0,25 và **L0,5**: 840 lượt. Giữ lượt thành công, chuyển bằng `to_lerobot_i2.py` → `runs/p3_demos_w/lerobot_i2`.
- Khoảng 6 giờ với 2 làn như E18 [ước lượng từ E6: render 0,074 s/khung].
- Ghi số tập theo tốc độ và theo loại vật.

### P4. Huấn luyện

- **`ACT_W`:** `train_act_i2.py`, cùng công thức ACT_I2 (100 000 bước, batch 8), hạt giống 1000/2000/3000. Khoảng 1,8 giờ mỗi hạt giống (đã đo: `act_i2_s2000`, `act_i2t_s1000`).
- **`DP_W` (Diffusion Policy, có sẵn trong LeRobot 0.6.1):**
  - Viết bộ huấn luyện I2 (hành động tương đối trong hệ băng, như `train_act_i2.py`) và `arena/methods/diffusion_i2.py` (2 khung quan sát, khử nhiễu DDIM khoảng 10 bước).
  - Siêu tham số (horizon, số bước hành động, cỡ ảnh, số bước huấn luyện) chọn **chỉ trên DEV** bằng một lần thử ngắn, có ghi lại.
  - Đo tốc độ huấn luyện 20 phút trước. Ước lượng 3–6 giờ mỗi hạt giống [chưa kiểm]. 3 hạt giống.
- **Ablation (chỉ mô tả):** `ACT_W_slow` huấn luyện trên tập con L0/L0,25 của demo mới, 1 hạt giống. Mục đích là tách hiệu ứng "sửa thầy" khỏi hiệu ứng "có thêm demo L0,5".
- **Kiểm đường ống trên DEV** (`dev_C2`, L0,5, n = 20) cho mỗi loại mô hình trước khi viết tiền đăng ký.
- **Cấu hình suy luận ACT** giữ như G2 (`ACT_REPLAN=0`, `ACT_COMMIT=0`) trừ khi DEV cho thấy khác. Chốt trước tiền đăng ký.
- **GPU:** khoảng 5,5 giờ (ACT) + 9–18 giờ (DP) + 1,8 giờ (ablation).

### P5. Tiền đăng ký và TEST mới

- **Sheet mới:** `python -m arena.arrangements --set sim --cell test_C2 --n 60 --seed <mới> --out locked/paper/...`, băm trong `PREREGISTRATION_PAPER.md`. Vật: tập vật TEST cũ (người dùng chốt 15/11), để so được với G2. Phải ghi rõ là kết quả theo từng vật của G2 đã được xem.
- **Phương pháp** (cùng 60 sắp xếp, ghép cặp): CL0, `CL0_W`, ORACLE, `ORACLE_W`, ACT_old (`act_i2_s1000`, `act_i2_s2000` có sẵn), `ACT_W` ×3, `DP_W` ×3, `ACT_W_slow` ×1.
- **Giả thuyết [đề xuất, chốt khi viết tiền đăng ký]:**
  - H1 (chính): `ACT_W` hơn baseline mô-đun mạnh nhất (`CL0_W` hoặc CL0, lấy cái mạnh hơn trên DEV) theo cấu trúc claim C của G2 (hiệu ≥ +15 điểm, McNemar chính xác p ≤ 0,05, SR ≥ 60%). Cách gộp 3 hạt giống chốt ở bước này; tôi sẽ đề xuất gộp theo từng sắp xếp để tăng công suất.
  - H2: `ACT_W` hơn ACT_old (hiệu ứng của thầy mới cộng demo L0,5).
  - H3 (phụ): `DP_W` so với `ACT_W`, kiểm hai phía.
  - Holm cho H1–H2. Mọi thứ còn lại là mô tả.
- **Ngưỡng SR tuyệt đối** phải đặt theo trần `ORACLE_W` đo trên sheet không khóa, trước TEST. Trên vật TEST, ORACLE chỉ đạt 47% ở G2, nên ngưỡng 60% có thể không với tới được.
- **Thời gian TEST:** khoảng 13–15 giờ với 2 làn (G2: ACT ~170 s/lượt, CL0 44 s, ORACLE 28 s; DP chưa đo).
- Chỉ chạy khi người dùng ra lệnh.

### P6. Phân tích và viết

Bảng kết quả chính, phân tích nguyên nhân hỏng, video, bản nháp bài báo.

### R. Robot thật (song song, kế hoạch riêng)

Hiệu chuẩn bắt đầu 16/11. Cần tiền đăng ký riêng. Còn chờ người dùng trả lời: cách hiệu chuẩn, và có thu demo bằng tay leader không.

## 3. Lịch dự kiến

| Ngày | Việc | Cần người dùng |
|---|---|---|
| 14/11 tối – 15/11 | P2: viết `ORACLE_W`, kiểm trên `train_C2` (L0,5 và L0) | Không (15/11 là hạn luận văn) |
| 16/11 | Cổng P2, xác nhận trên `train_C3`; `CL0_W`. Đêm: P3 sinh demo | Không |
| 17/11 | P3 xong, chuyển dữ liệu; DP: viết bộ chạy, đo tốc độ. Đêm: `ACT_W` ×3 | Không |
| 18/11 | DP: chọn siêu tham số trên DEV, rồi huấn luyện 3 hạt giống (GPU cả ngày lẫn đêm) | Không |
| 19/11 | Kiểm DEV mọi mô hình; viết tiền đăng ký; sinh và khóa sheet | Duyệt tiền đăng ký |
| 20/11 | TEST (khoảng 13–15 giờ) | Ra lệnh TEST |
| 21/11 | Phân tích, bảng, video | Không |

Robot thật: kết quả khoảng 22/11 (kế hoạch riêng). Lịch này chưa tính trễ; DP là phần rủi ro nhất.

## 4. Rủi ro

- W1 chỉ sửa nhóm A (8/19 lượt hỏng). Nếu sửa hết thì trần tối đa khoảng 82%; nhóm B và C vẫn còn.
- Vật TEST có đĩa mỏng (`plate`), loại chỉ có trong tập TEST, là nơi ORACLE hay hỏng vì điểm kẹp (G2: 10/25). Không chỉnh được trên vật này mà không rò rỉ TEST, nên trần trên TEST có thể vẫn thấp.
- DP chậm hơn dự kiến → DP còn 1 hạt giống và chỉ mô tả; ACT vẫn là chính sách chính.
- TEST mới vẫn không thấy lợi thế → báo cáo nguyên trạng, như đã làm với G2.
- `ACT_W` khác ACT_old ở hai chỗ (thầy và tốc độ demo). Ablation `ACT_W_slow` chỉ tách được một phần, và chỉ là mô tả.
- E15 đã cho thấy thêm 76 demo L0,5 từ thầy cũ không cải thiện ACT trên DEV. Nếu W1 chỉ sửa được ít lượt, `ACT_W` có thể không hơn ACT_old (H2 thất bại). Cách giảm rủi ro: kiểm `ACT_W` trên DEV trước khi viết tiền đăng ký; nếu không khác, báo cáo nguyên trạng và xem lại hướng.

## 5. Người dùng cần quyết

Đã quyết ngày 15/11:
1. `CL0_W`: **duyệt** (theo khuyến nghị).
2. Hội nghị hoặc tạp chí đích: **chưa có**. Lịch giữ như mục 3.
3. Tập vật TEST: **dùng lại tập vật TEST cũ**.
4. Máy: **máy này chạy toàn bộ**; robot thật dùng máy khác.

## 6. Khung (b): người dùng chốt ngày 16/11 (thay mục 2 P5 về giả thuyết)

**Câu chuyện.** Trên băng chuyển động, bộ thực thi cổ điển chọn nhánh góc kẹp (θ hay θ+180°) theo tính liên tục; vì khi kẹp thẳng đứng q5 = yaw + q1 − 177,2°, cổ tay xoay đúng bằng góc quay của đế khi bám vật, và nhánh gần nhất có thể chạm biên khớp. Lỗi này chi phối thất bại của pipeline mô-đun (CL0 37/60 lượt chạm biên trên DEV L0,5) và của thầy đặc quyền (ORACLE), nhưng gần như không chạm chính sách học (ACT 2/100 lượt DEV). W1 (chọn nhánh theo khoảng trống cổ tay dự báo trên cửa sổ bám) sửa nó: CL0 42% → 87% (DEV), ORACLE 68% → 82% / 58% → 73% (train_C2 / train_C3). Hệ quả: so sánh G2 "học ≈ mô-đun" bị lẫn bởi lỗi bộ thực thi; học bắt chước còn bị chặn bởi chất lượng thầy.

**Thí nghiệm (theo thứ tự hàng đợi `scripts/p5_queue.sh`, unit `arena-p5q`):**
1. Quét tốc độ trên DEV (`dev_C2`, ghép cặp): CL0 vs CL0_W, ORACLE vs ORACLE_W ở L1,0 (n = 60) và L0,25 (n = 30); L0,5 đã có. Dự đoán: hiệu ứng W1 tăng theo tốc độ (đế quay nhiều hơn mỗi lượt).
2. DEV ACT_old vs ACT_W ×3 (L0,5, n = 20).
3. DP_W hạt giống 1000 + DEV.
4. Ablation ACT_W_slow.
5. Tiền đăng ký `PREREGISTRATION_PAPER.md` + sheet TEST mới (hạt giống mới, vật TEST cũ), rồi TEST khi người dùng ra lệnh.

**Giả thuyết dự thảo (chốt khi viết tiền đăng ký, sau bước 1–2):**
- H1 (chính): CL0_W > CL0 trên TEST L0,5 (cùng 60 cảnh; McNemar chính xác một phía p ≤ 0,05; hiệu ≥ +15 điểm).
- H1b: ORACLE_W > ORACLE trên TEST L0,5 (cùng kiểm).
- H2 (phụ): ACT_W (gộp 3 hạt giống theo cảnh) > ACT_old trên TEST L0,5.
- H3 (mô tả hoặc kiểm, tùy kết quả bước 1): hiệu ứng W1 theo tốc độ (L0,25 / L0,5 / L1,0).
- Mô tả: so sánh học với mô-đun đã sửa; phân loại nguyên nhân hỏng; số nhịp giữ lệnh.
- Holm cho H1, H1b, H2.

**Thay đổi so với mục 2:** H1 cũ ("ACT_W hơn baseline mô-đun mạnh nhất") bỏ, vì CL0_W 87% trên DEV làm nó gần như chắc chắn thất bại. Báo cáo nó như so sánh mô tả.
