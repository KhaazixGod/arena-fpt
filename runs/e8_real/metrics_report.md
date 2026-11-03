Lần chạy e8_real · engine=isaac · 2026-10-31T19:23:06+07:00 · hash arena 1083206e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 (20) | 12 | 60% [39%, 78%] | 60% | — | 2.40/4.40 | 0.8/67.2 |
| CL0 | dev_C0 | 0.25 | 20 (20) | 17 | 85% [64%, 95%] | 85% | — | 2.36/2.65 | 0.6/62.2 |
| CL0 | dev_C2 | 0.25 | 20 (20) | 17 | 85% [64%, 95%] | 80% | — | 2.38/5.47 | 0.6/35.3 |
| NOOP | dev_C0 | 0 | 20 (20) | 0 | 0% [0%, 16%] | 0% | -60% (p=0.000; [-80, -40]%, N=20) | —/— | 0.0/0.0 |
| NOOP | dev_C0 | 0.25 | 20 (20) | 0 | 0% [0%, 16%] | 0% | -85% (p=0.000; [-100, -70]%, N=20) | —/— | 0.0/0.0 |
| ORACLE | dev_C0 | 0 | 20 (20) | 20 | 100% [84%, 100%] | 100% | +40% (p=0.008; [20, 60]%, N=20) | 2.41/4.52 | 0.6/14.4 |
| ORACLE | dev_C0 | 0.25 | 20 (20) | 20 | 100% [84%, 100%] | 100% | +15% (p=0.250; [0, 30]%, N=20) | 2.38/2.48 | 0.6/5.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 6 | 2 | 0 | 0 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 |
| CL0 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 0 |
| NOOP | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| NOOP | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: NOOP dev_C0 L0 = 0% (n=20), NOOP dev_C0 L0.25 = 0% (n=20), ORACLE dev_C0 L0 = 100% (n=20), ORACLE dev_C0 L0.25 = 100% (n=20)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 44 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/140

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 12/20 = 60% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 17/20 = 85% (cần ≥ 80%) -> ĐẠT
- S0a NOOP dev_C0 L0: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C0 L0.25: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a ORACLE dev_C0 L0: 20/20 = 100% (cần ≥ 95%) -> ĐẠT
- S0a ORACLE dev_C0 L0.25: 20/20 = 100% (cần ≥ 95%) -> ĐẠT
