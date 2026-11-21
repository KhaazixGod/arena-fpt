# PREREGISTRATION_P8 — các bài báo tái hiện (P05, P07, P17, P19) trên TEST của đồ án

Trạng thái: **ĐÃ KHÓA** (§7) (viết 20/11/2026 ~02:30, trước khi có bất kỳ kết quả DEV nào của P8). Khóa ở §7 trước lượt TEST đầu tiên. Sau khi khóa chỉ được thêm vào §8.
File này không sửa và không thay `PREREGISTRATION_PAPER.md`, vốn đã khóa. P8 là phần mở rộng thăm dò của paper-dev.

## 1. Lý do và phạm vi
- Số của 4 bài báo trong đồ án (Bảng 2.2, 4.8, 4.9) lấy từ máy benchmark: Windows, mã 4963d40, hiệu chuẩn khác. Số đó chỉ có trên 40 lượt DEV ở L0 và L0,25. Ba bài là "component_only" chạy trên bộ thực thi CL0 còn lỗi W1, và chưa có số TEST nào.
- Người dùng yêu cầu dựng lại các bài báo trên máy này và chạy trên đúng TEST của đồ án (tin nhắn 20/11/2026).
- **Lệnh TEST** (luật 5): người dùng, 20/11/2026 khoảng 02:16: "sau khi lên kế hoạch xong thì chạy luôn nhé, t đi ngủ đây", sau khi kế hoạch gồm bước TEST đã được trình bày.

## 2. Phương pháp (đều là tái hiện của đồ án, không phải mã gốc của benchmark)
| Tên trong trials.csv | Là gì | Mã |
|---|---|---|
| P05_CNS, P05_CNS_W | Phần nhận thức của CNS (SIFT, FLANN, tỉ số 0,75, RANSAC 5 px, theo `hhcaz/CNS` commit 6b42138, MIT). Ghép ảnh mẫu và chuyển điểm gắp mẫu. | `ports/p05_cns.py` |
| P07_VITVS, P07_VITVS_W | Phần nhận thức của ViT-VS (DINOv2 ViT-S/14 lớp 11, ghép best-buddy). Cửa sổ băng được đưa về 518 px. | `ports/p07_vitvs.py` |
| P17_ODIL, P17_ODIL_W | ODIL bước 1 (FPFH + FGR + ICP của Open3D trên ảnh độ sâu lý tưởng). Ghép đám mây điểm mẫu và chuyển điểm gắp mẫu. | `ports/p17_odil.py` |
| REMOTE:P19_ACT_TE_S1000/2000/3000 | P19 = ACT của LeRobot theo đúng cấu hình `p19_act.yaml` của benchmark. Dùng checkpoint ACT_J0 (học trên 444 demo E6 của ORACLE, cùng thiết kế 480 lượt với benchmark) cộng temporal ensembling 0,01 và `n_action_steps` 1. Seed 3000 được huấn luyện ngày 20/11. | `arena/methods/act_lerobot.py` (`ACT_TE_COEFF`) |

- Ba bài nhận thức dùng chung bộ bám, chọn vật và thực thi của CL0, qua `arena/methods/ports.py` (YawFeasibleController, giống nhóm rgb/rgbd_perception của benchmark). Hậu tố `_W` thêm W1.
- **Ảnh mẫu** do REFCAP render: một vật nằm một mình trên băng đứng yên, kèm điểm gắp tốt đã lưu của vật, tức lựa chọn của ORACLE. Tập chính gồm vật train và dev (26 vật), giống benchmark; như vậy vật TEST là vật lạ với mọi phương pháp. Tập phụ "có mẫu vật TEST" (36 vật) chỉ dùng cho các lượt `_t` ở §3 và luôn được ghi nhãn là biết trước mẫu vật.

## 3. Dữ liệu và lượt chạy TEST
- Tờ: `locked/paper/test_C2.csv`, 60 cảnh (cùng tờ và cùng sha256 với P6), n = 60, mỗi (cảnh, tốc độ, phương pháp) một lượt.
- **L0,5 (chính):** P05_CNS_W, P07_VITVS_W, P17_ODIL_W, P05_CNS, P07_VITVS, P17_ODIL, P19 ba seed.
- **L0,25 (phụ):** cùng 9 lượt chạy trên, cộng ACT_W ba seed (suy luận như P6: `serve_i2`, ACT_REPLAN=0, ACT_COMMIT=0).
- **L0,5 với tập mẫu có vật TEST (nhãn riêng):** P05_CNS_W, P07_VITVS_W, P17_ODIL_W, ở `runs/p8_test_c2_l05_<tên>_t`.
- **Dùng lại lượt chạy P6** (cùng tờ, cùng máy): CL0_W và ACT_W ba seed ở L0,5; CL0_W ở L0,25. Điều kiện để ghép cặp hợp lệ là bước kiểm lặp lại ở §4.
- Thư mục: `runs/p8_test_c2_<l05|l025>_<tên>`. Chạy bằng `scripts/p8_test.sh` (cần CONFIRM_TEST=yes). Quyết định bằng `scripts/p8_decide.py`.

