Lần chạy e10_yawlocal · engine=isaac · 2026-11-02T18:38:40+07:00 · hash arena 9139d67f · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 (20) | 11 | 55% [34%, 74%] | 55% | — | 2.40/4.55 | 0.7/45.5 |
| CL0 | dev_C0 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 70% | — | 2.36/2.42 | 0.6/38.6 |
| CL0 | dev_C1 | 0 | 20 (20) | 13 | 65% [43%, 82%] | 65% | — | 2.66/3.05 | 0.6/47.2 |
| CL0 | dev_C1 | 0.25 | 20 (20) | 15 | 75% [53%, 89%] | 75% | — | 2.34/2.40 | 0.6/35.6 |
| CL0 | dev_C2 | 0 | 20 (20) | 15 | 75% [53%, 89%] | 70% | — | 2.50/3.39 | 0.6/35.7 |
| CL0 | dev_C2 | 0.25 | 20 (20) | 16 | 80% [58%, 92%] | 75% | — | 2.39/5.44 | 0.6/38.7 |
| CL0 | dev_C2 | 0.5 | 20 (20) | 7 | 35% [18%, 57%] | 30% | — | 2.38/2.63 | 0.6/44.0 |
| CL0 | dev_C3 | 0 | 20 (20) | 1 | 5% [1%, 24%] | 5% | — | 2.42/2.80 | 27.3/32.3 |
| CL0 | dev_C3 | 0.25 | 20 (20) | 13 | 65% [43%, 82%] | 60% | — | 2.40/3.32 | 0.6/32.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 6 | 3 | 0 | 0 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 1 | 0 | 2 | 3 | 0 | 0 |
| CL0 | dev_C1 | 0 | 0 | 0 | 1 | 0 | 5 | 1 | 0 | 0 |
| CL0 | dev_C1 | 0.25 | 0 | 0 | 0 | 0 | 3 | 2 | 0 | 0 |
| CL0 | dev_C2 | 0 | 0 | 1 | 2 | 0 | 0 | 2 | 0 | 0 |
| CL0 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0 |
| CL0 | dev_C2 | 0.5 | 0 | 0 | 0 | 4 | 0 | 3 | 6 | 0 |
| CL0 | dev_C3 | 0 | 0 | 17 | 0 | 0 | 0 | 2 | 0 | 0 |
| CL0 | dev_C3 | 0.25 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 57 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/180

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 11/20 = 55% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 14/20 = 70% (cần ≥ 80%) -> CHƯA ĐẠT
