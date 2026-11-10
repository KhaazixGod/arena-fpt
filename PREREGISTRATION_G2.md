# PREREGISTRATION_G2 — quy tắc ghi trước cho đánh giá TEST (claim C, C′)

**Trạng thái: bốn quyết định đã được người dùng xác nhận ngày 8/11/2026 ("như m đề xuất"); file có hiệu lực khi được commit, và phải commit trước lượt TEST đầu tiên (kể cả G0, mục 0).** Từ lúc commit không sửa nội dung; muốn đổi thì ghi "Sai lệch" ở cuối file, không viết đè.
Bốn quyết định: (1) chính sách chính là I2, không phải I2F (mục 2); (2) hạt giống 1000 là chính, hạt giống 2000 để lặp lại bằng điểm ước lượng (mục 3); (3) H4 chạy trên `dev_C0`, không dùng `seen_C0` (mục 5); (4) claim C so với CL0, và với CL-1 chỉ khi G0 rơi vào vùng mơ hồ (mục 0 và 2).
Chạy ô `test_*` vẫn cần lệnh riêng của bạn (luật 5, `arena/CLAUDE.md`, cờ `--allow-locked`). File này không phải lệnh đó.

## 0. G0: CL0 một mình, chạy trước (theo `KE_HOACH_HUONG_1.md` §4, "Quy tắc G0")

Chính sách học **không** tham gia G0, nên không rò rỉ. Cần lệnh `--allow-locked` riêng của bạn.
- Kiểm hệ thống: CL0 trên `seen_C0` (`arrangements/sim_seen/seen_C0.csv`, n = 20), L = 0,5, phải ≥ 80%. Dưới mức đó là lỗi kỹ thuật, không tính là chỗ trống; sửa rồi chạy lại.
- Ô quyết định: CL0 trên `test_C2_001..030`, L = 0,5, n = 30.
  - **GO** nếu thành công ≤ 70% (≤ 21/30) **và** ≥ 50% lượt hỏng do nhận thức/chọn điểm kẹp (`merge`, `seg_miss`, `grasp_point`).
  - **GO có điều kiện** nếu ≤ 70% nhưng < 50% lượt hỏng do nhận thức: sửa nguyên nhân gốc rồi chạy lại G0 **đúng một lần**.
  - **PIVOT** (hướng 4) nếu ≥ 85% (≥ 26/30).
  - **Mơ hồ** (giữa hai mức) → xây và chạy CL-1 ở cùng ô, áp lại quy tắc; baseline của claim C là cái mạnh hơn trong CL0 và CL-1.
- Mọi sửa CL0 sau G0 chỉ được phát triển và kiểm trên vật và sắp xếp DEV (luật 4), cần bạn đồng ý nếu đổi thuật toán (luật 8). Băm mới của CL0 ghi vào mục "Sai lệch". Không tinh chỉnh theo vật TEST.
- Lưu ý đã biết: trên DEV, CL0 hỏng chủ yếu vì `collision` và `slip` ở `dev_C2 L0.5`, không phải nhận thức. Nhiều khả năng G0 cho "GO có điều kiện" nếu TEST giống DEV `[chưa kiểm]`.

Nguồn: `../KE_HOACH_HUONG_1.md` §2 (claim, H3, H4, H4b), §3.5, §4 (G1b, G2, G3). Mẫu: quy tắc ghi trước của E16 (`scripts/e16_commit.sh`, `scripts/e16_pair.py`).

## 1. Bộ TEST vật lạ: dùng bộ đã sinh, KHÔNG sinh lại

`locked/test_C0.csv`, `test_C2.csv`, `test_C3.csv` (n = 60 sắp xếp mỗi ô, hạt giống 30 / 32 / 33, sinh ngày 29/10, commit `3677daa`). Chỉ gồm 10 vật `split=test`, không có trong train hay dev:
- lõm / quai: `u27`, `ring28`, `mug29`
- mỏng / dẹt: `plate30`, `plate31`
- tương phản thấp với băng: `box32`, `cyl33`
- vật lạ thường: `t34`, `box35`, `cyl36`

