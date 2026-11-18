# PREREGISTRATION_PAPER: TEST mới cho bài báo, khung (b)

**Trạng thái.** Có hiệu lực từ commit `lock_commit` ghi ở mục 7, ngày 18/11/2026, **trước lượt TEST đầu tiên**.

- Bản nháp viết ngày 16/11. Người dùng duyệt nguyên bản và ra lệnh chạy TEST ngày 18/11: "còn câu hỏi gì thì hãy hỏi, nếu ko thì chạy đi".
- Lúc khóa chỉ thêm những phần bản nháp đã hẹn: sheet và mã băm (mục 1, 7), hai script (mục 6), cách tính p và quy tắc đọc dữ liệu (mục 4, 5). Giả thuyết, ngưỡng, ô chạy và phương pháp giữ nguyên.
- Từ commit này không sửa file. Muốn đổi thì ghi vào mục 8 "Sai lệch".
- Lệnh chạy: `CONFIRM_TEST=yes bash scripts/p6_test.sh` (luật 5).

**Khung (người dùng chốt 16/11).** Kết quả chính: lỗi chọn nhánh cổ tay của bộ thực thi trên băng chuyển động và cách sửa W1 (`arena/wrist_branch.py`). ACT và DP là baseline học; H2 là câu hỏi phụ.

**Đã biết trước khi viết (công khai trong bài báo).** Mọi số dưới đây là sheet không khóa (`PAPER_NOTES.md`):

| So sánh | Sheet, tốc độ | Thành công |
|---|---|---|
| ORACLE → ORACLE_W | `train_C2` L0,5 | 41 → 49/60 |
| | `train_C3` L0,5 | 35 → 44/60 |
| | `dev_C2` L0,5 | 45 → 58/60 |
| | `dev_C2` L0,25 | 27 → 29/30 |
| | `dev_C2` L1,0 | 0 → 0/60 |
| CL0 → CL0_W | `dev_C2` L0,5 | 25 → 52/60 |
| | `dev_C2` L0,25 | 24 → 26/30 |
| | `dev_C2` L1,0 | 0 → 0/60 |

Trên 20 cảnh `dev_C2` L0,5: ACT_old 15, ACT_W 15/15/13, ACT_W_slow 15, DP_W 16/13/16, ORACLE 16, ORACLE_W 19, CL0 7, CL0_W 17.

Kết quả G2 trên `locked/test_C2.csv` (cùng tập vật) đã được xem, kể cả theo từng vật (ORACLE yếu ở đĩa mỏng `plate`). W1 không được chỉnh trên vật hay sheet TEST nào.

## 1. Sheet TEST mới

- **Lệnh sinh (chạy 18/11/2026):** `python -m arena.arrangements --set sim --cell test_C2 --n 60 --seed 1611 --out locked/paper/test_C2.csv`. Hạt giống 1611 được chọn trước khi sinh.
- **Nội dung:** 60 sắp xếp, 212 vật (28 cảnh 3 vật, 32 cảnh 4 vật). Dùng đúng 10 vật của tập TEST cũ (`configs/objects_sim.csv`, split test).
- **Sheet cũ không dùng lại.** `locked/test_C2.csv` (G2) không dùng lại.
- **Mã sắp xếp trùng tên sheet cũ** (`test_C2_001`…) nhưng nằm ở thư mục khác. Mọi phân tích chỉ đọc các thư mục `runs/p6_test_*`.
- **Dòng đầu của sheet ghi dải vật khác sheet cũ.** Sheet mới ghi dải [155, 255] mm của `configs/scene.toml` hiện tại; sheet cũ ghi [130, 230].
  - Toạ độ trong sheet là tương đối với dải ảo 120 mm. Lúc chạy, chúng được đặt vào cảnh theo `scene.toml` (`arena/arrangements.py`, `to_placements`).
  - `scene.toml` là cùng một file ở G2, ở mọi lượt DEV và ở TEST này (sha256 `52f787bf…`, ghi trong `manifest.json`).
- **Mã băm:** mục 7.

## 2. Phương pháp (đóng băng tại `lock_commit`)

