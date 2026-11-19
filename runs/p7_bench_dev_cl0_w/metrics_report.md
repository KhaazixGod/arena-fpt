Lần chạy p7_bench_dev_cl0_w · engine=isaac · 2026-11-19T13:11:55+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0_W | dev_C0 | 0 | 10 (10) | 7 | 70% [40%, 89%] | 70% | — | 2.40/2.49 | 0.6/32.0 |
| CL0_W | dev_C0 | 0.25 | 10 (10) | 9 | 90% [60%, 98%] | 90% | — | 2.36/2.41 | 0.6/30.2 |
| CL0_W | dev_C2 | 0 | 10 (10) | 8 | 80% [49%, 94%] | 70% | — | 2.50/2.66 | 0.6/34.5 |
| CL0_W | dev_C2 | 0.25 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | 2.40/2.44 | 0.6/32.7 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0_W | dev_C0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 |
| CL0_W | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| CL0_W | dev_C2 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| CL0_W | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 45 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
