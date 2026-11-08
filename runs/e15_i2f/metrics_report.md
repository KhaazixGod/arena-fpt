Lần chạy e15_i2f · engine=isaac · 2026-11-06T23:56:54+07:00 · hash arena 519767a2 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2F | dev_C2 | 0.25 | 20 (20) | 16 | 80% [58%, 92%] | 80% | — | —/— | 2.9/86.6 |
| REMOTE:ACT_I2F | dev_C2 | 0.5 | 20 (20) | 14 | 70% [48%, 85%] | 60% | — | —/— | 4.8/87.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2F | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| REMOTE:ACT_I2F | dev_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 155 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
