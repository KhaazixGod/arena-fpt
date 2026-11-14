Lần chạy e15_i2_r100 · engine=isaac · 2026-11-06T19:58:53+07:00 · hash arena 519767a2 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2 | dev_C3 | 0.25 | 20 (20) | 10 | 50% [30%, 70%] | 50% | — | —/— | 2.9/88.7 |
| REMOTE:ACT_I2 | dev_C3 | 0.5 | 20 (20) | 9 | 45% [26%, 66%] | 40% | — | —/— | 72.5/92.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2 | dev_C3 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 2 |
| REMOTE:ACT_I2 | dev_C3 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 2 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 154 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
