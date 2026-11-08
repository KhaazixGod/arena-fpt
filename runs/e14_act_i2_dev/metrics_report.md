Lần chạy e14_act_i2_dev · engine=isaac · 2026-11-05T21:03:20+07:00 · hash arena 7ca6903e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2 | dev_C0 | 0 | 20 (20) | 11 | 55% [34%, 74%] | 55% | — | —/— | 2.7/75.5 |
| REMOTE:ACT_I2 | dev_C0 | 0.25 | 20 (20) | 19 | 95% [76%, 99%] | 95% | — | —/— | 2.9/85.9 |
| REMOTE:ACT_I2 | dev_C1 | 0 | 20 (20) | 9 | 45% [26%, 66%] | 45% | — | —/— | 2.7/78.1 |
| REMOTE:ACT_I2 | dev_C1 | 0.25 | 20 (20) | 11 | 55% [34%, 74%] | 55% | — | —/— | 2.9/85.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 4 |
| REMOTE:ACT_I2 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| REMOTE:ACT_I2 | dev_C1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 2 |
| REMOTE:ACT_I2 | dev_C1 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 139 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80
