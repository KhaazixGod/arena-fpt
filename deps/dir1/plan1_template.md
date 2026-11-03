# KẾ HOẠCH HƯỚNG 1: chính sách học từ ảnh cho vật lạ, xếp lộn xộn, trên băng chuyền (SO-101)

Cập nhật 27/10/2026 · bản nháp để bạn chỉnh · **chưa có số đo nào trên robot thật** · các bảng thống kê và ngân sách sinh ra từ `stats_tables.py` (chạy lại được); số trong các bảng tài liệu lấy từ trang nguồn; số toy lấy từ `KE_HOACH_THAM_DO.md`. Từ 26/10 có thêm mã CL-0 + bộ thực thi hệ băng (thư mục `cl0/`, xem §3.4 và Phụ lục A): kiểm trong mô phỏng và với thiết bị giả, **chưa chạy trên phần cứng nào**.

Chú thích: `[đã kiểm]` = mình đã mở trang nguồn (nói rõ mức: tóm tắt hay toàn văn) · `[chưa kiểm]` = chưa đọc/đo · `[giả định]` = số mình đặt để tính, bạn sửa được · `[ước lượng]` = mình đoán, không phải dữ liệu.

---

## 0. Kết luận trước

1. **Hướng này làm gì.** Thay chuỗi mô-đun "tách vật → ước lượng pose → theo dõi → dự đoán → chọn điểm kẹp" bằng một chính sách học từ ảnh, nhắm đúng chỗ chuỗi đó yếu: **vật chưa từng thấy** và **nhiều vật sát nhau (clutter)**. Diffusion không còn là đóng góp chính; nó là một trong ba lớp chính sách được so (ACT, DP, MIP) ở mục 3.3.
2. **Claim cần chứng minh, và có thể sai:** ở ô *vật lạ × clutter vừa (C2)*, chính sách học (dùng giao diện hệ quy chiếu băng) có tỉ lệ nhặt thành công **cao hơn baseline mô-đun đã tinh chỉnh công bằng ≥ 15 điểm**, ghép cặp theo sắp xếp, n = 60 cặp.
3. **Chỗ trống trong tài liệu** (mức tóm tắt): hai bài 2026 gần nhất (ForeTime-VLA trên băng chuyền, DynamicVLA trên vật lăn/ném) chỉ so với chính sách học khác, không có baseline cổ điển. Bài mạnh nhất cho vật di động trong clutter (Chen et al. 2025) là phương pháp ít huấn luyện, và không so với phương pháp nào khác. Mình **chưa tìm thấy** bài so chính sách học từ ảnh với baseline mô-đun mạnh trên băng chuyền với vật lạ trong clutter. "Chưa thấy" không có nghĩa "chưa ai làm".
4. **Rủi ro lớn nhất:** baseline cổ điển đã đủ tốt ở tốc độ băng và độ lộn xộn của bạn, khi đó không còn claim. Vì vậy cổng đầu tiên **G0** đo đúng điều này trên SO-101 thật: {{G0_TR|0}} lượt ≈ {{G0_H|1}} giờ robot, chưa kể thời gian dựng baseline.
5. **Mình đoán (chủ quan, `[ước lượng]`):** G0 cho thấy có chỗ trống ~{{P_H1|0}}%; học đạt ≥ 70% ở việc cơ bản ~{{P_H2|0}}%; học vượt cổ điển ≥ 15 điểm khi hai điều trên đúng ~{{P_H3|0}}%. Nhân lại, **claim mạnh đủ cả chuỗi chỉ ≈ {{P_CHAIN|0}}%**. Phần còn lại không vô ích: nếu cổ điển đủ tốt, hoặc cổ điển hỏng mà học chưa đuổi kịp, vẫn viết được bài đối chứng (hướng 4) trên cùng hạ tầng. Tạp chí Q3 của bạn có nhận kiểu bài đó không thì mình không biết.
6. **Việc đầu tiên, rẻ nhất, quyết định nhất:** điền và đo các mục ở §3.1 → hiệu chuẩn và chạy thử CL-0 (mã đã viết 26/10, xem `cl0/README_CL0.md`) → tinh chỉnh ≤ 2 ngày trên vật dev → đóng băng mã + cấu hình CL-0 và tiêu chí (§5) → chạy G0.
7. **Bạn có tay leader SO-101 (xác nhận 26/10), nên nhánh thu dữ liệu là nhánh T** (§4.1); nhánh S giữ làm phương án dự phòng.

Điều mà toy trước đã và chưa nói được: toy cho thấy chính sách học tụt mạnh khi băng nhanh (0,20 m/s: DP 55,0%, BC 55,6% so với 96,5% của cổ điển có bộ lọc + luật điều khiển), và DP ngang hồi quy cùng mạng (+0,8 điểm, khoảng [−0,6; +2,3]). Toy **không có ảnh, không có clutter, không có vật lạ**, nên nó không cung cấp bằng chứng cho H1 đến H3 bên dưới; nó chỉ gợi ý động cơ cho giao diện hệ quy chiếu băng (H4) và mức kỳ vọng cho H5.

---

## 1. Định vị so với tài liệu

Tất cả ở **mức tóm tắt** (trang abstract hoặc bản HTML, qua công cụ đọc trang); mình chưa tự đọc toàn văn bài nào (công cụ đọc trang trả về bản tóm tắt), các con số dưới đây cần đối chiếu bản gốc trước khi đưa vào bài viết. Riêng Bảng I của Chen et al. mình đã lấy hai lần và hai lần khớp nhau.

