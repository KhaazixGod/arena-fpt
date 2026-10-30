Lần chạy e4_cl0_interim · engine=isaac · 2026-10-29T19:51:25+07:00 · hash arena daf26b4e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: INTERIM primitives (arena/arena/objects.py), not the E5 object set

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 | 14 | 70% [48%, 85%] | 70% | — | 2.46/2.79 | 0.6/30.0 |
| CL0 | dev_C0 | 0.25 | 20 | 11 | 55% [34%, 74%] | 55% | — | 2.30/2.36 | 0.6/28.0 |
| CL0_YAW | dev_C0 | 0 | 20 | 15 | 75% [53%, 89%] | 75% | +5% (p=1.000; [0, 15]%, N=20) | 2.46/2.88 | 0.6/31.4 |
| CL0_YAW | dev_C0 | 0.25 | 20 | 12 | 60% [39%, 78%] | 60% | +5% (p=1.000; [0, 15]%, N=20) | 2.30/2.36 | 0.6/29.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 1 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 4 | 0 | 2 | 3 | 0 | 0 |
| CL0_YAW | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 2 |
| CL0_YAW | dev_C0 | 0.25 | 0 | 0 | 2 | 0 | 3 | 3 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat)
Tốc độ: 36 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 14/20 = 70% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 11/20 = 55% (cần ≥ 80%) -> CHƯA ĐẠT