Lý do không sinh lại: bộ này có trước mọi công việc E14–E16 (ACT_I2, I2F, COMMIT). Sinh lại bây giờ làm mất đúng tính chất mà ghi trước cần có. Kiểm đến 8/11: không run nào trong `runs/` chạm ô `test_*`; `locked/` không đổi từ commit đầu.

Băm đóng băng (sha256):
```
bd4532ba65e0f437b8f0e52637d62199d006e48502a6a1f5d257a0d98fe26415  locked/test_C0.csv
7962f4ecdc9590f4af00e0d068860d8deb8d75b4acdf6b0939b08f13f4d28434  locked/test_C2.csv
b45da43457cab0b55d67d06b4fcfe7dbc06cf065f6c8e8abf7012109e8023ad8  locked/test_C3.csv
3d9e600afceacdc5dd931ffc2424afad61933416e567cc4fcf10aad6b4051baa  configs/objects_sim.csv
aa49c57deff0dab6408c48d9b0d0e5a1e3c2afea6590324aabf819ddaa418066  configs/objects_sim.json
```
Không có `test_C1` (kế hoạch không dùng).

## 2. Các phương pháp đóng băng

| Vai trò | Phương pháp | Cố định |
|---|---|---|
| Chính sách học (claim C) | **ACT_I2, lập kế hoạch lại 100 khung, không COMMIT** (`ACT_REPLAN=0` = `n_action_steps` của checkpoint = 100 khung, `ACT_COMMIT=0`; đúng cách `e16_repeat_r100` đã chạy) | huấn luyện chỉ bằng demo E6 (`runs/e6_demos_real`, 444 tập), 100 000 bước, batch 8; hạt giống **1000** (đã có) và **2000** (huấn luyện thêm, cùng công thức) |
| Baseline mô-đun | CL0 | `cl0_code_sha256` 006af1c9…, `arena.toml` sha 84497cab…, `scene.toml` sha 52f787bf…, calib 98d3aa21… (đúng manifest E16) |
| Trần / kiểm hệ thống | ORACLE | cùng cấu hình |
| So sánh giao diện (H4) | ACT_J0 | huấn luyện chỉ bằng demo E6, 100 000 bước, batch 8; hạt giống 1000 (đã có) và 2000 |

Băm checkpoint hạt giống 1000 (`model.safetensors`):
```
f3f08c7798a3baa02242c456c1bf826fe94c46eb368c8b148c081d489ff835b8  act_i2_s1000
a52cd166c22826e484f88331bedf3287918cc84e605d6aea161d6475af298e84  act_j0_s1000
```
Băm của hạt giống 2000 ghi vào đây **trước** lượt TEST đầu tiên: `act_i2_s2000: e23de1180e29e53a29f731cd787497f99998993d0716dc36e8b562002e989bc4`, `act_j0_s2000: 948ea82e01760762aea7a65e07cdc4927a6faecf707a5c86f8a561cc3252944c`.

**[ĐÃ XÁC NHẬN 8/11] Chọn I2, không chọn I2F.** I2F (thêm 76 demo L0.5) chỉ ghi được trong sim, không mang sang robot thật. Trên DEV hai bản này không khác (50 so với 48 trên 80 lượt, p = 0,84). I2F, nếu chạy, chỉ là phân tích độ nhạy (mục 6), không tham gia quyết định.

**[ĐÃ XÁC NHẬN 8/11] Giới hạn đã biết:** CL0 là baseline mô-đun duy nhất có trong arena này. Claim C so với CL0, không so với "baseline mô-đun mạnh nhất" nói chung (kế hoạch nêu CL-0 hoặc CL-1). CL-1 chỉ được xây khi G0 rơi vào vùng mơ hồ (mục 0); khi đó claim C so với cái mạnh hơn trong hai.

## 3. Quyết định chính: claim C

**Ô:** `test_C2`, L = 0,5 (75 mm/s), cả 60 sắp xếp. Mỗi sắp xếp chạy cho ACT_I2, CL0 và ORACLE (ghép cặp theo `arrangement_id`; thứ tự xen kẽ theo cột `first_method`).

Kết quả đo: thành công theo nhãn GT của arena (`label.success`), không dùng `fail_cause_auto` của ACT.

