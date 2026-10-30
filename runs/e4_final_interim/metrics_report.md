Lần chạy e4_final_interim · engine=isaac · 2026-10-29T18:25:15+07:00 · hash arena daf26b4e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: INTERIM primitives (arena/arena/objects.py), not the E5 object set

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| NOOP | dev_C0 | 0 | 20 | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |
| NOOP | dev_C0 | 0.25 | 20 | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |
| ORACLE | dev_C0 | 0 | 20 | 20 | 100% [84%, 100%] | 100% | — | 2.47/2.69 | 0.6/5.1 |
| ORACLE | dev_C0 | 0.25 | 20 | 16 | 80% [58%, 92%] | 80% | — | 2.29/2.36 | 0.6/2.5 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| NOOP | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| NOOP | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |

Chặn dưới/trên: NOOP dev_C0 L0 = 0% (n=20), NOOP dev_C0 L0.25 = 0% (n=20), ORACLE dev_C0 L0 = 100% (n=20), ORACLE dev_C0 L0.25 = 80% (n=20)
Độ lặp lại: chưa đo (dùng --repeat)
Tốc độ: 14 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a NOOP dev_C0 L0: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C0 L0.25: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a ORACLE dev_C0 L0: 20/20 = 100% (cần ≥ 95%) -> ĐẠT
- S0a ORACLE dev_C0 L0.25: 16/20 = 80% (cần ≥ 95%) -> CHƯA ĐẠT
