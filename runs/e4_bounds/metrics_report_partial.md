Lần chạy e4_bounds · engine=isaac · 2026-10-29T17:18:05+07:00 · hash arena e70f38ba · Isaac 6.0.0.1 · cl0 006af1c9 · vật: INTERIM primitives (arena/arena/objects.py), not the E5 object set

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| NOOP | dev_C0 | 0 | 10 | 0 | 0% [0%, 28%] | 0% | — | —/— | 0.0/0.0 |
| NOOP | dev_C0 | 0.25 | 9 | 0 | 0% [0%, 30%] | 0% | — | —/— | 0.0/0.0 |
| ORACLE | dev_C0 | 0 | 9 | 8 | 89% [57%, 98%] | 89% | — | 2.46/3.73 | 0.7/9.6 |
| ORACLE | dev_C0 | 0.25 | 9 | 6 | 67% [35%, 88%] | 67% | — | 2.28/2.35 | 0.7/2.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| NOOP | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 |
| NOOP | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| ORACLE | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |

Chặn dưới/trên: NOOP dev_C0 L0 = 0% (n=10), NOOP dev_C0 L0.25 = 0% (n=9), ORACLE dev_C0 L0 = 89% (n=9), ORACLE dev_C0 L0.25 = 67% (n=9)
Độ lặp lại: chưa đo (dùng --repeat)
Tốc độ: 15 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/37

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a NOOP dev_C0 L0: 0/10 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C0 L0.25: 0/9 = 0% (cần ≈ 0%) -> ĐẠT
- S0a ORACLE dev_C0 L0: 8/9 = 89% (cần ≥ 95%) -> CHƯA ĐẠT
- S0a ORACLE dev_C0 L0.25: 6/9 = 67% (cần ≥ 95%) -> CHƯA ĐẠT
