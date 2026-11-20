Lần chạy p7_bench_dev_p17_odil · engine=isaac · 2026-11-20T06:27:46+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P17_ODIL | dev_C0 | 0 | 10 (10) | 7 | 70% [40%, 89%] | 70% | — | 2.40/4.04 | 0.7/127.8 |
| P17_ODIL | dev_C0 | 0.25 | 10 (10) | 8 | 80% [49%, 94%] | 80% | — | 2.38/6.31 | 0.7/106.1 |
| P17_ODIL | dev_C2 | 0 | 10 (10) | 8 | 80% [49%, 94%] | 70% | — | 2.56/3.05 | 0.7/219.9 |
| P17_ODIL | dev_C2 | 0.25 | 10 (10) | 7 | 70% [40%, 89%] | 70% | — | 2.41/2.46 | 0.7/185.6 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P17_ODIL | dev_C0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 0 | 0 |
| P17_ODIL | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| P17_ODIL | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| P17_ODIL | dev_C2 | 0.25 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 77 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
