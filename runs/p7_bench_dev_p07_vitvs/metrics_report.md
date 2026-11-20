Lần chạy p7_bench_dev_p07_vitvs · engine=isaac · 2026-11-20T05:33:36+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P07_VITVS | dev_C0 | 0 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | 2.42/3.80 | 0.7/110.7 |
| P07_VITVS | dev_C0 | 0.25 | 10 (10) | 6 | 60% [31%, 83%] | 60% | — | 2.38/2.44 | 0.7/107.9 |
| P07_VITVS | dev_C2 | 0 | 10 (10) | 8 | 80% [49%, 94%] | 60% | — | 2.59/4.45 | 0.7/117.5 |
| P07_VITVS | dev_C2 | 0.25 | 10 (10) | 7 | 70% [40%, 89%] | 70% | — | 2.36/5.02 | 0.7/117.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P07_VITVS | dev_C0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| P07_VITVS | dev_C0 | 0.25 | 0 | 0 | 0 | 1 | 1 | 2 | 0 | 0 |
| P07_VITVS | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| P07_VITVS | dev_C2 | 0.25 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 80 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
