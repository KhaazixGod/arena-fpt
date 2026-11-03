# Nhật ký tinh chỉnh CL-0 trong sim

Chỉ vật DEV và sắp xếp DEV, `engine=isaac`, mỗi lần một thông số. Không mang sang robot thật. Giờ làm việc do người dùng báo; giờ máy ghi riêng và không tính vào hạn 16 giờ.

| Ngày | Thông số | Cũ → mới | Lý do | Bằng chứng | Kết quả | Giờ đã dùng |
|---|---|---|---|---|---|---|
| 2/11 | `perception.grasp.yaw_mode` | `"pca"` → `"local"` | `mug24` 13/30 với CL0, ORACLE 18/19 (`runs/e9_clutter_real`); nút không thuộc CL-0 gốc, người dùng đồng ý thử | `configs/arena_yawlocal.toml`, `runs/e10_yawlocal` | 105/180 so với gốc 107/180, so cặp không ô nào p < 0,05 (thấp nhất dev_C0 L0.25 14 vs 17, p = 0,25); 0/180 không hợp lệ. Không cải thiện → đề xuất không giữ | [chưa báo] |
| 2/11 | `perception.split` | `"none"` → `"watershed"` | 16/20 đống `dev_C3` tĩnh dính thành một khối (`runs/e9_detect_probe`); nút không thuộc CL-0 gốc, người dùng đồng ý thử | `configs/arena_watershed.toml`, `runs/e10_watershed`, `runs/e10_watershed_s70` | a = -40: 112/180 so với gốc 107/180, không ô nào p < 0,05 (C3 L0 4 vs 2, p = 0,5); a = -70: C2 L0 15 vs 15, C3 L0 11 vs 10 so với `runs/e9_static70`; 0/220 không hợp lệ. Không cải thiện rõ → đề xuất không giữ | [chưa báo] |