**GO (claim C được ủng hộ trong sim)** khi và chỉ khi **cả hai** đúng:
- (a) **Hạt giống 1000 (chính):** SR(ACT_I2) − SR(CL0) ≥ **+15 điểm**, McNemar chính xác hai phía **p ≤ 0,05**, và SR(ACT_I2) ≥ **60%**.
- (b) **Hạt giống 2000 (lặp lại):** hiệu ≥ **+15 điểm** và SR ≥ **60%** (điểm ước lượng; p chỉ báo cáo).

**[ĐÃ XÁC NHẬN 8/11] Cách gộp hai hạt giống.** Hạt giống 1000 là chính vì đã có và đã chỉ định trước khi thấy TEST; hạt giống 2000 chỉ để loại trường hợp may mắn một lần. (Phương án chặt hơn, yêu cầu p ≤ 0,05 ở cả hai, đã không chọn.)

**NO-GO** nếu không đạt (a) hoặc (b). Khi đó theo sơ đồ quyết định: báo cáo nguyên trạng và chuyển sang hướng 4 (arena làm testbed đối chứng). Không đổi ngưỡng, không đổi chính sách, không chọn lại hạt giống.

Ước lượng công suất [ước lượng thô, xấp xỉ chuẩn, giả định độc lập]: với n = 60 cặp, nếu chênh thật ≥ 30 điểm thì khả năng đạt (a) > 90%; nếu chỉ 20 điểm thì khoảng 60%. Kết quả DEV (+35 điểm) có thể lạc quan hơn thực tế.

## 4. Báo cáo bắt buộc (mô tả, không dùng để quyết định)

- `test_C0` và `test_C3`, L = 0,5, n = 30 (`test_C0_001..030`, `test_C3_001..030`): ACT_I2 (hạt giống 1000), CL0, ORACLE.
- Phân tách theo loại khó (lõm / mỏng / tương phản thấp / thường) của ô `test_C2`.
- Chế độ lỗi từ GT bằng `scripts/e16_failure_modes.py` (đóng kẹp vào chỗ trống, `partial_lift`, độ lệch ngang `db`).
- ORACLE trên `test_C2` L0.5: nếu < 70% thì ghi rõ ô bị giới hạn bởi hình học (như `dev_C3 L0.5`). Quy tắc GO vẫn chấm như trên.
- Wilson 95% mọi tỉ lệ; số lượt `valid=0` và nguyên nhân.

## 5. Claim phụ C′ (chạy trên DEV, KHÔNG dùng TEST)

**H4 (giao diện hệ băng).** `dev_C0`, L = 1,0, n = 30 (`dev_C0_001..030`), ACT_I2 so với ACT_J0, cùng CL0 và ORACLE làm ngữ cảnh.
- Ủng hộ H4 khi hạt giống 1000: hiệu ≥ **+15 điểm** và McNemar p ≤ 0,05, và hạt giống 2000 cùng dấu với hiệu ≥ +15.
- n = 30 chỉ thấy chênh khoảng ≥ 26–32 điểm (kế hoạch §2). Chênh nhỏ hơn: báo cáo là mô tả.
- **[ĐÃ XÁC NHẬN 8/11]** Dùng `dev_C0` thay `seen_C0` vì `seen_C0` chỉ có 20 sắp xếp. Đây là sai khác nhỏ so với kế hoạch G1b.
- **Giới hạn:** J0 khác I2 ở cả giao diện lẫn không gian hành động (khớp so với EE tương đối), nên H4 được thử như một gói, chưa tách thành phần.

**H4b (demo tĩnh dùng được cho băng chạy).** Hai lần huấn luyện cùng công thức (100 000 bước, batch 8, hạt giống 1000):
- `i2_static`: toàn bộ **221** tập thành công ở L0 của E6.
- `i2_moving`: **221** tập chọn ngẫu nhiên (hạt giống 7) từ **223** tập thành công ở L0.25.
- Đánh giá: `dev_C2`, L = 0,5, n = 30. Ủng hộ H4b khi SR(i2_static) ≥ **0,8** × SR(i2_moving). Báo cáo Wilson 95% của tỉ số.
- Ưu tiên thấp nhất; chạy cuối nếu còn thời gian.

