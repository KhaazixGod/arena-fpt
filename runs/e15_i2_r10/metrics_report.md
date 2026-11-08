Lần chạy e15_i2_r10 · engine=isaac · 2026-11-06T17:27:50+07:00 · hash arena 519767a2 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2_R10 | dev_C2 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 70% | — | —/— | 3.0/90.0 |
| REMOTE:ACT_I2_R10 | dev_C2 | 0.5 | 20 (20) | 6 | 30% [15%, 52%] | 25% | — | —/— | 75.6/94.0 |
| REMOTE:ACT_I2_R10 | dev_C3 | 0.25 | 20 (20) | 16 | 80% [58%, 92%] | 70% | — | —/— | 3.1/89.0 |
| REMOTE:ACT_I2_R10 | dev_C3 | 0.5 | 20 (20) | 3 | 15% [5%, 36%] | 5% | — | —/— | 73.0/96.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2_R10 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| REMOTE:ACT_I2_R10 | dev_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 2 |
| REMOTE:ACT_I2_R10 | dev_C3 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| REMOTE:ACT_I2_R10 | dev_C3 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 175 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80
