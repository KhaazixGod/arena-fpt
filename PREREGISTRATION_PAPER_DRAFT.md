# PREREGISTRATION_PAPER (BẢN NHÁP, chờ người dùng duyệt): TEST mới cho bài báo, khung (b)

**Trạng thái.** Nháp ngày 16/11/2026, chưa có hiệu lực. Khi người dùng duyệt: sửa theo ý kiến, đổi tên thành `PREREGISTRATION_PAPER.md`, sinh và băm sheet (mục 1), điền băm checkpoint và commit mã (mục 2), commit **trước lượt TEST đầu tiên**. Từ lúc đó không sửa; muốn đổi thì ghi vào mục 8 "Sai lệch". File này không phải lệnh chạy TEST (luật 5: cần lệnh riêng của người dùng, `CONFIRM_TEST=yes`, `--allow-locked`).

**Khung (người dùng chốt 16/11).** Kết quả chính: lỗi chọn nhánh cổ tay của bộ thực thi trên băng chuyển động và cách sửa W1 (`arena/wrist_branch.py`). ACT và DP là baseline học; H2 là câu hỏi phụ.

**Đã biết trước khi viết (công khai trong bài báo).** Mọi số dưới đây là sheet không khóa (`PAPER_NOTES.md`): ORACLE → ORACLE_W 41 → 49/60 (`train_C2` L0,5), 35 → 44/60 (`train_C3`), 45 → 58/60 (`dev_C2` L0,5), 27 → 29/30 (`dev_C2` L0,25), 0 → 0/60 (`dev_C2` L1,0); CL0 → CL0_W 25 → 52/60 (`dev_C2` L0,5), 24 → 26/30 (L0,25), 0 → 0/60 (L1,0); ACT_old 15/20, ACT_W 15/15/13, ACT_W_slow 15/20, DP_W s1000 16/20 trên 20 cảnh `dev_C2` L0,5. Kết quả G2 trên `locked/test_C2.csv` (cùng tập vật) đã được xem, kể cả theo từng vật (ORACLE yếu ở đĩa mỏng `plate`). W1 không được chỉnh trên vật hay sheet TEST nào.

## 1. Sheet TEST mới

- `python -m arena.arrangements --set sim --cell test_C2 --n 60 --seed 1611 --out locked/paper/test_C2.csv` (tập vật TEST cũ: `configs/objects_sim.csv`, split test; hạt giống 1611 chọn trước, chưa sinh). Sheet cũ `locked/test_C2.csv` (G2) không dùng lại.
- Mã sắp xếp trùng tên với sheet cũ (`test_C2_001`…) nhưng ở thư mục khác; mọi phân tích chỉ đọc các thư mục `runs/p6_test_*`.
- Băm sha256 điền khi khóa: `locked/paper/test_C2.csv`, `configs/objects_sim.csv`.

## 2. Phương pháp (đóng băng tại commit khóa)

| Tên | Định nghĩa | Ghi chú |
|---|---|---|
| CL0 | baseline gốc (`cl0/`, đóng băng) | như G2 |
| CL0_W | CL0 + W1 (`arena/methods/oracle_w.py`) | người dùng duyệt 15/11 |
| ORACLE | CL-0 + nhận thức GT + khả thi theo yaw | trần, đặc quyền |
| ORACLE_W | ORACLE + W1 | thầy mới |
| ACT_old s1000, s2000 | `act_i2_s1000`, `act_i2_s2000` (demo E6 của ORACLE) | checkpoint của G2 |
| ACT_W s1000, s2000, s3000 | cùng công thức, demo P3 của ORACLE_W | băm: `PAPER_NOTES.md` |
| DP_W | Diffusion Policy I2, UNet (256, 512, 1024) | số hạt giống tùy thời gian; chỉ mô tả |
| ACT_W_slow s1000 | ACT_W chỉ trên demo L0/L0,25 | ablation, chỉ mô tả |

Suy luận ACT như G2 (`ACT_REPLAN=0`, `ACT_COMMIT=0`); DP: `DP_REPLAN` = n_action_steps (32), số bước khử nhiễu mặc định của checkpoint. Tham số W1 cố định: cửa sổ 4,0 s, bắt đầu 0,5 s, khoảng an toàn 10°.