## 6. Phân tích độ nhạy (không quyết định)

- ACT_I2F (checkpoint hiện có) trên `test_C2` L0.5, n = 60.
- Lặp lại quy trình `/100` với tiến trình máy chủ mới, để đo nhiễu (E16 đo được 3/20 lượt đổi kết quả).

## 7. Thứ tự chạy và kiểm soát

0. G0 (mục 0): CL0 một mình trên TEST, khi bạn ra lệnh `--allow-locked`. Cần commit file này trước bước này.
1. Huấn luyện hạt giống 2000 (I2, J0), rồi `i2_static` / `i2_moving` nếu làm H4b. **Không chạy Isaac song song huấn luyện** (luật 1: VRAM 8 GB).
2. Ghi băm checkpoint hạt giống 2000 vào mục 2, commit file này.
3. Chạy H4 và H4b trên DEV (không đụng TEST).
4. **TEST của chính sách học đặt cuối** (G0 của CL0 ở bước 0 là ngoại lệ), khi mọi thứ đã đóng băng và bạn ra lệnh `--allow-locked`.
5. Tối đa 2 làn Isaac song song, có watchdog như `e16_commit.sh`. Sự cố hạ tầng (E16: Isaac hết VRAM, segfault) chỉ được xử lý bằng chạy bù **cùng cấu hình** (như `e16_resume_c01.sh`), không đổi gì khác.
6. Lượt `valid=0` (chỉ lỗi mô phỏng, luật 7) chạy lại cùng sắp xếp, tối đa 2 lần; báo cáo số lần. Tỉ lệ `valid=0` > 10% thì dừng và sửa.

Từ lượt TEST đầu tiên trở đi **không** sửa chính sách, CL0, ngưỡng, sheet hay cách chấm. Nếu phát hiện lỗi sau khi thấy kết quả TEST: kết quả theo quy tắc này vẫn được báo cáo đầy đủ; bản sửa chạy riêng và gắn nhãn "post-hoc".

Chi phí ước lượng [thô]: khoảng 600 lượt (~144 s thật mỗi lượt ACT) và 3–5 lần huấn luyện (~2,5 giờ mỗi lần), tức 1,5–2 ngày máy, phần lớn chạy qua đêm.

## 8. Sai lệch (điền sau nếu có)

### Sai lệch 1 (9/11/2026, trước khi chạy bất kỳ lượt TEST của chính sách học): kiểm hệ thống G0

**Sự kiện.** G0 chạy ngày 8/11 (`logs/2026-11-08_223351_g0_decision.txt`): CL0 trên `seen_C0` L0.5 được 6/20 = 30% (< 80%, kiểm hệ thống không đạt theo mục 0); CL0 trên `test_C2` L0.5 được 10/30 = 33% [19, 51], lượt hỏng do nhận thức/điểm kẹp 2/20 = 10% (theo mục 0 là "GO có điều kiện").

**Thừa nhận quan điểm.** Người dùng chọn xử lý sai lệch này **sau khi đã thấy** 6/20 và 10/30, nên lựa chọn dưới đây không độc lập với kết quả; tiêu chí kiểm thay thế dưới đây được nêu trước khi chạy nó, nhưng được chọn có tham khảo số DEV đã biết (CL0 `dev_C0` L0.25 = 17/20, L0 = 12/20, `dev_C2` L0.5 = 6/20).

