Lần chạy e16_commit_c23 · engine=isaac · 2026-11-08T14:29:32+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2_COMMIT | dev_C2 | 0.25 | 20 (20) | 13 | 65% [43%, 82%] | 65% | — | —/— | 3.6/92.0 |
| REMOTE:ACT_I2_COMMIT | dev_C2 | 0.5 | 20 (20) | 9 | 45% [26%, 66%] | 45% | — | —/— | 72.1/93.7 |
| REMOTE:ACT_I2_COMMIT | dev_C3 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 60% | — | —/— | 3.0/79.4 |
| REMOTE:ACT_I2_COMMIT | dev_C3 | 0.5 | 20 (20) | 5 | 25% [11%, 47%] | 25% | — | —/— | 65.3/92.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2_COMMIT | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| REMOTE:ACT_I2_COMMIT | dev_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 |
| REMOTE:ACT_I2_COMMIT | dev_C3 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| REMOTE:ACT_I2_COMMIT | dev_C3 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 155 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80
