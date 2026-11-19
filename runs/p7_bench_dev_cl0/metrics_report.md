Lần chạy p7_bench_dev_cl0 · engine=isaac · 2026-11-19T12:25:49+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 10 (10) | 7 | 70% [40%, 89%] | 70% | — | 2.40/3.85 | 0.7/47.3 |
| CL0 | dev_C0 | 0.25 | 10 (10) | 9 | 90% [60%, 98%] | 90% | — | 2.36/2.41 | 0.7/34.6 |
| CL0 | dev_C2 | 0 | 10 (10) | 6 | 60% [31%, 83%] | 60% | — | 2.55/3.88 | 0.7/43.3 |
| CL0 | dev_C2 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 90% | — | 2.41/5.69 | 0.6/44.7 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| CL0 | dev_C2 | 0 | 0 | 1 | 0 | 0 | 0 | 2 | 1 | 0 |
| CL0 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 68 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 7/10 = 70% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 9/10 = 90% (cần ≥ 80%) -> ĐẠT
