Lần chạy e18_pilot_a · engine=isaac · 2026-11-11T14:30:55+07:00 · hash arena 23bcfd3b · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E18 task catalog configs/objects_tasks.json sha256 34ba91c64208

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| TASK_EXPERT | pilot_T | 0 | 100 (100) | 97 | 97% [92%, 99%] | 97% | — | —/— | 0.7/2.5 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK_EXPERT | pilot_T | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 22 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/100
