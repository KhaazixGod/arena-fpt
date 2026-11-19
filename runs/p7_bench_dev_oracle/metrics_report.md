Lần chạy p7_bench_dev_oracle · engine=isaac · 2026-11-19T12:26:50+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C0 | 0 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.41/3.55 | 0.7/11.0 |
| ORACLE | dev_C0 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.38/2.41 | 0.7/3.8 |
| ORACLE | dev_C2 | 0 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.58/3.46 | 0.7/15.4 |
| ORACLE | dev_C2 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 90% | — | 2.41/2.44 | 0.7/4.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: ORACLE dev_C0 L0 = 100% (n=10), ORACLE dev_C0 L0.25 = 100% (n=10), ORACLE dev_C2 L0 = 100% (n=10), ORACLE dev_C2 L0.25 = 100% (n=10)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 31 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a ORACLE dev_C0 L0: 10/10 = 100% (cần ≥ 95%) -> ĐẠT
- S0a ORACLE dev_C0 L0.25: 10/10 = 100% (cần ≥ 95%) -> ĐẠT
