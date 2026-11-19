Lần chạy p6_test_c2_l05_act_w_s3000 · engine=isaac · 2026-11-19T00:54:55+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_W_S3000 | test_C2 | 0.5 | 60 (60) | 37 | 62% [49%, 73%] | 55% | — | —/— | 3.1/71.6 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_W_S3000 | test_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 6 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 112 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
