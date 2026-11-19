Lần chạy p7_bench_dev_act_old_s1000 · engine=isaac · 2026-11-19T13:43:10+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_OLD_S1000 | dev_C0 | 0 | 10 (10) | 5 | 50% [24%, 76%] | 50% | — | —/— | 2.7/66.6 |
| REMOTE:ACT_OLD_S1000 | dev_C0 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | —/— | 3.0/71.0 |
| REMOTE:ACT_OLD_S1000 | dev_C2 | 0 | 10 (10) | 6 | 60% [31%, 83%] | 60% | — | —/— | 2.7/48.7 |
| REMOTE:ACT_OLD_S1000 | dev_C2 | 0.25 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | —/— | 3.0/71.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_OLD_S1000 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 2 |
| REMOTE:ACT_OLD_S1000 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| REMOTE:ACT_OLD_S1000 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| REMOTE:ACT_OLD_S1000 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 107 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
