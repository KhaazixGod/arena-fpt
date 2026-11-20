Lần chạy p7_bench_dev_p19_act_te_s3000 · engine=isaac · 2026-11-20T09:43:21+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:P19_ACT_TE_S3000 | dev_C0 | 0 | 10 (10) | 9 | 90% [60%, 98%] | 90% | — | —/— | 14.5/27.4 |
| REMOTE:P19_ACT_TE_S3000 | dev_C0 | 0.25 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | —/— | 14.4/27.0 |
| REMOTE:P19_ACT_TE_S3000 | dev_C2 | 0 | 10 (10) | 4 | 40% [17%, 69%] | 40% | — | —/— | 14.5/28.0 |
| REMOTE:P19_ACT_TE_S3000 | dev_C2 | 0.25 | 10 (10) | 3 | 30% [11%, 60%] | 20% | — | —/— | 14.4/27.0 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:P19_ACT_TE_S3000 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| REMOTE:P19_ACT_TE_S3000 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| REMOTE:P19_ACT_TE_S3000 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| REMOTE:P19_ACT_TE_S3000 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 150 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