| Tên | Định nghĩa | Ghi chú |
|---|---|---|
| CL0 | baseline gốc (`cl0/`, đóng băng) | như G2 |
| CL0_W | CL0 + W1 (`arena/methods/oracle_w.py`) | người dùng duyệt 15/11 |
| ORACLE | CL-0 + nhận thức GT + khả thi theo yaw | trần, đặc quyền |
| ORACLE_W | ORACLE + W1 | thầy mới |
| ACT_old s1000, s2000 | `act_i2_s1000`, `act_i2_s2000` (demo E6 của ORACLE) | checkpoint của G2, băm trùng `PREREGISTRATION_G2.md` |
| ACT_W s1000, s2000, s3000 | cùng công thức, demo P3 của ORACLE_W | 100 000 bước |
| DP_W s1000, s2000, s3000 | Diffusion Policy I2, UNet (256, 512, 1024), batch 16, 82 000 bước | chỉ mô tả |
| ACT_W_slow s1000 | ACT_W chỉ trên demo L0/L0,25 | ablation, chỉ mô tả |

**Suy luận** (như mọi lượt DEV):

- ACT như G2: `ACT_REPLAN=0`, `ACT_COMMIT=0`.
- DP: `DP_REPLAN` = n_action_steps (32); số bước khử nhiễu mặc định của checkpoint (100).
- Tham số W1 cố định: cửa sổ 4,0 s, bắt đầu 0,5 s, khoảng an toàn 10°.

**Mã:** `arena_sha256` ở mục 7, tính trên `arena/**/*.py` và `configs/*`, gồm `arena.toml`, `scene.toml` và `objects_sim.*`.

- Đây đúng là mã của mọi lượt DEV từ 16/11: ACT/DP DEV, ORACLE DEV L0,5, quét tốc độ.
- W1 không đổi từ commit 8364cbb (15/11).
- Mã CL-0 (`cl0_code_sha256`), USD và hiệu chuẩn: mục 7.

## 3. Ô chạy

- **Chính:** `test_C2` × **L0,5**, n = 60, mọi phương pháp ở mục 2, cùng 60 sắp xếp (ghép cặp).
- **Phụ (mô tả, H3):** `test_C2` × **L0,25**, n = 60, chỉ CL0, CL0_W, ORACLE, ORACLE_W.
- **L1,0 không chạy:** trên DEV mọi phương pháp đều 0/60 do tầm với (`late`), không phải do cổ tay.

## 4. Giả thuyết và quy tắc quyết định

Holm–Bonferroni trên H1, H1b, H2 ở α = 0,05 (gia đình 3 phép kiểm).

- **H1 (chính): CL0_W > CL0** ở L0,5. Kiểm McNemar chính xác một phía trên 60 cặp. Được ủng hộ khi p ≤ ngưỡng Holm **và** SR(CL0_W) − SR(CL0) ≥ +15 điểm.
- **H1b: ORACLE_W > ORACLE** ở L0,5. McNemar chính xác một phía. Được ủng hộ khi p ≤ ngưỡng Holm và hiệu ≥ +5 điểm.
- **H2 (phụ): ACT_W khác ACT_old** ở L0,5.
  - Với mỗi sắp xếp i: d_i = (trung bình thành công của ACT_W trên 3 hạt giống) − (trung bình của ACT_old trên 2 hạt giống).
  - Kiểm hoán vị dấu hai phía trên d_i: đảo dấu ngẫu nhiên 100 000 lần, hạt giống 0.
  - Được ủng hộ (theo hướng ACT_W tốt hơn) khi p ≤ ngưỡng Holm và trung bình d > 0.
  - DEV gợi ý không khác; vẫn kiểm và báo cáo nguyên trạng.
