Lần chạy p7_bench_dev_p19_act_te_s2000 · engine=isaac · 2026-11-20T06:55:41+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:P19_ACT_TE_S2000 | dev_C0 | 0 | 10 (10) | 9 | 90% [60%, 98%] | 90% | — | —/— | 14.5/26.6 |
| REMOTE:P19_ACT_TE_S2000 | dev_C0 | 0.25 | 10 (10) | 7 | 70% [40%, 89%] | 70% | — | —/— | 14.2/24.8 |
| REMOTE:P19_ACT_TE_S2000 | dev_C2 | 0 | 10 (10) | 5 | 50% [24%, 76%] | 50% | — | —/— | 14.5/26.9 |
| REMOTE:P19_ACT_TE_S2000 | dev_C2 | 0.25 | 10 (10) | 3 | 30% [11%, 60%] | 30% | — | —/— | 14.6/26.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:P19_ACT_TE_S2000 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| REMOTE:P19_ACT_TE_S2000 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| REMOTE:P19_ACT_TE_S2000 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 |
| REMOTE:P19_ACT_TE_S2000 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 151 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
