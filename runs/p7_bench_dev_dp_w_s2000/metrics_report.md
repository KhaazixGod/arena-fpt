Lần chạy p7_bench_dev_dp_w_s2000 · engine=isaac · 2026-11-19T22:26:14+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DP_W_S2000 | dev_C0 | 0 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | —/— | 5.5/7.2 |
| REMOTE:DP_W_S2000 | dev_C0 | 0.25 | 10 (10) | 6 | 60% [31%, 83%] | 60% | — | —/— | 5.7/74.5 |
| REMOTE:DP_W_S2000 | dev_C2 | 0 | 10 (10) | 5 | 50% [24%, 76%] | 40% | — | —/— | 5.5/7.5 |
| REMOTE:DP_W_S2000 | dev_C2 | 0.25 | 10 (10) | 6 | 60% [31%, 83%] | 50% | — | —/— | 5.7/76.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DP_W_S2000 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| REMOTE:DP_W_S2000 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| REMOTE:DP_W_S2000 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| REMOTE:DP_W_S2000 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 118 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