| Nguồn | Bối cảnh và phương pháp | Số đáng chú ý | Liên quan tới mình |
|---|---|---|---|
| **Chen, Kiyokawa, Wan, Harada 2025** ([2502.05916](https://arxiv.org/abs/2502.05916)) | UR5e + Robotiq 2F-140 + RealSense D435 **gắn tay**; vật lạ (YCB) di động trong clutter dày trên băng; so khớp tương đồng, ít huấn luyện | băng 5,5 và 11,0 cm/s; 3 mẫu clutter (P1 3 vật giống nhau, P2 3 vật khác nhau, P3 5 vật khác nhau). **SR** (thành công trên mỗi lần kẹp đã thực hiện) 57–94%, trung bình 78–86% ở 5,5 cm/s và 64–75% ở 11,0 cm/s; **ER** (tỉ lệ vật mục tiêu mà robot thực sự thử kẹp) 60–100%. **Không so phương pháp nào khác** (chỉ ablation). Mã nguồn: không nêu | Phương pháp gần nhất về bài toán. Nhân hai trung bình (SR×ER, ước tính của mình) ra ≈ 55–73% vật mục tiêu được nhặt ở 5,5 cm/s và ≈ 54–72% ở 11,0 cm/s: ngay cả một phương pháp thiết kế riêng, có depth, phần cứng tốt, cũng chỉ nhặt được khoảng 55–73% vật mục tiêu trong clutter dày. Ô C2 của mình nhẹ hơn và phần cứng khác, nên chỉ là mốc về độ lớn |
| **ForeTime-VLA 2026** ([2608.20735](https://arxiv.org/abs/2608.20735)) | băng chuyền, π0.5 + chưng cất token tương lai; hộp/ngô/dưa hấu; 458 tập | băng chậm: 58,9% (53/90) so với π0.5 36,7%; chỉ một băng, một nền tảng. Baseline đều là chính sách học | Một chính sách học lớn trên băng chuyền thật đạt 81,1% khi vật đứng yên và 58,9% khi băng chậm; không có baseline cổ điển nên không biết con số đó cao hay thấp |
| **DynamicVLA 2026** ([2601.22153](https://arxiv.org/abs/2601.22153)) | Franka/PiPER; vật **lăn/ném** trên bàn (không phải băng chuyền); VLA 0,4B; 2K tập thật thu bằng demonstrator tự động (EfficientTAM + tam giác hóa) | tác giả nêu không có sai số hay kiểm định ý nghĩa; lợi ích phụ thuộc backbone trễ thấp | Mẫu cho nhánh thu demo không cần leader arm (§4.1, nhánh S) |
| **GG-CNN** ([1804.05172](https://arxiv.org/abs/1804.05172)) | tổng hợp điểm kẹp theo từng pixel của ảnh **depth**, 50 Hz | 83% vật lạ đối kháng, 88% vật bị dịch khi kẹp, 81% clutter động | Baseline "mô-đun có học" hợp lý nếu camera có depth (CL-2, §3.4); không phải băng chuyền |
| **Yamamoto et al. 2023** ([2309.12547](https://arxiv.org/abs/2309.12547)) | băng chuyền, CNN-LSTM, kéo giãn thời gian demo chậm để ra tốc độ/vị trí chưa dạy | 100% ở vị trí và tốc độ chưa dạy trong thí nghiệm của họ; một vật; kém khi màu rất khác | Là hướng 2 của lần trước; ở đây chỉ dùng như bối cảnh |
| **GAP-RL** ([2410.03509](https://arxiv.org/abs/2410.03509)), **KARL** ([2506.15945](https://arxiv.org/abs/2506.15945)) | RL cho kẹp vật động; KARL = Kalman + RL, camera gắn tay | abstract không có số | KARL là hướng "lai học + bộ lọc cổ điển". Không phải băng chuyền eye-to-hand |
| **DCDP** ([2603.01953](https://arxiv.org/abs/2603.01953)), **RTC** ([2506.07339](https://arxiv.org/abs/2506.07339)) | sửa độ trễ/cảnh động cho DP và flow policy, không cần huấn luyện lại | DCDP +19% thích nghi (PushT động), thêm ~5% tính toán | Dùng được như tiện ích; không phải claim của mình |
| **Much Ado About Noising** ([2512.01809](https://arxiv.org/abs/2512.01809)) | lợi thế của chính sách sinh đến từ **tính toán lặp có giám sát bước giữa**, không phải đa mode; MIP (hồi quy 2 bước) ngang flow | khoảng cách còn lại chủ yếu ở tác vụ cần độ chính xác cao | Reviewer sẽ đòi baseline MIP, nên MIP có trong §3.3 |
| **ABB Conveyor Tracking** ([datasheet](https://library.e.abb.com/public/51c0fc4c87a036f6c1257b1300579b96/Data%20sheet%20Conveyor_tracking.pdf)) | encoder 2 pha trên băng + hệ tọa độ đi theo vật; TCP lệch trong ±2 mm ở tới 350 mm/s khi hiệu chuẩn tốt | số của hãng, điều kiện lý tưởng | **Hệ quy chiếu băng là kỹ thuật cổ điển.** Cái có thể mới là dùng nó làm giao diện cho chính sách học và cho phép demo lúc băng dừng; mình chưa tìm thấy bài làm điều đó |

Đã đọc abstract nhưng ít liên quan: DynaMOMA ([2606.25295](https://arxiv.org/abs/2606.25295), diffusion dự đoán quỹ đạo kẹp, robot di động), Kiyokawa et al. ([2411.09904](https://arxiv.org/abs/2411.09904), kẹp khi robot di chuyển), IL-based visual servoing ([2309.07729](https://arxiv.org/abs/2309.07729), mô phỏng), DGBench ([2204.13879](https://arxiv.org/abs/2204.13879)), "Learning-augmented robotic automation" ([2604.22235](https://arxiv.org/abs/2604.22235), không có băng chuyền).

**Hệ quả cho thiết kế:** (a) baseline mô-đun phải mạnh và dùng *cùng* bộ thực thi hệ quy chiếu băng với chính sách học, để phần khác biệt chỉ là nhận thức + chọn điểm kẹp; (b) phải có MIP; (c) số lượt thử mỗi ô phải nhiều hơn mức các bài VLA hay báo cáo, vì chênh lệch cần thấy là cỡ 15–20 điểm (§4.4).

---

## 2. Claim, giả thuyết, cách bị bác bỏ

**Claim chính (C):** ô chính = *vật lạ × C2*, băng ở tỉ số dẫn trước L = 0,5 (§3.5). **Chính sách học của hồ sơ** (ACT với giao diện mặc định chốt ở G1b, cố định trước G2; DP và MIP chạy ở G3) hơn baseline mô-đun mạnh nhất (CL-0 hoặc CL-1) ≥ 15 điểm, McNemar chính xác p ≤ 0,05, và chính sách học ≥ 60% tuyệt đối. Chọn trước một chính sách thay vì chọn "cái tốt nhất" sau khi thử, vì với 20–30 lượt mỗi cấu hình thì chọn bằng robot trên dev chủ yếu là chọn theo nhiễu.

**Claim phụ (C′):** giao diện hệ quy chiếu băng giúp chính sách chịu được băng nhanh hơn, và cho phép dùng demo thu lúc băng dừng.

| # | Giả thuyết | Bị bác bỏ khi | Mình đoán `[ước lượng]` |
|---|---|---|---|
| H1 | **Có chỗ trống:** baseline mô-đun hỏng ở chỗ khó (ô vật lạ × C2) | CL ở ô đó ≥ {{G0_PIVOT_PCT|0}}% (nếu ô kiểm hệ thống `seen_C0` < {{G0_SANITY_PCT|0}}% thì hệ thống lỗi, chưa kết luận được) | {{P_H1|0}}% |
| H2 | Chính sách học làm được việc cơ bản với ≤ 100 demo | < 50% ở vật quen, C0/C1, băng chậm sau tối đa 2 vòng sửa kỹ thuật | {{P_H2|0}}% |
| H3 | ACT (chính sách của hồ sơ) hơn mô-đun ở ô chính ≥ 15 điểm (= claim C) | hiệu < +15, hoặc p > 0,05, hoặc học < 60% | {{P_H3|0}}% (nếu H1, H2 đúng) |
| H4 | Giao diện hệ quy chiếu băng (I2) hơn giao diện hệ thế giới (I0/I1) ≥ 15 điểm ở L = 1,0 | hiệu < +15 ở L = 1,0 | {{P_H4|0}}% |
| H4b | Chính sách I2 huấn luyện bằng **demo lúc băng dừng** đạt ≥ 80% so với I2 huấn luyện bằng demo lúc băng chạy, khi chạy trên băng chạy | < 80% | {{P_H4B|0}}% |
| H5 | DP hơn MIP/ACT có ý nghĩa ở ô chính. **Tiên nghiệm của mình: không** | báo cáo kết quả dù thế nào | {{P_H5|0}}% cho "DP hơn có ý nghĩa" |
| H5b | Khi demo chọn vật *tự do* (không quy tắc), DP giữ mode tốt hơn hồi quy | không có khác biệt, hoặc người thao tác thực ra chọn nhất quán | chưa có cơ sở |

H4, H4b và H5 được thử ở n = 30 mỗi ô (G3), nên chỉ thấy được chênh lớn (≳ {{mdd_pair_30_70|0}}–{{mdd_pair_30_50|0}} điểm, §4.4); chênh nhỏ hơn thì báo cáo là mô tả, không kết luận.

Nếu hội đồng muốn DP là đóng góp chính thì H5/H5b là con đường duy nhất, và tiên nghiệm của mình là thấp.

---

## 3. Hệ thống

### 3.1 Cần bạn điền hoặc đo trước (mình chưa biết)

| # | Mục | Vì sao cần | Cách làm |
|---|---|---|---|
| 1 | Camera: model, RGB hay RGB-D, độ phân giải, fps, vị trí gắn | quyết định có CL-2 (GG-CNN) hay không và độ trễ | điền |
| 2 | **Độ trễ camera → PC** (ms) | tính τ và L | chớp LED trước ống kính + bộ đếm khung, lấy trung vị 10 lần |
| 3 | **Độ mở kẹp hữu dụng w** (mm) và tải tối đa (g) | chọn vật, tính L | thước, cân. `[chưa kiểm]` mình không có thông số chính thức của SO-101 |
| 4 | **Độ lặp lại vị trí của SO-101** (độ lệch chuẩn, mm) | là trần thành công của *cả hai* phía | ra lệnh đến cùng một điểm 20 lần, đo lệch bằng thước/ảnh |
| 5 | Tốc độ băng thật so với số xung (mm/s) và tốc độ tối đa an toàn | tính s(t) và L | vạch đánh dấu cách đều + camera, 3 tốc độ |
| 6 | Bề rộng băng, màu và texture mặt băng | phân đoạn, sinh sắp xếp | điền |
| 7 | Có tay leader SO-101 (hoặc thiết bị teleop khác) không | chọn nhánh dữ liệu | **CÓ** (bạn báo 26/10) → nhánh T, §4.1 |
| 8 | CPU (số lõi), RAM, ổ cứng trống | tốc độ ghi video và huấn luyện | điền |
| 9 | Hạn chót đồ án, tạp chí nhắm tới | chọn gói tối thiểu hay đầy đủ (§6) | điền |

Công thức tỉ số dẫn trước (đại lượng không thứ nguyên để chọn tốc độ băng): **L = v · τ / w**, với v = tốc độ băng, τ = tổng trễ vòng (camera + suy luận + trễ cánh tay), w = độ mở kẹp hữu dụng. L nhỏ (dưới ~0,25) thì sai số "dẫn trước" nằm trong dung sai của kẹp, mọi giao diện đều ổn; L ≥ 0,5 thì giao diện bắt đầu có ý nghĩa `[ước lượng]`. Ví dụ tính (`[giả định]` w và τ, bạn thay bằng số đo của mình):

<!--T:t5-->

### 3.2 Giao diện chính sách ↔ băng (biến chính của claim phụ)

```
s(t)  độ dịch của băng dọc hướng băng (mm) = số xung bước × mm/xung; mốc 0 lúc bắt đầu tập
p_w   vị trí trong hệ thế giới (gốc ở đế robot);   p_b = p_w − s(t)·x̂  là vị trí trong hệ băng

I0  chính sách xuất mục tiêu EE trong hệ thế giới; không có đầu vào băng
I1  như I0 nhưng nhận thêm s(t) và ṡ(t) làm đầu vào
I2  chính sách xuất mục tiêu EE trong hệ băng, tương đối so với EE lúc chụp ảnh t_img:
        a_k = p_b,mục tiêu(t_img + kΔ) − p_b,EE(t_img)            (nhãn huấn luyện)
    bộ thực thi đổi về hệ thế giới ở thời điểm THỰC THI t_x:
        p_w,lệnh(t_x) = p_w,EE(t_img) + a_k + (s(t_x) − s(t_img))·x̂
```

Ý nghĩa: ở I2, độ dịch của băng trong khoảng trễ (camera, suy luận, hàng đợi hành động) do **bộ thực thi** gánh, không phải mạng học. Mạng chỉ phải học "đi đâu so với vật, theo hệ băng". Đây chính là "conveyor tracking" của robot công nghiệp (mục 1, dòng ABB), nên bản thân hệ băng *không* là đóng góp; đóng góp có thể là dùng nó làm giao diện cho chính sách học từ ảnh, và hệ quả của nó: **demo thu lúc băng dừng dùng được khi băng chạy** (H4b), vì khi s(t) không đổi thì nhãn I2 trùng nhãn hệ thế giới.

Yaw, độ cao z và kẹp không có thành phần băng. Ba điều cần lưu ý (`[giả định]` chưa thử):
- **Vật trượt trên băng** hay bước bị mất thì s(t) lệch; phải đo (mục 3.1, dòng 5) và ghi lại.
- **Vùng với tới của SO-101 nhỏ.** Với băng chạy, bộ thực thi phải *chờ* tới khi mục tiêu vào vùng với tới rồi mới chạy chunk; demo lúc băng dừng không dạy phần chờ này, nên phần chờ là luật cứng ở bộ thực thi.
- **Phần mềm:** LeRobot mặc định dùng hành động trong không gian khớp. I2 cần đổi nhãn sang không gian EE bằng động học thuận (URDF SO-101) và bộ thực thi dùng động học ngược; trang `il_robots` mình đọc không nhắc EE hay IK `[đã kiểm: không có]`; thanh bên của trang đó có mục "Action Representations" mình chưa đọc `[chưa kiểm]`. Với SO-101 (5 khớp + kẹp) tư thế kẹp từ trên xuống + yaw có thể giải IK dạng đóng, khoảng 3–5 ngày làm cả phần này `[ước lượng]`.

### 3.3 Các lớp chính sách (cùng dữ liệu, cùng backbone, cùng ngân sách bước huấn luyện)

| Lớp | Mô tả | Ghi chú |
|---|---|---|
| **ACT** | Action Chunking with Transformers ([2304.13705](https://arxiv.org/abs/2304.13705)) | trang chủ tài liệu LeRobot gọi ACT là "chính sách đầu tiên nên dùng"; lệnh huấn luyện `lerobot-train --policy.type=act` có trong trang `il_robots` `[đã kiểm]` |
| **DP** | Diffusion Policy ([2303.04137](https://arxiv.org/abs/2303.04137)) | LeRobot có bản DP theo các trang tài liệu bản sao `[chưa kiểm trên bản bạn cài]`. Toy: K = 1–2 bước DDIM không kém K = 8–32, nên thử K nhỏ để giữ độ trễ thấp |
| **MIP** | hồi quy 2 bước có giám sát bước giữa ([2512.01809](https://arxiv.org/abs/2512.01809)) | không có sẵn trong LeRobot, cần cài đặt (đổi hàm mất mát của DP; mình viết được) |
| SmolVLA (tùy chọn) | VLA nhỏ ([2506.01844](https://arxiv.org/abs/2506.01844)) | chỉ làm mốc tham chiếu; có thể không vừa 8 GB khi tinh chỉnh `[chưa kiểm]` |

Cố định: đầu vào = 1 camera eye-to-hand (thêm camera thứ hai nếu có) + trạng thái khớp; hành động = (x, y, z, yaw, kẹp) trong không gian EE với góc chúc xuống cố định, **cùng không gian hành động cho I0, I1 và I2**, để khác biệt giữa các giao diện không lẫn với khác biệt không gian hành động. G2 và G3 dùng 2 hạt giống huấn luyện; ở G2 mỗi hạt giống chạy một nửa số sắp xếp (xen kẽ lẻ/chẵn) để trung bình hóa phương sai giữa các lần huấn luyện (toy cho thấy phương sai này lớn); phân tích gộp, hạt giống ghi ở cột `note`.

### 3.4 Baseline mô-đun (phần quan trọng nhất để bài đứng được)

| Tên | Cấu tạo |
|---|---|
| **CL-0** (cổ điển thuần) | (1) hiệu chuẩn camera → mặt phẳng băng (homography); (2) tách nền: mô hình nền của băng trống (nhớ bù độ dịch băng nếu mặt băng có texture) → mặt nạ → thành phần liên thông; (3) với mỗi vật: **điểm kẹp = cực đại của biến đổi khoảng cách** (không phải trọng tâm, vì chịu được vật lõm), yaw vuông góc trục dài (PCA), bỏ vật rộng hơn w; (4) chọn vật theo luật cố định (xuôi dòng nhất trong vùng với tới); (5) vị trí vật trong hệ băng p_b là hằng số khi vật không trượt, lấy trung bình nhiều khung; (6) **dùng cùng bộ thực thi hệ băng I2** để bám, hạ kẹp, khép, nhấc; cập nhật lại vị trí khi còn tiếp cận |
| **CL-1** (mô-đun + phân đoạn nền tảng) | như CL-0 nhưng bước (2) dùng mặt nạ không phân lớp của SAM 2 hoặc EfficientTAM (DynamicVLA dùng EfficientTAM cho demonstrator `[đã kiểm]`); tốc độ trên RTX 3070 Ti `[chưa kiểm]` |
| **CL-2** (tùy chọn) | bộ dự đoán điểm kẹp có huấn luyện sẵn, ví dụ GG-CNN, **chỉ nếu camera có depth** |

Quy tắc công bằng (ghi trước, đóng băng): cùng camera, băng, robot, IK, kẹp, bộ thực thi; mỗi baseline được tinh chỉnh **tối đa 2 ngày làm việc** trên *vật dev và sắp xếp dev* (tập tách rời khỏi test), ghi lại số giờ đã dùng; sau đó đóng băng toàn bộ tham số trước lượt test đầu tiên và công bố tham số cùng mã.

**Trạng thái CL-0 (26/10/2026).** Các bước (1)–(6) ở bảng trên và bộ thực thi hệ băng (`BeltExecutor`: IK + s(t), thành phần mà I2 sẽ dùng lại) đã được viết thành gói `cl0/`, kèm: lệnh hiệu chuẩn (FK, camera → mặt băng bằng bàn cờ + 9 điểm chạm, hướng băng/mm-xung/độ trễ, nền băng trống, độ trễ servo), công cụ đặt băng và xem nhận thức, lệnh đóng băng (`python -m cl0.freeze`; bộ chạy G0 có `--require-frozen`) và bộ chạy G0 (đặt vật theo tờ sắp xếp, ghi CSV đúng định dạng `g0_analyze.py`). Hướng dẫn: `cl0/README_CL0.md`.
- **Đã kiểm:** 233 test tự động (mô phỏng động học vòng kín; "phòng lab ảo" chạy chính các lệnh hiệu chuẩn với người vận hành ảo; thiết bị giả cho serial, robot, camera). API LeRobot 0.6.1 được đối chiếu bằng đọc mã nguồn, không chạy robot.
- **Chưa kiểm:** mọi thứ chạm phần cứng thật (robot, băng, camera). Mô phỏng là động học (không ma sát, không đẩy vật): nó cho thấy logic, khung toạ độ và định thời *có thể* đúng, **không dự đoán tỉ lệ thành công ở G0**.
- **Giới hạn đã biết của CL-0 (liên quan tới cách chọn bộ test, §3.5):** độ cao kẹp cố định (vật mỏng hơn mức đó không kẹp được; chỉnh chung cho mọi vật trên dev); thị sai của vật cao; vật lõm/có quai dễ trượt; TCP của kẹp một má động chưa xác định cho máy bạn.
- **Hai nút không thuộc CL-0 gốc**, mặc định TẮT: `perception.grasp.yaw_mode = "local"`, `perception.split = "watershed"`. Bật thì phải ghi vào ghi chú đóng băng và công bố, vì chúng làm baseline mạnh hơn bản mô tả ở bảng trên.

### 3.5 Vật thể, clutter, tốc độ

- **32 vật** `[giả định]`: 20 *train* (thu demo), 4 *dev* (tinh chỉnh CL-0/CL-1; siêu tham số của chính sách học chọn bằng mất mát validation, không bằng lượt thử robot), 8 *test* (vật lạ; chốt **trước** G0). Vừa kẹp (đường kính ≲ 70–80% w) và nhẹ hơn tải tối đa `[chưa đo]`. Bộ test phải gồm ít nhất 3 dạng khó với heuristic: lõm hoặc có quai, mỏng/dẹt, tương phản thấp với mặt băng; chụp ảnh và lưu danh sách.
- **Clutter:** C0 = 1 vật; C1 = 2 vật tách xa; C2 = 3–4 vật, mỗi vật cách ít nhất một vật khác 10–25 mm, hai vật bất kỳ cách ≥ 8 mm; C3 = 4–5 vật chạm nhau (hở 0–3 mm). Ngưỡng mm sửa trong `make_arrangements.py` cho hợp kẹp của bạn, **trước** khi sinh bộ test.
- **Tốc độ:** chọn theo L = 0,25 / 0,5 / 1,0 (công thức §3.1). Ô chính ở L = 0,5; L = 1,0 chỉ cho G1b và G3. Chen et al. dùng 5,5 và 11,0 cm/s với phần cứng khác, chỉ để tham khảo cỡ độ lớn.
- **Sắp xếp:** sinh sẵn bằng hạt giống cố định, mỗi sắp xếp dùng cho *mọi* phương pháp (ghép cặp), kèm cột `first_method` (A = baseline, B = chính sách học) để cân bằng thứ tự chạy.

---

## 4. Dữ liệu và giao thức thử

### 4.1 Thu demo: hai nhánh

| | **Nhánh T: có tay leader SO-101** | **Nhánh S: không có leader** |
|---|---|---|
| Cách thu | `lerobot-record` với `so101_follower` + `so101_leader` `[đã kiểm: trang il_robots]`; thu cả lúc băng dừng và băng chạy chậm | **demonstrator bấm chuột trên băng dừng:** người bấm điểm kẹp + kéo hướng yaw trên ảnh, robot chạy theo kịch bản IK, ghi ảnh/khớp/hành động. Người chọn *vật nào, kẹp ở đâu*; quỹ đạo là kịch bản |
| Ưu | quỹ đạo tự nhiên, đa dạng; demo lúc băng chạy có thật | không cần phần cứng thêm; quỹ đạo sạch; dùng chung hiệu chuẩn với CL-0 |
| Nhược | người điều khiển khó bám vật khi băng chạy, demo ồn | quỹ đạo đồng nhất nên đa mode chỉ nằm ở khâu chọn vật; **phụ thuộc hoàn toàn vào H4b** (demo tĩnh dùng cho băng chạy) |
| Khuyến nghị | thu bằng tay | thu 150 demo đầu theo nhánh S; nếu có thể thì lắp một tay leader (cùng thiết kế SO-101; giá và thời gian giao `[chưa kiểm]`) rồi chuyển sang nhánh T |

**Đã chọn (26/10): nhánh T**, vì bạn có tay leader SO-101; nhánh S chỉ còn là phương án dự phòng nếu thu demo bằng leader gặp vấn đề. Hai hệ quả: (a) tay follower dùng chung hiệu chuẩn LeRobot với CL-0 (cùng `robot_id`); **đừng chạy lại `lerobot-calibrate` cho follower giữa lúc hiệu chuẩn camera và lúc thu demo**, vì "0°" của LeRobot là trung điểm tầm chuyển động đã ghi, đổi hiệu chuẩn thì FK, `calib.json` và nhãn I2 lệch theo; (b) demo lúc băng chạy do người điều khiển bám vật nên ồn (đúng hàng "Nhược" ở trên), nên giữ nguyên số demo lúc băng dừng và kiểm H4b như đã ghi.

Khối lượng `[giả định]`: **{{N_DEMO|0}} demo** ≈ {{DEMO_H|1}} giờ; trong đó 250 demo lúc băng dừng (có **20 sắp xếp × 3 lần lặp** để đo xem người chọn vật nhất quán đến đâu: tỉ lệ cặp demo cùng sắp xếp chọn cùng một vật; nếu ≥ 90% `[ngưỡng mình chọn]` thì coi là đơn mode ở khâu chọn vật và bỏ H5b; tức đo đa mode thật chứ không giả định) và 150 demo lúc băng chạy. Cỡ này khiêm tốn: Yamamoto et al. chỉ dùng 3 demo (mỗi vị trí một demo) cho một vật rồi tăng cường dữ liệu, còn ForeTime-VLA dùng 458 tập nhưng với mô hình lớn; **đường co giãn dữ liệu ở G3 sẽ cho biết 400 có đủ không.**

<!--T:t7-->

### 4.2 Dữ liệu ghi mỗi lượt và mỗi demo

| Luồng | Nội dung | Ghi chú |
|---|---|---|
| ảnh | khung camera + dấu thời gian lúc nhận | ≥ 30 fps nếu tải được; lưu video gốc cho các lượt thất bại |
| robot | trạng thái khớp, hành động lệnh, ≥ 30 Hz, có dấu thời gian | |
| băng | số xung bước s(t) có dấu thời gian, tốc độ lệnh | căn thời gian với camera là điểm dễ sai nhất; đo độ lệch đồng hồ |
| lượt | `trial_id, method, cell, arrangement_id, success, valid, fail_cause, note` + cấu hình, hạt giống, ánh sáng, người thao tác | đúng định dạng của `g0_analyze.py` (xem `g0_template.csv`) |
| hiệu chuẩn | nội tham số camera, camera↔robot, hướng băng trong hệ robot, độ trễ camera, kiểm tốc độ băng | ghi lại mỗi buổi |

### 4.3 Giao thức một lượt thử

- Đặt vật theo tờ sắp xếp, chạy băng đến tốc độ cài, **một lần thử duy nhất** mỗi lượt; hết giờ sau 20 s `[giả định]`.
- **Thành công** = một vật được nhấc khỏi băng và giữ ≥ 2 s. Phụ: *thành công sạch* = không vật khác bị xô quá 1 cm. Ghi vật nào bị nhặt.
- **Lượt không hợp lệ chỉ gồm** lỗi phần cứng/ngắt khẩn cấp/mất giao tiếp camera hoặc servo. Loại và **chạy lại**; mọi thứ khác tính là thành công hoặc thất bại. Nếu tỉ lệ không hợp lệ > 10% thì dừng và sửa. Quy tắc này ghi trước để không "hợp lệ hóa" các lượt thất bại.
- Phương pháp chạy xen kẽ trên cùng sắp xếp, trong cùng buổi và cùng ánh sáng, thứ tự theo cột `first_method`.
- Nguyên nhân thất bại điền ngay sau lượt từ danh sách đóng: `merge` (các vật dính thành một), `seg_miss` (không phát hiện), `grasp_point` (điểm/hướng kẹp sai), `timing` (sớm/muộn, sai dẫn trước), `calib` (lệch hệ thống), `slip` (tuột), `collision` (va), `other`.

### 4.4 Số lượt cần để thấy chênh lệch (tính bằng `stats_tables.py`)

Độ rộng khoảng tin cậy Wilson 95% quanh một tỉ lệ quan sát. Ví dụ ở 70%, n = 30 cho ±{{hw30_70|0}} điểm, n = 60 cho ±{{hw60_70|0}} điểm:

<!--T:t1-->

Chênh lệch tối thiểu thấy được với công suất 80%, α = 0,05 (hai phía), theo baseline thật. "Ghép cặp" dùng McNemar chính xác với tương quan thành công giữa hai phương pháp trên cùng sắp xếp ρ = {{RHO|1}} `[giả định]`; "—" = không đạt 80% dù đối chứng đạt 100%:

<!--T:t2-->

Số lượt cần để thấy đúng +15 hoặc +20 điểm (số cặp khi ghép; số lượt mỗi nhánh khi độc lập):

<!--T:t2b-->

Hệ quả: **n = 30 mỗi ô chỉ thấy được chênh ≳ {{mdd_pair_30_70|0}}–{{mdd_pair_30_50|0}} điểm; không đủ cho +15.** Vì vậy ngân sách dồn vào *một ô chính* với n = 60 cặp (thấy được chênh ≳ {{mdd_pair_60_70|0}}–{{mdd_pair_60_50|0}} điểm); các ô còn lại n = 20–30 chỉ để mô tả. Thấy đúng +15 với công suất 80% cần khoảng {{need_15_60|0}} cặp ở baseline 60% (độc lập: {{need_15_60_ind|0}} mỗi nhánh), tức thêm 60 cặp ≈ {{EXT_TR|0}} lượt ≈ {{EXT_H|1}} giờ robot cho ô chính. Mình **không** đưa việc mở rộng vào quy tắc: nhìn kết quả ở 60 cặp rồi mới quyết định thêm là xem trộm và làm sai mức α. Nếu muốn n = 120 thì chọn ngay từ đầu; nếu mở rộng sau khi đã thấy kết quả, ghi nó vào mục "Sai lệch" và coi là phân tích thăm dò.

Xác suất đạt tiêu chí G2 (hiệu quan sát ≥ +15 **và** McNemar p ≤ 0,05), n = 60 cặp, ρ = {{RHO|1}}:

<!--T:t3-->

Đọc bảng: nếu baseline thật 60%, hiệu thật +20 thì có {{pgo_20_60|0}}% khả năng GO, +15 thì {{pgo_15_60|0}}%, hiệu thật 0 thì {{pgo_0_60|0}}% (dương tính giả). Ngưỡng +15 đi kèm điều kiện *quan sát* ≥ +15 nên dù hiệu thật đúng +15 vẫn chỉ khoảng một nửa số lần đạt; tiêu chí cố ý chặt để GO nghĩa là thắng rõ. Kết quả "không kết luận" là hợp lệ và có khả năng xảy ra; kế hoạch phải chấp nhận được nó.

---

## 5. Các cổng và tiêu chí ghi trước

**Quy tắc đóng băng:** trước lượt thử đầu tiên, chốt ngưỡng (sửa ở đây và ở đầu `g0_analyze.py` nếu muốn), rồi chạy (từ thư mục chứa cả `KE_HOACH_HUONG_1.md` và `dir1/`) `sha256sum KE_HOACH_HUONG_1.md dir1/g0_analyze.py > dir1/FROZEN.txt` và giữ file đó. Mọi thay đổi về sau ghi vào mục "Sai lệch so với kế hoạch" ở cuối file, không sửa chỗ cũ. Mọi ngưỡng ở mục này (70%, 85%, 80%, 50%, +15 điểm, 60%) là **do mình chọn** theo lập luận bên dưới, không từ nguồn nào; sửa được trước khi đóng băng. Mã và cấu hình CL-0 được đóng băng riêng bằng `python -m cl0.freeze` (§3.4); sửa sau đó chỉ qua `--force --notes "SỬA ĐỔI: …"`, vết cũ được giữ trong `frozen.json` và phải công bố ở mục "Sai lệch" cuối file.

| Cổng | Câu hỏi | Chi phí | Việc | Tiêu chí |
|---|---|---|---|---|
| **G0** | Baseline mô-đun có hỏng ở chỗ khó không? | bạn: hiệu chuẩn/tinh chỉnh CL-0 (mã đã viết, §3.4) + {{G0_TR|0}} lượt ≈ {{G0_H|1}} giờ robot | CL-0 đã đóng băng, L = 0,5. Ô: `seen_C0` (n = 20, kiểm hệ thống), `novel_C0` (20), **`novel_C2` (30, ô quyết định)**, `novel_C3` (20). Dùng sắp xếp đầu danh sách của bộ test (CL không học nên không rò rỉ). Dữ liệu G0 chỉ để ra quyết định; G2 **chạy lại CL xen kẽ cùng buổi** với chính sách học để ghép cặp thật sự cùng điều kiện | xem bên dưới |
| **G1a** | Chính sách học làm được việc cơ bản không? | bạn: ~100 demo (trích từ bộ demo vật quen) + 1 lần huấn luyện + 30 lượt | ACT, I0, vật quen (train), C0/C1, L = 0,25 | ≥ 70% (≥ 21/30). < 50%: lỗi kỹ thuật (camera, trễ, không gian hành động), sửa tối đa 2 vòng; còn < 50% thì dừng, sang hướng 4 |
| **G1b** | Bộ thực thi hệ quy chiếu băng chạy đúng không? | bạn: +1 huấn luyện + 60 lượt | I2 so với I0, vật quen, C0, L = 1,0, n = 30 mỗi bên | **Không phải cổng thắng/thua** (n = 30 chỉ thấy chênh cỡ 30 điểm). Dùng I2 làm mặc định nếu I2 ≥ I0 − 10 điểm; nếu thấp hơn nhiều thì lỗi ở bộ thực thi (mốc thời gian, dấu của s), sửa trước |
| **G2** | Học có hơn mô-đun ở ô chính không? | bạn: gói tối thiểu {{G2_MIN_TR|0}} lượt | ô `novel_C2` n = 60 cặp + `seen_C0`, `novel_C0`, `novel_C3` n = 30; chính sách học = ACT + giao diện mặc định, 2 hạt giống, cố định trước G2 | GO nếu hiệu ≥ +15 điểm, McNemar p ≤ 0,05, học ≥ 60%. Chỉ ô chính được tính vào quyết định; các ô còn lại chỉ mô tả |
| **G3** | Thành phần nào đóng góp? | bạn: ~{{G3_MIN_TR|0}} lượt (huấn luyện: xem §6) | I0/I1/I2 × L; ACT/DP/MIP × 2 hạt giống; demo tĩnh so với chạy; co giãn dữ liệu (25/50/100%) | không có GO/NO-GO; báo cáo mọi kết quả, kể cả âm |

**Quy tắc G0** (áp cho CL-0 trước, rồi CL-1 nếu mơ hồ), `g0_analyze.py g0`:

- *Kiểm hệ thống:* `seen_C0` phải ≥ 80%. Dưới mức đó là lỗi hiệu chuẩn/kỹ thuật, **không** tính là chỗ trống; sửa rồi chạy lại.
- *Ô quyết định* `novel_C2`, n = 30: **GO** nếu thành công ≤ 70% (≤ {{g0_kgo_30|0}}/30) **và** ≥ 50% các lượt thất bại do nhận thức/chọn điểm kẹp (`merge`, `seg_miss`, `grasp_point`); **PIVOT** nếu ≥ 85% (≥ {{g0_kpv_30|0}}/30); ở giữa là **mơ hồ** → chạy CL-1 ở cùng ô và áp lại quy tắc; baseline ghi nhận là cái mạnh hơn trong hai. Nếu thành công ≤ 70% nhưng < 50% thất bại do nhận thức/chọn điểm kẹp thì là **GO có điều kiện**: sửa nguyên nhân gốc (hiệu chuẩn, định thời, kẹp) và chạy lại G0 đúng một lần trước khi vào G1a.
- Lập luận cho điều kiện thứ hai: nếu hỏng chủ yếu vì `timing`, `calib` hay `slip` thì đó là giới hạn phần cứng/hiệu chuẩn, chính sách học trên cùng robot cũng không cứu được.
- Lập luận cho ngưỡng 70%: để học vượt +15 mà vẫn khả thi (học đạt ~85% là trần hợp lý với cỡ dữ liệu này `[ước lượng]`) thì baseline phải ≤ ~70%.

Tính chất vận hành của quy tắc theo tỉ lệ thành công (chỉ phần tỉ lệ; tính từ phân phối nhị thức):

<!--T:t4-->

Đọc bảng: nếu baseline thật 80%, G0 báo GO sai chỉ {{g0_false_go_80_30|0}}%, nhưng vùng 70–80% rất hay rơi vào "mơ hồ", và khi đó phải chạy CL-1; nếu baseline thật 90%, G0 báo PIVOT {{g0_pivot_90_30|0}}% số lần; nếu thật 60%, báo GO {{g0_go_60_30|0}}%.

**Sơ đồ quyết định**

```
G0 ── PIVOT ──► hướng 4 (đối chứng / testbed), có thể thêm hướng 2; dùng lại hiệu chuẩn, bộ thực thi, CL-0/1, giao thức, log
 │  mơ hồ ──► CL-1 ở ô quyết định, áp lại quy tắc
 └─ GO ──► G1a ── < 50% sau 2 vòng sửa ──► dừng, hướng 4
             └─ ≥ 70% ──► G1b (sanity) ──► G2 ── GO ──► G3 + viết (claim mạnh)
                                              ├─ THẮNG NHỎ / KHÔNG KẾT LUẬN ──► G3 + viết như nghiên cứu đối chứng
                                              └─ NO-GO ──► viết như nghiên cứu đối chứng ("cổ điển hỏng nhưng học chưa đuổi kịp"), G3 chỉ ra thiếu gì
```

Nhãn của `g0_analyze.py g2`: THẮNG NHỎ = p ≤ 0,05 nhưng hiệu < +15 hoặc học < 60% tuyệt đối; KHÔNG KẾT LUẬN = khoảng tin cậy chứa cả 0 lẫn +15; NO-GO = cận trên bootstrap của hiệu < +15.

---

## 6. Ngân sách và lịch

Số lượt thử và giờ robot (`[giả định]`: {{MIN_PER_TRIAL|0}} phút/lượt gồm đặt vật, chạy, dọn; hệ số hao phí {{OVERHEAD|1}} cho hiệu chuẩn, lỗi phần cứng, chạy lại). **Gói tối thiểu ≈ {{MIN_TR|0}} lượt ≈ {{MIN_H|0}} giờ robot; gói đầy đủ ≈ {{FULL_TR|0}} lượt ≈ {{FULL_H|0}} giờ.**

<!--T:t6-->

Huấn luyện: khoảng {{N_TRAIN|0}} lần chạy; nếu mỗi lần {{TRAIN_LO|0}}–{{TRAIN_HI|0}} giờ trên RTX 3070 Ti thì tổng {{TRAIN_H_LO|0}}–{{TRAIN_H_HI|0}} giờ GPU. Khoảng này rộng vì mình **chưa đo** tốc độ huấn luyện trên máy bạn `[chưa kiểm]`; đo ở G1a rồi cập nhật bảng này.

Lịch thô `[ước lượng]`, 1 người làm bán thời gian:

| Giai đoạn | Việc | Thời gian |
|---|---|---|
| 1 | điền/đo §3.1; hiệu chuẩn; ghi log; CL-0 **kèm bộ thực thi bám băng** (IK + s(t), dùng lại cho chính sách học) **đã viết 26/10**, phần còn lại là phần cứng: lắp, hiệu chuẩn, lượt thử tĩnh rồi băng chậm, tinh chỉnh ≤ 2 ngày trên dev, đóng băng | 1,5–2 tuần |
| 2 | **chạy G0** → quyết định #1 | 1–2 ngày |
| 3 | chuyển nhãn sang không gian EE / hệ băng (động học thuận), nối chính sách vào bộ thực thi đã có, thu demo, G1a, G1b | 2–3 tuần |
| 4 | G2 | 1–2 tuần |
| 5 | G3, phân tích, viết | 3–4 tuần |

Tổng ≈ 8–11 tuần; nếu G0 ra PIVOT thì dừng ở tuần ~3 và chuyển hướng với hạ tầng đã có.

Ghi chú 26/10: phần viết mã của giai đoạn 1 đã xong, nên 1,5–2 tuần còn lại gần như toàn là lắp đặt, đo đạc và hiệu chuẩn. Mình **không** rút ngắn con số vì lần chạy đầu của lớp I/O trên thiết bị thật là chỗ nhiều rủi ro nhất (xem bảng rủi ro, §7) `[ước lượng]`.

---

## 7. Ai làm gì, rủi ro

| Việc | Mình (trong sandbox, không chạm robot) | Bạn (phòng lab) |
|---|---|---|
| G0 | bộ phân tích đã viết và thử (`g0_analyze.py`); **CL-0 tham chiếu bằng OpenCV kèm bộ thực thi bám băng (IK + s(t)) đã viết (`cl0/`, 26/10), thử trên ảnh tổng hợp, mô phỏng động học và thiết bị giả** | lắp, hiệu chuẩn, tinh chỉnh CL-0 ≤ 2 ngày, đóng băng, chạy {{G0_TR|0}} lượt |
| Chuẩn bị test | bộ sinh sắp xếp đã viết và thử (`make_arrangements.py`) | chọn 32 vật, chụp ảnh, chốt bộ test |
| I2 | bộ thực thi bám băng đã có (`BeltExecutor`, dùng chung với CL-0); còn phải viết bộ chuyển nhãn khớp → EE/hệ băng (dùng lại `cl0/kinematics.py`, URDF SO-101 đã nhúng) và nối chính sách vào bộ thực thi, nếu bạn bảo | thu demo (nhánh T), chạy trên robot |
| MIP | viết cài đặt | huấn luyện, đo tốc độ |
| Huấn luyện/thử | không làm được (không GPU, không robot) | toàn bộ |
| Phân tích, viết bài | toàn bộ phần thống kê, bảng, bản nháp | số liệu thật, hình, kiểm chứng |

| Rủi ro | Mức `[ước lượng]` | Giảm thiểu |
|---|---|---|
| Không có chỗ trống (cổ điển ≥ 85%) | cao | cổng G0 đặt đầu tiên; PIVOT dùng lại hạ tầng |
| SO-101 lặp lại kém / kẹp yếu chặn trần cả hai phía | trung bình | đo ở §3.1 dòng 4; chọn vật nhẹ, mềm mặt kẹp; ghi trần |
| 400 demo không đủ cho vật lạ | cao | backbone huấn luyện sẵn, tăng cường dữ liệu; đường co giãn ở G3 để biết thiếu bao nhiêu |
| Bị chê baseline yếu | trung bình | CL dùng cùng bộ thực thi I2; CL-1 với phân đoạn nền tảng; điểm kẹp bằng biến đổi khoảng cách; 2 ngày tinh chỉnh, đóng băng, công bố mã |
| Bị chê chính sách học tinh chỉnh kém | trung bình | cùng dữ liệu/backbone/ngân sách bước; siêu tham số chọn bằng mất mát validation; 2 hạt giống; DP và MIP cũng chạy ở G3 (nếu vượt ACT thì báo là thăm dò vì không phải chính sách của hồ sơ) |
| Xung bước làm s(t) lệch (băng trượt, mất bước) | thấp–trung bình | kiểm bằng vạch đánh dấu + camera mỗi buổi |
| Căn thời gian ảnh ↔ băng ↔ khớp sai | trung bình | đo độ trễ camera; dấu thời gian mọi luồng; kiểm bằng lượt băng dừng/chạy |
| Lớp I/O phần cứng của CL-0 (LeRobot, serial băng, V4L2) chưa từng chạy trên thiết bị thật; firmware băng của bạn có thể khác giả định | cao ở lần chạy đầu | thiết bị giả và "phòng lab ảo" đã thử; API LeRobot 0.6.1 đối chiếu bằng đọc mã; chuỗi lệnh/dòng báo của băng sửa trong TOML, không cần sửa mã; chạy lượt tĩnh (`--speed 0`) rồi băng chậm trước (README_CL0 §7); mất camera/băng/servo giữa lượt được phát hiện và không bị tính là thất bại của CL-0 |
| Sai số hiệu chuẩn camera ↔ robot/băng làm CL-0 yếu giả tạo (nhiễu chạm tay ~1 mm; trong phòng lab ảo, ánh xạ ảnh → robot sai trung bình 1,7 mm, tối đa 3,4 mm) | trung bình | bàn cờ lớn và 9 điểm chạm; `calibrate` cảnh báo khi sai số chạm > 3 mm hoặc ô in bị co/giãn; đo độc lập quãng đường băng bằng thước (README_CL0 §5); `seen_C0` < 80% ở G0 coi là lỗi kỹ thuật, không phải chỗ trống |
| Ánh sáng đổi giữa buổi | trung bình | màn che, đèn cố định; ghi lại; xen kẽ phương pháp trong cùng buổi |
| Quá thời gian | trung bình | làm theo thứ tự cổng; gói tối thiểu |

---

## 8. Mình đề nghị chưa làm (bạn đổi được)

- **Không dựng lại mô phỏng PyBullet cho hướng này.** Hướng này phải có số thật; mô phỏng 5000 tập (8 s mỗi tập, 15 khung/s, 128×128) mất ≈ {{SIM_WALL_H|1}} giờ trên 2 lõi của sandbox `[tính từ số đo: vật lý 0,19 s/s mô phỏng, kết xuất 22 ms/khung]` và vẫn phải huấn luyện trên GPU của bạn, rồi còn khoảng cách mô phỏng → thật.
- **Không mở rộng toy.** Toy không có ảnh/clutter/vật lạ. Một phép thử "I2 có giúp ở toy" gần như chắc chắn thành công (băng trở thành tĩnh), nên giá trị thông tin thấp; mình chỉ làm nếu bạn muốn dùng nó để thử bộ thực thi.
- **Không tinh chỉnh VLA lớn.** ForeTime-VLA và DynamicVLA đã đi đường đó; 8 GB VRAM cũng hạn chế.

---

## 9. Nguồn

Mức đọc: tóm tắt trang abstract hoặc HTML qua công cụ đọc trang; **mình chưa đọc toàn văn bài nào**.

- [Chen et al., Adaptive Grasping of Moving Objects in Dense Clutter (2502.05916)](https://arxiv.org/abs/2502.05916) · bản HTML v2 đã đọc (thiết lập, Bảng I)
- [ForeTime-VLA (2608.20735)](https://arxiv.org/abs/2608.20735) · abstract + bản HTML v2
- [DynamicVLA (2601.22153)](https://arxiv.org/abs/2601.22153) · abstract + bản HTML v2
- [GG-CNN (1804.05172)](https://arxiv.org/abs/1804.05172) · abstract
- [Yamamoto et al. (2309.12547)](https://arxiv.org/abs/2309.12547) · abstract
- [GAP-RL (2410.03509)](https://arxiv.org/abs/2410.03509), [KARL (2506.15945)](https://arxiv.org/abs/2506.15945), [IL-based VS (2309.07729)](https://arxiv.org/abs/2309.07729), [DynaMOMA (2606.25295)](https://arxiv.org/abs/2606.25295), [Kiyokawa et al. (2411.09904)](https://arxiv.org/abs/2411.09904), [DGBench (2204.13879)](https://arxiv.org/abs/2204.13879), [Learning-augmented manufacturing (2604.22235)](https://arxiv.org/abs/2604.22235) · abstract
- [DCDP (2603.01953)](https://arxiv.org/abs/2603.01953), [RTC (2506.07339)](https://arxiv.org/abs/2506.07339), [Much Ado About Noising (2512.01809)](https://arxiv.org/abs/2512.01809) · abstract
- [ACT (2304.13705)](https://arxiv.org/abs/2304.13705), [Diffusion Policy (2303.04137)](https://arxiv.org/abs/2303.04137), [SmolVLA (2506.01844)](https://arxiv.org/abs/2506.01844) · abstract
- [ABB Conveyor Tracking, datasheet](https://library.e.abb.com/public/51c0fc4c87a036f6c1257b1300579b96/Data%20sheet%20Conveyor_tracking.pdf) · đọc qua công cụ đọc trang
- [LeRobot: Imitation Learning on Real-World Robots](https://huggingface.co/docs/lerobot/en/il_robots) · đọc qua công cụ đọc trang; trang này có vài chỗ tự mâu thuẫn (cờ `push_to_hub`, ghi chú "Koch")

Truy vấn tìm kiếm đã dùng (để bạn lặp lại): "diffusion policy dynamic grasping moving objects conveyor belt"; "learning-based grasping of moving objects on conveyor low-cost robot arm visual servoing 2026"; "grasping unseen moving objects in clutter learned visuomotor policy imitation learning conveyor"; "dynamic manipulation moving objects vision-language-action model benchmark conveyor 2026"; "class-agnostic grasping moving objects conveyor belt deep learning clutter pick novel objects segmentation"; "SAM 2 video segmentation tracking robot grasping moving objects conveyor pick unseen objects foundation model"; "classical visual servoing baseline versus learned imitation policy moving object grasping comparison tracker Kalman"; "conveyor frame action representation learned grasping policy encoder compensated moving belt robot learning"; "low-cost robot arm SO-100 SO-101 moving object conveyor ACT diffusion policy dynamic grasp"; "end-to-end learned policy vs modular perception pipeline dynamic grasping moving objects clutter 2026 benchmark".

---

## Phụ lục A. Bộ công cụ kèm theo (`dir1_tools.tar.gz`)

| File | Làm gì | Đã thử |
|---|---|---|
| `stats_tables.py` | sinh mọi bảng thống kê/ngân sách ở file này (cần numpy, scipy); sửa `PARAMS` ở đầu file rồi chạy lại | khớp scipy (Fisher, McNemar, Wilson) và mô phỏng Monte Carlo |
| `g0_analyze.py` | `cells` (bảng Wilson theo ô), `g0` (quy tắc G0), `g2` (ghép cặp, McNemar chính xác, bootstrap theo sắp xếp), `selftest`; chỉ dùng thư viện chuẩn | `selftest` qua 21 kiểm tra, gồm so khớp scipy và 9 kịch bản quyết định trên dữ liệu giả |
| `g0_template.csv` | mẫu CSV lượt thử | đọc được |
| `make_arrangements.py` | sinh sắp xếp vật ngẫu nhiên có hạt giống cho C0–C3 | cùng hạt giống ra cùng file; 0 vi phạm ràng buộc trên 180 sắp xếp thử |
| `objects_template.csv` | mẫu danh sách vật (`name,diameter_mm,split`) | |
| `README_DIR1.md` | lệnh chạy | |
| `cl0/` (thư mục dự án CL-0, giải nén cạnh `dir1/`) | CL-0, bộ thực thi hệ băng, các lệnh hiệu chuẩn, đặt băng/xem nhận thức, đóng băng, bộ chạy G0; hướng dẫn: `cl0/README_CL0.md` | 233 test tự động (mô phỏng động học, "phòng lab ảo", thiết bị giả) qua trên Python 3.12 và 3.13; **chưa chạy trên phần cứng** |

**Chưa viết, chờ bạn bảo:** bộ chuyển nhãn I2 (khớp → EE/hệ băng), MIP.

## Sai lệch so với kế hoạch (điền sau, không sửa các mục trên)

| Ngày | Điều đổi | Lý do | Ảnh hưởng tới kết luận |
|---|---|---|---|
| 26/10/2026 | Bạn có tay leader SO-101 → chọn nhánh T (§4.1). CL-0 và bộ thực thi hệ băng được viết trước khi điền §3.1 và trước khi đóng băng tiêu chí | bạn muốn có baseline để hiệu chuẩn và thử sớm | Không đổi tiêu chí hay ngưỡng nào, chỉ đổi thứ tự việc (mã trước, đo sau). Mã được viết khi chưa có số liệu thật nào, nên chưa có tinh chỉnh nào theo dữ liệu test |
