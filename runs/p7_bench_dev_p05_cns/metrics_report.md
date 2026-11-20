Lần chạy p7_bench_dev_p05_cns · engine=isaac · 2026-11-20T04:47:19+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P05_CNS | dev_C0 | 0 | 10 (10) | 1 | 10% [2%, 40%] | 10% | — | 2.42/2.62 | 0.7/111.8 |
| P05_CNS | dev_C0 | 0.25 | 10 (10) | 5 | 50% [24%, 76%] | 50% | — | 2.40/2.40 | 0.6/113.1 |
| P05_CNS | dev_C2 | 0 | 10 (10) | 5 | 50% [24%, 76%] | 50% | — | 2.40/2.61 | 0.7/114.5 |
| P05_CNS | dev_C2 | 0.25 | 10 (10) | 6 | 60% [31%, 83%] | 60% | — | 2.43/3.13 | 0.7/302.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P05_CNS | dev_C0 | 0 | 0 | 0 | 0 | 0 | 6 | 3 | 0 | 0 |
| P05_CNS | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 |
| P05_CNS | dev_C2 | 0 | 0 | 0 | 3 | 0 | 0 | 1 | 1 | 0 |
| P05_CNS | dev_C2 | 0.25 | 0 | 0 | 0 | 2 | 0 | 1 | 1 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 68 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
