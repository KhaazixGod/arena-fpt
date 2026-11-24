# Nhật ký tinh chỉnh CL-0 trong sim

Chỉ vật DEV và sắp xếp DEV, `engine=isaac`, mỗi lần một thông số. Không mang sang robot thật. Giờ làm việc do người dùng báo; giờ máy ghi riêng và không tính vào hạn 16 giờ.

| Ngày | Thông số | Cũ → mới | Lý do | Bằng chứng | Kết quả | Giờ đã dùng |
|---|---|---|---|---|---|---|
| 2/11 | `perception.grasp.yaw_mode` | `"pca"` → `"local"` | `mug24` 13/30 với CL0, ORACLE 18/19 (`runs/e9_clutter_real`); nút không thuộc CL-0 gốc, người dùng đồng ý thử | `configs/arena_yawlocal.toml`, `runs/e10_yawlocal` | 105/180 so với gốc 107/180, so cặp không ô nào p < 0,05 (thấp nhất dev_C0 L0.25 14 vs 17, p = 0,25); 0/180 không hợp lệ. Không cải thiện → đề xuất không giữ | [chưa báo] |
| 2/11 | `perception.split` | `"none"` → `"watershed"` | 16/20 đống `dev_C3` tĩnh dính thành một khối (`runs/e9_detect_probe`); nút không thuộc CL-0 gốc, người dùng đồng ý thử | `configs/arena_watershed.toml`, `runs/e10_watershed`, `runs/e10_watershed_s70` | a = -40: 112/180 so với gốc 107/180, không ô nào p < 0,05 (C3 L0 4 vs 2, p = 0,5); a = -70: C2 L0 15 vs 15, C3 L0 11 vs 10 so với `runs/e9_static70`; 0/220 không hợp lệ. Không cải thiện rõ → đề xuất không giữ | [chưa báo] |

## 25/11/2026 — M4 v2 (bản sửa duy nhất: nhả cổng hạ có kiểm soát; `m4v2/diffusion_vs2.py`, DEV `scripts/m4v2_dev.sh`, dev_C2 20 cảnh đầu, DP_W seed 1000)

Lý do: chẩn đoán lần TEST M4 v1 (seed 1120): tốc độ hạ tối đa trong lượt thành công trung vị 726 mm/s (M4 v1) so với 148 mm/s (M3); trước vật bị đẩy đầu tiên 486 so với 18 mm/s; vật bị đẩy trung vị 33,2 so với 19,3 mm.
Cổng hạ giữ z ở độ cao pre-grasp rồi nhả đột ngột, kẹp lao xuống theo giới hạn tốc độ khớp. Không đổi gì khác so với v1 (cùng `m4/m4_vs.env`).

Quy tắc chọn cấu hình v2, ghi lúc 00:59 ngày 25/11, trước khi có kết quả của cấu hình `pause` (mọi lần chạy chỉ trên DEV, không đụng sheet khoá):
1. `v2a_vd150` (hạ có giới hạn 150 mm/s) và `v2b_vd250` (250 mm/s) chạy song song. Lúc 00:57, sau 11 và 10 lượt, v2a 7/11 (4 va chạm), v2b 9/10 (1 va chạm); v2a bị dừng tay lúc 00:59 ở 11/20 lượt vì kém hơn rõ và không phải thiết kế ưu tiên (chậm hơn nhịp chính sách: kẹp đóng muộn so với kế hoạch của chính sách).
2. `v2e_pause` (đồng hồ của chính sách tạm dừng trong lúc cổng hạ giữ z; không có tham số mới; chính sách tự hạ với tốc độ vốn có) thay chỗ v2a trên cùng 20 cảnh.
3. v2 = `pause` nếu trên 20 cảnh nó đạt ≥ (số thành công của v2b) − 1 và số lượt hỏng do va chạm ≤ (của v2b) + 1; nếu không, v2 = `rate` 250 mm/s. Không chạy thêm cấu hình nào khác trước khoá.
Kết quả (01:38): v2b (250 mm/s) 16/20, 4 va chạm; v2a (150) dừng ở 7/11; `pause` dừng ở 7/13 (6 hỏng, quy tắc không thể thoả); M3 16/20; M4 v1 18/20 (cùng 20 cảnh). Theo quy tắc: v2 = `rate` 250 mm/s (`m4v2/m4v2.env`). Trên 20 cảnh không biến thể v2 nào hơn v1 hay M3; giả thuyết cơ chế (hạ nhanh gây đẩy vật) không được DEV ủng hộ, chỉ dựa vào chẩn đoán mô tả của TEST cũ. Giờ đã dùng: khoảng 1,3 giờ máy (2 làn), không tính vào hạn 16 giờ.
M1 (`m4v2/kin_cv_ik.py`, không có tham số) chạy thử 10 cảnh dev_C2: 4/10, kết quả `picked_hold_complete` x4, `late` x2, `ik_fail` x1, `dropped_in_hold` x3.
