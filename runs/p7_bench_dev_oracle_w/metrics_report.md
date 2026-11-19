Lần chạy p7_bench_dev_oracle_w · engine=isaac · 2026-11-19T12:48:26+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | dev_C0 | 0 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.41/2.49 | 0.7/3.8 |
| ORACLE_W | dev_C0 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.38/2.41 | 0.7/3.2 |
| ORACLE_W | dev_C2 | 0 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.56/2.67 | 0.7/9.0 |
| ORACLE_W | dev_C2 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.41/2.44 | 0.7/3.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE_W | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE_W | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE_W | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 31 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