## 3. Ô chạy

- Chính: `test_C2` × **L0,5**, n = 60, mọi phương pháp ở mục 2, cùng 60 sắp xếp (ghép cặp).
- Phụ (mô tả, H3): `test_C2` × **L0,25**, n = 60, chỉ CL0, CL0_W, ORACLE, ORACLE_W.
- L1,0 không chạy: trên DEV mọi phương pháp đều 0/60 do tầm với (`late`), không phải do cổ tay.

## 4. Giả thuyết và quy tắc quyết định

Holm–Bonferroni trên H1, H1b, H2 ở α = 0,05 (gia đình 3 phép kiểm).
- **H1 (chính): CL0_W > CL0** ở L0,5. Kiểm McNemar chính xác một phía trên 60 cặp. Được ủng hộ khi p ≤ ngưỡng Holm **và** SR(CL0_W) − SR(CL0) ≥ +15 điểm.
- **H1b: ORACLE_W > ORACLE** ở L0,5. McNemar chính xác một phía. Được ủng hộ khi p ≤ ngưỡng Holm và hiệu ≥ +5 điểm.
- **H2 (phụ): ACT_W khác ACT_old** ở L0,5. Với mỗi sắp xếp i: d_i = (trung bình thành công của ACT_W trên 3 hạt giống) − (trung bình của ACT_old trên 2 hạt giống). Kiểm hoán vị dấu hai phía trên d_i (đảo dấu ngẫu nhiên, 100 000 lần, hạt giống 0). Được ủng hộ (theo hướng ACT_W tốt hơn) khi p ≤ ngưỡng Holm và trung bình d > 0. DEV gợi ý không khác; vẫn kiểm và báo cáo nguyên trạng.
- Không tham gia quyết định (mô tả): SR và Wilson 95% của mọi phương pháp; CL0_W so với ACT_W (gộp) và DP_W; ACT_W_slow; L0,25 (H3); nguyên nhân hỏng (`fail_cause_auto`); số nhịp giữ lệnh và số lượt đổi nhánh của W1.

## 5. Lượt hợp lệ

`valid=0` chỉ vì lỗi mô phỏng (luật 7); chạy bù cùng cấu hình đến đủ 60 lượt hợp lệ. Lượt treo của Replicator (bộ canh giữ diệt) không ghi kết quả và được chạy lại như mọi lần chạy khác. Tỉ lệ `valid=0` > 10% thì dừng và hỏi.

## 6. Thứ tự chạy và kiểm soát

- Chuỗi `scripts/p6_test.sh` (viết khi khóa): kiểm `CONFIRM_TEST=yes` và file tiền đăng ký đã commit; một Isaac mỗi lúc cho các phương pháp render ảnh; ORACLE/ORACLE_W có thể chạy song song với một làn khác.
- Thứ tự: CL0, CL0_W, ORACLE, ORACLE_W (L0,5) → ACT_old ×2, ACT_W ×3 → DP_W, ACT_W_slow → ô L0,25.
- Ước lượng: khoảng 25 giờ máy (ACT ~136 s/lượt, CL0 ~65 s, ORACLE ~30 s).
- Phân tích: `scripts/p6_decide.py` (viết và commit cùng tiền đăng ký, trước TEST).

## 7. Băm (điền khi khóa)

```
locked/paper/test_C2.csv: ...
configs/objects_sim.csv: ...
commit paper-dev: ...
act_w_s1000: abd7cb0a154dc8a541fbb6a9bb03ce803e37e0abb1a8703ded41e9aa43f8115f
act_w_s2000: c07a917d9d125bca4f2e0585368c04d24400ca2b1743fb3bd2590894bf3cbb6c
act_w_s3000: 37d2e0d9e1ebf46a74e253696ddb8ae89ab1657386e786c9919be3324ec145a5
dp_w_*, act_w_slow_s1000: ...
```

## 8. Sai lệch

_(chưa có)_
