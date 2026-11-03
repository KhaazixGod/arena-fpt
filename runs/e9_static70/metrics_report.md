Lần chạy e9_static70 · engine=isaac · 2026-11-01T23:52:00+07:00 · hash arena 1083206e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 (20) | 10 | 50% [30%, 70%] | 50% | — | 2.38/6.29 | 0.6/43.0 |
| CL0 | dev_C1 | 0 | 20 (20) | 11 | 55% [34%, 74%] | 55% | — | 2.80/3.59 | 0.6/41.3 |
| CL0 | dev_C2 | 0 | 20 (20) | 15 | 75% [53%, 89%] | 70% | — | 2.50/5.06 | 0.6/41.1 |
| CL0 | dev_C3 | 0 | 20 (20) | 10 | 50% [30%, 70%] | 50% | — | 2.42/3.09 | 0.6/33.5 |
| ORACLE | dev_C0 | 0 | 20 (20) | 19 | 95% [76%, 99%] | 95% | +45% (p=0.012; [20, 70]%, N=20) | 2.38/2.48 | 0.6/3.5 |
| ORACLE | dev_C1 | 0 | 20 (20) | 20 | 100% [84%, 100%] | 100% | +45% (p=0.004; [25, 65]%, N=20) | 2.47/5.31 | 0.6/14.1 |
| ORACLE | dev_C2 | 0 | 20 (20) | 20 | 100% [84%, 100%] | 95% | +25% (p=0.062; [10, 45]%, N=20) | 2.53/2.85 | 0.6/8.7 |
| ORACLE | dev_C3 | 0 | 20 (20) | 19 | 95% [76%, 99%] | 70% | +45% (p=0.004; [25, 65]%, N=20) | 2.52/2.99 | 0.6/8.5 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 2 | 0 | 6 | 2 | 0 | 0 |
| CL0 | dev_C1 | 0 | 0 | 0 | 1 | 0 | 5 | 3 | 0 | 0 |
| CL0 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 2 |
| CL0 | dev_C3 | 0 | 0 | 3 | 2 | 1 | 0 | 3 | 1 | 0 |
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| ORACLE | dev_C1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

Chặn dưới/trên: ORACLE dev_C0 L0 = 95% (n=20), ORACLE dev_C1 L0 = 100% (n=20), ORACLE dev_C2 L0 = 100% (n=20), ORACLE dev_C3 L0 = 95% (n=20)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 34 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/160

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 10/20 = 50% (cần ≥ 80%) -> CHƯA ĐẠT
- S0a ORACLE dev_C0 L0: 19/20 = 95% (cần ≥ 95%) -> ĐẠT
