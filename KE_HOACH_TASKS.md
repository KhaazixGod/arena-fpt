# KE_HOACH_TASKS: E18, 40 nhiệm vụ thao tác cho một ACT đa nhiệm vụ (phụ lục post-hoc)

Người dùng chốt ngày 11/11/2026: 40 nhiệm vụ (không phải vật mới), làm ngay, song song với viết luận văn; mô hình = ACT_I2 + mã nhiệm vụ.
Kết quả chính của luận văn vẫn là G2 (NO-GO, `PREREGISTRATION_G2.md`). E18 là phụ lục, báo cáo dù kết quả thế nào.

## 1. Phạm vi (đã chốt để kịp hạn)

- **Băng đứng yên (L0) cho cả 40 nhiệm vụ.** Đẩy/kéo/lật trên băng chạy quá rủi ro trong 3 ngày.
- Vật: 20 vật TRAIN cũ + 6 vật "tháp" mới (cao 45–60 mm, rộng 18–25 mm) để lật được. Danh mục riêng `configs/objects_tasks.json`; `objects_sim.*` không đổi.
- Cách gắp/kẹp luôn thẳng đứng (tilt 90°, như I2); lật = đẩy ngang ở gần đỉnh vật bằng kẹp đã khép.

## 2. 40 nhiệm vụ = 4 họ

| Họ | Biến thể | Số | Thành công (đo từ GT, cuối lượt) |
|---|---|---|---|
| `pick` gắp đúng vật | loại vật đích ∈ {box, cyl, L, T, mug, ring}; cảnh có thêm 1 vật khác loại | 6 | vật ĐÍCH nhấc ≥ 25 mm, giữ ≥ 2 s (luật M1, chỉ tính vật đích) |
| `place` gắp đặt vào vùng | 6 loại × vùng {A: xuôi băng, B: ngược băng} | 12 | vật đích nằm trên băng, đứng thẳng, tâm cách tâm vùng ≤ 25 mm, kẹp đã nhả |
| `pull` kéo trượt (không nhấc) | 6 loại × hướng {về phía robot, xuôi băng}, 50 mm | 12 | dịch ≥ 35 mm theo hướng, lệch ngang ≤ 20 mm, không lúc nào nhấc > 10 mm, đã nhả, còn đứng |
| `topple` lật đổ | {box, cyl} (vật cao) × 4 hướng + mug × 2 hướng | 10 | trục đứng của vật đích nghiêng ≥ 60° |

**Mã nhiệm vụ** (vector 12 chiều, `observation.environment_state` của ACT, không sửa mô hình): họ (one-hot 4) + loại vật (one-hot 6) + tham số 2 chiều (hướng kéo/đẩy hoặc vị trí vùng, đơn vị hệ băng, chuẩn hoá về ±1; `pick` = 0). Câu lệnh tiếng Anh ghi vào trường `task` của LeRobot để đọc, mô hình không dùng.

**Chia TRAIN/TEST:** 32 nhiệm vụ huấn luyện, **8 nhiệm vụ giữ lại** là tổ hợp (họ × loại × tham số) chưa thấy, nhưng từng thành phần đều đã thấy ở nhiệm vụ khác (tổng quát tổ hợp). Danh sách cụ thể chốt sau cổng kiểm (mục 4) và ghi trong `PREREGISTRATION_E18.md`.

## 3. Mã cần viết (tất cả trong `arena/`, không đụng `cl0/`)

1. `arena/tasks.py`: danh sách 40 nhiệm vụ, mã nhiệm vụ, sinh sheet cảnh (JSON: arrangement_id, task_id, vị trí vật).
2. `arena/methods/task_expert.py`: chuyên gia `TASK_EXPERT` (có đặc quyền, như ORACLE): lập điểm tựa trong W từ GT, IK mỗi nhịp, giới hạn tốc độ khớp.
3. `arena/task_labeler.py`: chấm thành công + nguyên nhân hỏng theo họ.
4. `world.py` / `trial.py`: thêm góc nghiêng `tilt` của vật vào GT (cho `topple`).
5. `run_arena.py`: cờ `--tasks` (đọc sheet nhiệm vụ, gửi nhiệm vụ cho phương pháp qua `set_task`, dùng nhãn mới, ghi câu lệnh + mã vào demo).
6. `methods/remote.py`, `remote_server.py`: chuyển `set_task` sang tiến trình ACT.
7. `methods/act_i2.py`: đưa mã nhiệm vụ vào `observation.environment_state` (mặc định tắt: ACT_I2 cũ không đổi hành vi).
8. `to_lerobot_i2.py`: cờ `--task-vec` ghi `observation.environment_state`.

## 4. Thứ tự chạy và cổng

| # | Việc | Ước lượng |
|---|---|---|
| A | Viết mã 1–8 + kiểm không cần Isaac (IK với tới các vùng, sinh sheet) | 11/11 |
| B | Cổng chuyên gia: TASK_EXPERT, 5 cảnh mỗi nhiệm vụ (200 lượt, không render), phải ≥ 4/5 mỗi nhiệm vụ. Không đạt: sửa chuyên gia, hoặc thay/bỏ nhiệm vụ đó (ghi lại) | ~1 giờ máy |
| C | Ghi trước `PREREGISTRATION_E18.md` (danh sách nhiệm vụ, chia TRAIN/TEST, sheet TEST khoá + băm, quy tắc), commit | |
| D | Demo: 32 nhiệm vụ × 25 cảnh, giữ lượt thành công | ~5 giờ máy (2 làn) |
| E | Đổi nhãn I2 + mã nhiệm vụ; huấn luyện `act_i2t_s1000` (100k bước, batch 8) | ~3 giờ |
| F | TEST (lệnh `CONFIRM_TEST=yes` của người dùng): ACT_I2T trên 8 nhiệm vụ giữ lại × 10 cảnh + 32 nhiệm vụ đã học × 5 cảnh mới; TASK_EXPERT và NOOP cùng cảnh | ~7 giờ máy |
| G | Phân tích, bảng cho luận văn | 13/11 sáng |

Không chạy Isaac song song huấn luyện (luật 1). Ô TEST tên bắt đầu bằng `test` nên luôn cần `--allow-locked` (luật 5).

## 5. Quy tắc dự kiến (chốt ở bước C)

- Báo cáo tỉ lệ thành công của ACT_I2T trên nhiệm vụ đã học và nhiệm vụ giữ lại (Wilson 95%), so với TASK_EXPERT (trần) và NOOP (sàn), tách theo họ.
- "Học được nhiều kỹ năng": nhiệm vụ đã học ≥ 50% và mỗi họ ≥ 30%. "Tổng quát tổ hợp": nhiệm vụ giữ lại ≥ 30% và vượt NOOP với p ≤ 0,05 (nhị thức một phía). Ngưỡng [đề xuất], chốt trước khi huấn luyện.
- Một hạt giống (1000); nhiễu giữa các lần chạy ghi theo E16 (3/20 lượt đổi kết quả).

## 6. Rủi ro đã biết

- `topple` với kẹp thẳng đứng có thể không ổn định; `mug` có thể không đổ được (cổng B sẽ cho biết).
- Vùng B (ngược băng) gần mép tầm với; kiểm IK ở bước A.
- Không có baseline module (CL0 chỉ biết gắp-giữ, không nhận câu lệnh): so sánh chỉ với trần chuyên gia và sàn NOOP.
- Kết quả không chuyển sang robot thật trước 22/11.