**Thay đổi so với mục 0.**
1. Kiểm hệ thống ≥ 80% **ở L0.5 không còn áp dụng**. Lý do giả thuyết: CL0 chậm với băng 75 mm/s (kể cả trên DEV), không nhất thiết là lỗi hiệu chuẩn `[chưa kiểm]`. Kiểm thay thế: CL0 trên `seen_C0` (`arrangements/sim_seen`, không phải ô khoá), **L0.25, n = 20, phải ≥ 16/20 (80%)**. Chạy một lần (`scripts/g0_syscheck_l025.sh`). Nếu < 16/20 thì tính là lỗi kỹ thuật thật, dừng và điều tra hiệu chuẩn (luật 4, trên DEV) trước G2, không viết lại tiêu chí. Nếu ≥ 16/20: hệ thống (camera, hiệu chuẩn, CL0 đóng băng) được coi là hoạt động, và con số 10/30 ở `test_C2` L0.5 được dùng như độ mạnh của CL0 ở ô đó.
2. Kết quả `test_C2` L0.5 (10/30, "GO có điều kiện") **không** dẫn tới sửa CL0 và chạy lại G0. Lý do: nguyên nhân chính là `slip` (9) và `collision` (8), tức điều khiển/tiếp xúc, không phải nhận thức; sửa chúng là đổi thuật toán CL0 (luật 8) và không kịp kiểm trên DEV trước 15/11. Baseline của claim C vẫn là **CL0 đóng băng, không đổi**. Giới hạn này sẽ được viết vào luận văn: "CL0 chưa phải baseline module hoá mạnh nhất có thể; thất bại chủ yếu ở bước gắp/điều khiển, không ở nhận thức".
3. Không xây CL-1 (mục 0 chỉ yêu cầu khi "mơ hồ"; G0 không rơi vào vùng đó).
4. Mục 3 (quy tắc GO/NO-GO cho claim C), mục 4–7 và mọi ngưỡng khác **không đổi**.

### Sai lệch 2 (9/11/2026): H4 không đo được

H4 (mục 5) chạy xong 9/11 (`logs/2026-11-09_*_h4_decision.txt`): cả 6 phương pháp, kể cả ORACLE, đạt 0/30 ở `dev_C0` L1.0. Không có chênh lệch nào để kiểm; theo quy tắc kết quả là "không được ủng hộ" nhưng thực chất là hiệu ứng sàn. Báo cáo như kết quả mô tả: "L = 1.0 (150 mm/s) vượt khả năng cả ORACLE trong sim hiện tại". Không chạy lại ở tốc độ khác trong khuôn khổ file này; nếu sau đó làm H4 ở L0.5 thì ghi riêng là thử nghiệm post-hoc.

### Sai lệch 3 (10/11/2026): kiểm hệ thống thay thế không đạt; kết quả điều tra (chưa có quyết định về G2)

- Kiểm thay thế (Sai lệch 1): CL0 `seen_C0` L0.25 = **14/20 = 70%**, dưới ngưỡng 16/20 đã ghi trước (`logs/2026-11-09_*_g0_syscheck_l025.txt`, `runs/g0_syscheck_seen_c0_l025`, 0 lượt không hợp lệ). Lượt hỏng: `collision` 3, `slip` 3. Ngưỡng không bị hạ.
- Điều tra (`scripts/g0_investigate.sh`, ô không khoá, 0 lượt không hợp lệ): ORACLE trên cùng `seen_C0` đạt **18/20 ở L0.25 và 18/20 ở L0.5** (`runs/g0inv_oracle_seen_c0_l025`, `runs/g0inv_oracle_seen_c0_l05`; cả 2 lượt hỏng là `slip`). Vậy mô phỏng, bộ thực thi gắp và tốc độ băng 75 mm/s **không** là trần: khoảng cách đến CL0 (14/20 ở L0.25, 6/20 ở L0.5) nằm ở phần nhận thức/định thời của CL0.
- Phân tích 14 lượt hỏng của CL0 `seen_C0` L0.5 (`runs/g0_seen_c0`, trường `details`): 8/14 lượt có `max_lift_target_mm = 0` (cánh tay không nhấc được vật) với sai số ước lượng vị trí nhỏ (1–7 mm), gán nhãn `timing` 3 và `other` 5 (+1 `other` khác); 2/14 là `ring20` với sai số chọn điểm ~20 mm (nhãn `calib`); 3/14 `slip`. Đọc: CL0 thường **đến chậm** một vật đang chạy, không phải sai vị trí. Đây là nhận định `[chưa kiểm]`: chưa đo độ trễ của CL0 và chưa so với dấu thời gian.
- Kết luận kỹ thuật tạm: không thấy lỗi mô phỏng hay hiệu chuẩn chung; thấy điểm yếu của CL0 ở băng chuyển động. Theo chữ của mục 0 đây vẫn là "không đạt"; việc có chạy G2 hay không là quyết định của người dùng, ghi vào Sai lệch 4.
