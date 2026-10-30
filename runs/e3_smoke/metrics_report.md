Lần chạy e3_smoke · engine=isaac · 2026-10-29T17:06:34+07:00 · hash arena 05b61b28 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: INTERIM primitives (arena/arena/objects.py), not the E5 object set

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 2 | 1 | 50% [9%, 91%] | 50% | — | 2.40/2.40 | 13.9/30.3 |
| CL0 | dev_C0 | 0.25 | 2 | 0 | 0% [0%, 66%] | 0% | — | 2.22/2.26 | 0.7/27.7 |
| NOOP | dev_C0 | 0 | 2 | 0 | 0% [0%, 66%] | 0% | -50% (p=1.000; [-100, 0]%, N=2) | —/— | 0.0/0.0 |
| NOOP | dev_C0 | 0.25 | 2 | 0 | 0% [0%, 66%] | 0% | +0% (p=1.000; [0, 0]%, N=2) | —/— | 0.0/0.0 |
| ORACLE | dev_C0 | 0 | 2 | 1 | 50% [9%, 91%] | 50% | +0% (p=1.000; [0, 0]%, N=2) | 2.40/2.40 | 1.0/4.2 |
| ORACLE | dev_C0 | 0.25 | 2 | 1 | 50% [9%, 91%] | 50% | +50% (p=1.000; [0, 100]%, N=2) | 2.32/2.32 | 0.6/3.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| NOOP | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| NOOP | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| ORACLE | dev_C0 | 0.25 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: NOOP dev_C0 L0 = 0% (n=2), NOOP dev_C0 L0.25 = 0% (n=2), ORACLE dev_C0 L0 = 50% (n=2), ORACLE dev_C0 L0.25 = 50% (n=2)
Độ lặp lại: chưa đo (dùng --repeat)
Tốc độ: 53 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/12

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 1/2 = 50% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 0/2 = 0% (cần ≥ 80%) -> CHƯA ĐẠT
- S0a NOOP dev_C0 L0: 0/2 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C0 L0.25: 0/2 = 0% (cần ≈ 0%) -> ĐẠT
- S0a ORACLE dev_C0 L0: 1/2 = 50% (cần ≥ 95%) -> CHƯA ĐẠT
- S0a ORACLE dev_C0 L0.25: 1/2 = 50% (cần ≥ 95%) -> CHƯA ĐẠT
