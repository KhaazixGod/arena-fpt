Lần chạy p7_bench_dev_act_w_slow_s1000 · engine=isaac · 2026-11-19T19:55:09+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_W_SLOW_S1000 | dev_C0 | 0 | 10 (10) | 9 | 90% [60%, 98%] | 90% | — | —/— | 2.8/69.7 |
| REMOTE:ACT_W_SLOW_S1000 | dev_C0 | 0.25 | 10 (10) | 9 | 90% [60%, 98%] | 90% | — | —/— | 2.9/70.4 |
| REMOTE:ACT_W_SLOW_S1000 | dev_C2 | 0 | 10 (10) | 6 | 60% [31%, 83%] | 60% | — | —/— | 2.8/68.2 |
| REMOTE:ACT_W_SLOW_S1000 | dev_C2 | 0.25 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | —/— | 2.9/71.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_W_SLOW_S1000 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| REMOTE:ACT_W_SLOW_S1000 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| REMOTE:ACT_W_SLOW_S1000 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| REMOTE:ACT_W_SLOW_S1000 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 109 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
