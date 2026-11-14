Lần chạy e18_test_held_act · engine=isaac · 2026-11-12T13:25:00+07:00 · hash arena 8fcb74d6 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E18 task catalog configs/objects_tasks.json sha256 34ba91c64208

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2T | test_Theld | 0 | 80 (80) | 58 | 72% [62%, 81%] | 69% | — | —/— | 2.5/4.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2T | test_Theld | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 144 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80