- **Cách tính, cố định trong `scripts/p6_decide.py`** (commit cùng file này):
  - McNemar một phía: p = P[X ≥ số cặp phương pháp _W thắng | n = số cặp khác kết quả, ½].
  - H2: T = trung bình d_i. Dùng 100 000 vector dấu `numpy.random.default_rng(0).integers(0, 2, (100000, 60)) * 2 − 1`. p = (1 + #{|T*| ≥ |T|}) / 100 001, tính đúng trên 6·d_i (số nguyên).
  - Holm bước xuống; p bằng nhau thì xếp theo tên.
- **Không tham gia quyết định (mô tả):**
  - SR và Wilson 95% của mọi phương pháp.
  - CL0_W so với ACT_W (gộp) và DP_W.
  - ACT_W_slow.
  - L0,25 (H3).
  - Nguyên nhân hỏng (`fail_cause_auto`).
  - Số nhịp giữ lệnh và số lượt đổi nhánh của W1.

## 5. Lượt hợp lệ

- **`valid=0` chỉ vì lỗi mô phỏng** (luật 7). Chạy bù cùng cấu hình đến đủ 60 lượt hợp lệ.
- **Lượt treo của Replicator** (bộ canh giữ diệt) không ghi kết quả và được chạy lại như mọi lần chạy khác.
- **Tỉ lệ `valid=0` > 10%** trên các dòng của một lần chạy thì dừng và hỏi:
  - Chuỗi ghi `runs/p6_test_STOP`.
  - Cả hai làn dừng trước lần chạy kế tiếp.
- **Mỗi sắp xếp lấy lượt hợp lệ đầu tiên.** Lượt hợp lệ thứ hai (nếu có) chỉ được báo là cảnh báo.
- **Khi nào `p6_decide.py` không in quyết định:**
  - Thiếu sắp xếp nào ở ô nào.
  - Có dòng sai phương pháp, ô hay tốc độ.
  - `manifest.json` không khớp mục 7: sheet, `arena_sha256` của mọi lần thử, mã CL-0, USD, hiệu chuẩn.

## 6. Thứ tự chạy và kiểm soát

**Chuỗi `scripts/p6_test.sh`** (commit cùng file này). Trước khi chạy, nó kiểm:

- `CONFIRM_TEST=yes`.
- File này và các file đóng băng đã commit, không có sửa cục bộ, không đổi so với `lock_commit`. Các file đóng băng là `arena/`, `configs/`, `remote_server.py`, sheet, `scripts/lib_chain.sh` và hai script P6.
- Băm sheet khớp mục 7.
- Băm mọi checkpoint khớp mục 7, cả trọng số lẫn toàn bộ thư mục `pretrained_model` (gồm thống kê chuẩn hoá).
- Không có huấn luyện hay Isaac khác đang chạy.

`DRY=1` kiểm các điều trên và in kế hoạch mà không chạy gì.

**Hai làn:**

- **Làn A** (phương pháp render ảnh, một Isaac mỗi lúc): CL0, CL0_W (L0,5) → ACT_old s1000, s2000, ACT_W s1000, s2000, s3000 → DP_W s1000, s2000, s3000, ACT_W_slow s1000 → CL0, CL0_W (L0,25).
- **Làn B** (ORACLE không render, chạy song song với làn A như bản nháp cho phép): ORACLE, ORACLE_W (L0,5) → ORACLE, ORACLE_W (L0,25).

**Mỗi lần chạy:**

- Thư mục `runs/p6_test_c2_<l05|l025>_<tên>`.
- Bộ canh giữ như DEV (`run_until`): tối đa 30 lần thử; không tiến triển quá 360 s thì diệt và chạy tiếp.
- Máy chủ ACT/DP khởi động lại tối đa 3 vòng nếu lần chạy chưa đủ.

**Ước lượng:** khoảng 25 giờ máy cho làn A (ACT ~136 s/lượt, DP ~111 s, CL0 ~65 s). Làn B (ORACLE ~30 s/lượt, ~2 giờ) chạy song song.

**Phân tích:** `scripts/p6_decide.py test` ghi `logs/*_p6_decision.txt` và `runs/p6_test_decision.json`.

- `scripts/p2_compare.py` cho số nhịp giữ lệnh và số lượt đổi nhánh (mô tả).
- `p6_decide.py selftest` tính lại số DEV: CL0 25 → CL0_W 52, ORACLE 45 → ORACLE_W 58.
- Trong lúc TEST chạy, chỉ xem tiến độ bằng `p6_decide.py status`. Lệnh này đếm lượt hợp lệ, không đếm thành công.

## 7. Băm

`lock_commit` là commit chứa sheet, hai script và mã ở trên. Nó được ghi vào file này ở commit ngay sau.

```
lock_commit: 248c7e845150c182d348bda065a3e23b7ab2fb2f
locked/paper/test_C2.csv: 29aa1c3beb50847f04f73918044256afe7c733d38d420b158b8bd7b5e142b4ca
configs/objects_sim.csv: 3d9e600afceacdc5dd931ffc2424afad61933416e567cc4fcf10aad6b4051baa
configs/objects_sim.json: aa49c57deff0dab6408c48d9b0d0e5a1e3c2afea6590324aabf819ddaa418066
arena_sha256: 0603069a3f229b3efe824d32cd6e8faa873dee85425802ee71b4909eca1a402d
cl0_code_sha256: 006af1c9686621e93249f7b2d17cf3e5cfd60ee96862213e13d000ddce63ab12
usd_sha256: b3c6b01c5eeebc9cde74a6161e521aff36d6c305b84deda1aba4aa09c7bf91de
calib_sha256: 98d3aa2170c502ec07e50b5580d84fa5e6b853146d362860d4ace3e6b33cbac1
background_sha256: 65b8ac38ee8c84f9104efc6f11cb05df9fd504f6c5e2382b72548b6513c66b52
act_i2_s1000: f3f08c7798a3baa02242c456c1bf826fe94c46eb368c8b148c081d489ff835b8
act_i2_s2000: e23de1180e29e53a29f731cd787497f99998993d0716dc36e8b562002e989bc4
act_w_s1000: abd7cb0a154dc8a541fbb6a9bb03ce803e37e0abb1a8703ded41e9aa43f8115f
act_w_s2000: c07a917d9d125bca4f2e0585368c04d24400ca2b1743fb3bd2590894bf3cbb6c
act_w_s3000: 37d2e0d9e1ebf46a74e253696ddb8ae89ab1657386e786c9919be3324ec145a5
act_w_slow_s1000: 97fec9039fc7d79f4c31a52bd69e5df4b89a11fdb307ea9edfe989bbd0a5b695
dp_w_s1000: 737d09ccd963a151b6be4ca4a1161f27c74372602a834389582e3b22153d0d3e
dp_w_s2000: 88b47f6aea835c4f9077f45dbbc58a1b2c7f16388c5c8567b76ddd948fed997a
dp_w_s3000: 0ad63bf645a4f4548a0115958166861e3ff7615a9150ed7a2c130e60a0f59ef9
act_i2_s1000/pretrained_model: 13e5deff9b82fae4446c774adb50034a0dfbabd33f420c097e247c40680ba91b
act_i2_s2000/pretrained_model: 47952f820fcea06dd55fd0d678b6d0f78a1d2da82703e0185e5b7edc2e56c244
act_w_s1000/pretrained_model: d2a9d87195b3bc21cf6922064467a766a231613a26eff2ebb0a7981a2ab69d54
act_w_s2000/pretrained_model: cbc4b42ac4b8939095decffee652d12a0504ab7a72005887c76f1140f1765613
act_w_s3000/pretrained_model: aafed8ce7a9c89e0814764b4901d84c7cbd71c87713d6816af71511dd7a9eb40
act_w_slow_s1000/pretrained_model: 8702e7f0875c6e79003576738e23a2b4563ddda0466e7e4375f1b979ce57e203
dp_w_s1000/pretrained_model: 5932755f5ac50b1783d93dc8c0960ad77a9813dd87f883965d7a09e83e79ce1d
dp_w_s2000/pretrained_model: 094b26a7c60e55a4152bbbe10039edc69890f5e34f21a00583caf9c939ba9a37
dp_w_s3000/pretrained_model: 0f4bf3f4abad140795fb4c12239fae78049a77414787471aee56c669321f5dc5
```

Checkpoint là `runs/<tên>/checkpoints/last/pretrained_model`:

- Dòng `<tên>:` là sha256 của `model.safetensors`.
- Dòng `<tên>/pretrained_model:` là sha256 của danh sách `sha256sum` mọi file trong thư mục, xếp theo tên.

Môi trường lúc khoá: Isaac Sim 6.0.0.1, NVIDIA GeForce RTX 3070 Ti 8 GB, `engine=isaac`.

## 8. Sai lệch

_(chưa có)_
