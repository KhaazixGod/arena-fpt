Lần chạy e3_repeat_cl0 · engine=isaac · 2026-10-30T16:51:25+07:00 · hash arena 278cef06 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: INTERIM primitives (arena/arena/objects.py), not the E5 object set

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 40 | 30 | 75% [60%, 86%] | 75% | — | 2.46/2.88 | 0.7/32.1 |
| CL0 | dev_C0 | 0.25 | 40 | 24 | 60% [45%, 74%] | 60% | — | 2.30/2.36 | 0.6/29.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 2 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 6 | 0 | 4 | 6 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: CL0: 40/40 nhóm lặp cùng kết quả
Tốc độ: 38 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 30/40 = 75% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 24/40 = 60% (cần ≥ 80%) -> CHƯA ĐẠT
