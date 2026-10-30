# Quy tắc gán nhãn tự động của arena (viết trước khi dùng, 29/10/2026)

Cài đặt: `arena/arena/labeler.py`. Đầu vào: chuỗi ground truth (GT) theo từng tick điều khiển 50 Hz (`trial_XXXX_gt.npz`), sự kiện và pha của phương pháp (`trial_XXXX.json`), tờ sắp xếp, tốc độ băng. Mọi ngưỡng có nhãn `[đề xuất]` là của mình, chờ bạn duyệt; đổi ngưỡng thì ghi ngày và lý do ở cuối file này, **không** đổi sau khi đã so phương pháp.

Ký hiệu:
- **Tâm kẹp (TCP):** `gripper_frame_link` + R · `robot.tcp_offset_mm`. Đây là điểm CL-0 đưa tới vật, tức tâm khe hai má.
- **Hệ băng:** `a_b = a − s_gt(t)`, trong đó `s_gt` là quãng băng đi thật.
- **Vật nằm trên băng:** |z tâm − (mặt băng + h/2)| ≤ 5 mm và a ≤ đầu cuối băng − bán kính bao.

## 1. Thành công (M1)
Thành công khi có một vật thoả cả hai điều kiện **liên tục ≥ 2,0 s**:
- đáy vật cao ≥ 25 mm so với mặt băng (khớp `cl0.sim.world` và kế hoạch §4.3);
- khoảng cách ngang từ TCP tới tâm vật ≤ w/2 = 30 mm (vật nằm trong má kẹp) `[đề xuất]`.

Gọi vật đó là **vật đích**. Thời điểm thành công là lúc đủ 2,0 s.

## 2. Thành công sạch (M2)
Thành công, và không vật nào khác bị xô quá 10 mm trong hệ băng (đo khi nó còn nằm trên băng) từ t = 0 tới lúc thành công `[đề xuất]`.

## 3. Vật đích khi thất bại
Lấy theo thứ tự ưu tiên:
1. vật gần TCP nhất (theo phương ngang) lúc bắt đầu pha `CLOSE` đầu tiên;
2. nếu không có `CLOSE`: vật gần điểm đã chọn ở sự kiện `select` đầu tiên (so trong hệ băng);
3. nếu không có cả hai: không có vật đích.

## 4. Nguyên nhân thất bại
Danh sách đóng: `merge, seg_miss, grasp_point, timing, calib, slip, collision, other`. Áp **theo đúng thứ tự dưới đây, lấy quy tắc khớp đầu tiên**.

1. **`collision`**: trước khi bắt đầu `CLOSE` (hoặc tới hết lượt nếu không có `CLOSE`), có một vật bị dịch > 10 mm trong hệ băng khi còn nằm trên băng. Tức tay đã xô vật trước khi kẹp.
2. **`slip`**: vật đích từng được nhấc cao ≥ 5 mm (đáy) nhưng không đạt thành công. Tức đã kẹp được rồi tuột (gồm `dropped_in_hold`).
3. **`merge`**: tại `select`, điểm chọn nằm trong (bán kính bao + 5 mm) của **≥ 2** vật thật. Tức một vùng phát hiện phủ hai vật.
4. **`calib`**: ước lượng mục tiêu **cuối cùng trước `CLOSE`** của phương pháp (sự kiện `freeze` nếu có, nếu không thì `select`) lệch tâm vật gần nhất > 8 mm `[đề xuất]` trong hệ băng, so ở đúng thời điểm của sự kiện đó, và vật đó đứng riêng (không vật nào khác trong vòng 30 mm). Tức hình học ảnh sang mặt băng sai: homography, thị sai chiều cao, độ trễ.
5. Nếu có `CLOSE`, tính độ lệch Δ của TCP so với tâm vật đích lúc bắt đầu `CLOSE`, tách thành Δa (dọc băng) và Δb (ngang băng):
   - **`timing`**: băng chạy, |Δ| > 8 mm và |Δa| ≥ |Δb|;
   - **`grasp_point`**: còn lại. Gồm |Δ| > 8 mm ngang băng, hoặc căn đúng tâm nhưng kẹp rỗng (góc kẹp sai, ví dụ kẹp chéo khối vuông).
6. Không có `CLOSE`:
   - **`seg_miss`**: kết quả `no_target` và phương pháp không có phát hiện hợp lệ nào (`diag.n_ok_dets` = 0, hoặc phương pháp không báo `diag`);
   - **`other`**: kết quả `no_target` mà vẫn có phát hiện hợp lệ. Tức nhận thức thấy vật nhưng chọn vật bỏ qua vì ngoài bản đồ tầm với hay cửa sổ nhặt;
   - **`timing`**: `late`, `timeout`, `hard_timeout`;
   - **`other`**: `ik_fail`, `noop`, `method_exception:*` và mọi kết quả khác.
7. Không khớp quy tắc nào ở trên thì là `other`.

## 5. Thời gian (M5)
- `t_detect_s`: thời điểm sự kiện `select` đầu tiên. Phương pháp không phát `select` thì để trống.
- `t_lift_s`: thời điểm pha `LIFT` đầu tiên. Nếu không có pha này, lấy lúc đáy vật đích lần đầu cao ≥ 5 mm.
- M5 = `t_lift_s − t_detect_s`.

## 6. Kiểm tay
Kiểm tay 30 lượt thất bại (xem video và chuỗi GT), báo tỉ lệ đồng ý với nhãn tự động trong `ARENA_SETUP_REPORT.md`.

## Nhật ký đổi quy tắc
- **29/10/2026, quy tắc 4, trước mọi so sánh phương pháp:** đổi từ "điểm lúc `select`" sang "ước lượng cuối trước `CLOSE` (`freeze`, nếu không có thì `select`)".
  - Lý do: CL-0 còn cập nhật ước lượng sau `select` tới lúc `freeze`, và chỉ sai số **cuối cùng** mới quyết định chỗ tay kẹp.
  - Bằng chứng: chạy thử `runs/e3_smoke` lượt 3 và 9. Hai lượt này đóng băng ở 0,46–0,52 s với sai số 8,4–9,8 mm dọc băng (thị sai của xi lanh cao 40 mm ở a = −150 mm); nhãn không đổi.
  - Chỉ dùng trong lần chạy thử đó, chưa dùng cho số so sánh nào.