## 4. Cổng DEV (trước khi khóa; kết quả ghi ở §8)
1. Mỗi lượt chạy DEV của `scripts/p8_dev.sh` xong đủ lượt hợp lệ, `valid=0` ≤ 10%, và lỗi của bộ nhận diện (method_exception) dưới 5% số lượt.
2. CL0_W chạy lại trên dev_C2, L0,5, 20 cảnh đầu phải cho **cùng kết quả 20/20** với `runs/p2_cl0w_dev_c2_l05`. Nếu không, tức là môi trường đã đổi: dừng, không chạy TEST.
3. So với máy benchmark trên lưới P7 chỉ để mô tả, không phải điều kiện. Một bài được tái hiện mà đạt dưới 10% trên lưới P7 thì phải kiểm lỗi phần nối. Chỉ được sửa lỗi phần nối (không chỉnh thuật toán, không chỉnh ngưỡng theo kết quả DEV) rồi chạy lại DEV. Mọi thay đổi ghi vào §8.
4. Bài nào không qua mục 1 thì không chạy TEST và được ghi ở §8.

## 5. So sánh và luật quyết định (TEST, α = 0,05, hai phía)
**Họ F1 (chính, Holm trên 4 phép), L0,5:** ACT_W (gộp 3 seed) so với từng bài: P05_CNS_W, P07_VITVS_W, P17_ODIL_W, P19 (gộp 3 seed).
- Thống kê: hiệu trung bình theo cảnh của tỉ lệ thành công trung bình qua các seed (như H2 của P6). Kiểm định hoán vị dấu hai phía, 100 000 hoán vị, seed 0.
- "ACT_W hơn bài k" được ủng hộ khi bị bác bỏ sau Holm và d > 0. "Bài k hơn ACT_W" được ủng hộ khi bị bác bỏ sau Holm và d < 0.

**Họ F2 (phụ, Holm trên 3 phép), L0,5:** CL0_W so với P05_CNS_W, P07_VITVS_W, P17_ODIL_W. Cùng bộ thực thi, chỉ khác phần nhận thức. Dùng McNemar chính xác hai phía.

**Chỉ mô tả, không có claim:**
- tác động của W1 với từng bài (bài_W so với bài);
- mọi số ở L0,25, gồm ACT_W so với CL0_W ở L0,25 (câu hỏi về tốc độ băng);
- các lượt `_t`;
- P19 so với ACT_old (giao diện I2 so với J0 + TE, cùng bộ demo E6);
- khoảng Wilson 95%, nguyên nhân thất bại, ms/bước.

Không gộp số TEST mới với số của máy benchmark.

## 6. Luật chạy
- `valid=0` chỉ dành cho lỗi mô phỏng (luật 7). Ngoại lệ của bộ nhận diện hay server là thất bại của phương pháp.
- Lượt chạy nào có trên 10% `valid=0` thì dừng.
- Đã ra TEST thì không đổi mã, ảnh mẫu, ngưỡng hay checkpoint. Chạy lại chỉ để bù lượt `valid=0` (run_until tiếp tục chạy).

## 7. Khóa
```
lock_commit: edb331cd14b264bcdb15f737ff65b454d240d276
locked/paper/test_C2.csv: 29aa1c3beb50847f04f73918044256afe7c733d38d420b158b8bd7b5e142b4ca
act_j0_s1000: a52cd166c22826e484f88331bedf3287918cc84e605d6aea161d6475af298e84
act_j0_s2000: 948ea82e01760762aea7a65e07cdc4927a6faecf707a5c86f8a561cc3252944c
act_j0_s3000: e6c8dea7f0070df08675de03ac8b0f84e3b259902bee4b9fe2ddcaae75e5b09c
act_w_s1000: abd7cb0a154dc8a541fbb6a9bb03ce803e37e0abb1a8703ded41e9aa43f8115f
act_w_s2000: c07a917d9d125bca4f2e0585368c04d24400ca2b1743fb3bd2590894bf3cbb6c
act_w_s3000: 37d2e0d9e1ebf46a74e253696ddb8ae89ab1657386e786c9919be3324ec145a5
refs/train_dev: c2d7b9a3948609fdf5f61703631d7a29860c20dd78d398426ad35894261f1131
refs/testobj: 8e1fc3dc905c0d433f02f570bf7c307b98adcb3cd32c5e2d6079ec40030670b2
ports/common.py: 86559c608c49bd22a43b6b10e9973122efe0317bc14f2bb0df46a2a9b461fb14
ports/detector_server.py: 5ab912f7d171497a8b766b1b641c903807ac3cec169af45ad97b4432a254aa93
ports/p05_cns.py: d2aed5ae37d87766abe82bcde76e29b32e3c46200e0b64392a68412ccaf7e2a9
ports/p07_vitvs.py: 1abe5b65a8bdb74c3c2b37eee2405c7aaa6262b52e9338b62d49605ca5bceddf
ports/p17_odil.py: bcff4b479cf81f445b4b4076df1a5363c7ee0d5a6441309e34380d403f76d5df
arena/methods/ports.py: a72753a66c1011093f1f243370e13d5a801dfcb17d069407e3009d8f0a1bf0d2
arena/methods/act_lerobot.py: bce19a4363a96a0248b88d49c5aea913085cee0a7064e4f521164f7046834f3f
arena/methods/act_i2.py: 37b63ced1f4f67e0ff7c1acbeae5431bc64dfc47934e31df4ac4dc2d6dca55e9
scripts/p8_test.sh: 3daf13913529b74418fc488e0d3c34dfcaeee63e2a937888afb19a953c331d21
scripts/p8_decide.py: e5faa2ef2529970a88236521b2991199e9c753bc057f173bf7e95206ba7e241d
```
Khóa lúc 2026-11-20 11:25:56. Từ đây chỉ được thêm vào §8.

