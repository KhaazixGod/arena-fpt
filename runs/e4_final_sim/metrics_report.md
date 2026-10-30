Lần chạy e4_final_sim · engine=isaac · 2026-10-29T18:44:56+07:00 · hash arena daf26b4e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| NOOP | dev_C0 | 0 | 20 | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |
| NOOP | dev_C0 | 0.25 | 20 | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |
| NOOP | dev_C2 | 0 | 20 | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |
| NOOP | dev_C2 | 0.25 | 20 | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |
| ORACLE | dev_C0 | 0 | 20 | 19 | 95% [76%, 99%] | 95% | — | 2.52/2.93 | 0.6/12.9 |
| ORACLE | dev_C0 | 0.25 | 20 | 18 | 90% [70%, 97%] | 90% | — | 2.30/2.40 | 0.6/3.8 |
| ORACLE | dev_C2 | 0 | 20 | 20 | 100% [84%, 100%] | 100% | — | 2.73/4.17 | 0.6/14.0 |
| ORACLE | dev_C2 | 0.25 | 20 | 18 | 90% [70%, 97%] | 85% | — | 2.32/2.36 | 0.6/14.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| NOOP | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| NOOP | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| NOOP | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| NOOP | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |
| ORACLE | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| ORACLE | dev_C0 | 0.25 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ORACLE | dev_C2 | 0.25 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |

Chặn dưới/trên: NOOP dev_C0 L0 = 0% (n=20), NOOP dev_C0 L0.25 = 0% (n=20), NOOP dev_C2 L0 = 0% (n=20), NOOP dev_C2 L0.25 = 0% (n=20), ORACLE dev_C0 L0 = 95% (n=20), ORACLE dev_C0 L0.25 = 90% (n=20), ORACLE dev_C2 L0 = 100% (n=20), ORACLE dev_C2 L0.25 = 90% (n=20)
Độ lặp lại: chưa đo (dùng --repeat)
Tốc độ: 25 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/160

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a NOOP dev_C0 L0: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C0 L0.25: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C2 L0: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a NOOP dev_C2 L0.25: 0/20 = 0% (cần ≈ 0%) -> ĐẠT
- S0a ORACLE dev_C0 L0: 19/20 = 95% (cần ≥ 95%) -> ĐẠT
- S0a ORACLE dev_C0 L0.25: 18/20 = 90% (cần ≥ 95%) -> CHƯA ĐẠT