## 8. Sai lệch và kết quả DEV
### 8.1 Trước lượt chạy arena đầu tiên của các bộ nhận diện (20/11, trước mọi kết quả DEV có điểm số)
- Lần render ảnh mẫu đầu (`runs/p8_refs/run_train_dev`, 04:25) không ghi được ảnh nào. Nguyên nhân: REFCAP đếm cả các vật đỗ ngoài băng. Đã sửa ở commit 7cf068a để chỉ đếm vật trên băng và trong cửa sổ, render lại ở `runs/p8_refs/run2_*`. Lượt cũ được giữ.
- Mặt nạ của ảnh mẫu bị trống, vì ảnh độ sâu là inf ở chỗ không có vật. Đã sửa tỉ lệ và nới vùng tìm (7cf068a).
- P17 nâng điểm gắp lên ở độ sâu của mặt băng, vì pixel điểm gắp là điểm trên mặt băng (7cf068a).
- P05: số cặp khớp tối thiểu đổi từ 8 xuống 3, bằng mức tối thiểu của chính CNS (commit 014e8b6). Quyết định dựa trên ảnh mẫu, vì vật sim trơn chỉ có 0–20 điểm SIFT. Lượt chạy thử đầu `runs/p8_smoke_p05_w` (0/2, no_target) có thể đã dùng ngưỡng 8, vì server khởi động cùng lúc với lần sửa. Đã chạy lại ở `runs/p8_smoke2_p05_w` với ngưỡng 3: 0/2, nhưng có phát hiện và có thử gắp.

### 8.2 Kết quả DEV (`scripts/p8_dev.sh`, HEAD 014e8b6, 04:46 → 11:24 ngày 20/11; chỉ để mô tả)
Cổng §4: cả 16 lượt chạy DEV đủ lượt, 0 dòng valid=0, 0 ngoại lệ của bộ nhận diện. CL0_W trên dev_C2, L0,5, 20 cảnh cho **cùng kết quả 20/20** với `runs/p2_cl0w_dev_c2_l05` (17/20 cả hai). **Mọi phương pháp qua cổng.**

| Lưới P7 (40 lượt, L0 và L0,25; bài nhận thức không có W1) | Máy này | Máy benchmark |
|---|---|---|
| P05_CNS | 17/40 | 18/40 |
| P07_VITVS | 29/40 | 12/40 |
| P17_ODIL | 30/40 | 25/40 |
| P19, seed 1000 / 2000 / 3000 | 25 / 24 / 24 | 20/40 (một checkpoint của họ) |

| dev_C2, L0,5, 20 cảnh | Không W1 | Có W1 |
|---|---|---|
| P05_CNS | 7 | 11 |
| P07_VITVS | 8 | 13 |
| P17_ODIL | 7 | 15 |
| P19, seed 1000 / 2000 / 3000 | 2 / 2 / 2 | – |
| CL0_W | – | 17 |

Không có tham số, mã, ảnh mẫu hay checkpoint nào được đổi sau khi có các kết quả DEV này.

### 8.3 TEST (thêm sau khi khóa)
- `scripts/p8_test.sh` chạy theo đúng §3, từ 11:28 ngày 20/11 đến 11:26 ngày 21/11/2026, HEAD 1dcac88. Cả 24 lượt chạy đủ 60/60 lượt hợp lệ, 0 dòng valid=0. Không có sai lệch nào so với §3–§6.
- Quyết định: `logs/2026-11-21_112617_p8_decision.txt`, `runs/p8_test_decision.json`. Bằng chứng: commit cdc7f4f.
- `logs/2026-11-20_112706_p8_decision.txt` là file rỗng, sinh ra từ một lần chạy khô (DRY) của script bị dừng giữa chừng. Không có lượt TEST nào trong lần đó.
