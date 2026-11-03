Lần chạy e10_watershed · engine=isaac · 2026-11-02T18:53:10+07:00 · hash arena 9139d67f · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 (20) | 11 | 55% [34%, 74%] | 55% | — | 2.40/4.40 | 0.6/42.2 |
| CL0 | dev_C0 | 0.25 | 20 (20) | 16 | 80% [58%, 92%] | 80% | — | 2.36/2.65 | 0.6/31.2 |
| CL0 | dev_C1 | 0 | 20 (20) | 15 | 75% [53%, 89%] | 75% | — | 2.67/4.11 | 0.6/41.6 |
| CL0 | dev_C1 | 0.25 | 20 (20) | 15 | 75% [53%, 89%] | 75% | — | 2.34/2.40 | 0.6/30.7 |
| CL0 | dev_C2 | 0 | 20 (20) | 13 | 65% [43%, 82%] | 65% | — | 2.53/3.14 | 0.6/39.9 |
| CL0 | dev_C2 | 0.25 | 20 (20) | 17 | 85% [64%, 95%] | 80% | — | 2.38/5.45 | 0.6/36.6 |
| CL0 | dev_C2 | 0.5 | 20 (20) | 7 | 35% [18%, 57%] | 30% | — | 2.36/2.44 | 0.6/45.2 |
| CL0 | dev_C3 | 0 | 20 (20) | 4 | 20% [8%, 42%] | 15% | — | 2.39/2.79 | 25.9/32.9 |
| CL0 | dev_C3 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 55% | — | 2.36/6.06 | 0.6/37.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 6 | 3 | 0 | 0 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 3 | 1 | 0 | 0 |
| CL0 | dev_C1 | 0 | 0 | 0 | 0 | 0 | 4 | 1 | 0 | 0 |
| CL0 | dev_C1 | 0.25 | 0 | 0 | 0 | 0 | 3 | 2 | 0 | 0 |
| CL0 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 3 | 0 |
| CL0 | dev_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 |
| CL0 | dev_C2 | 0.5 | 0 | 0 | 0 | 2 | 0 | 3 | 8 | 0 |
| CL0 | dev_C3 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| CL0 | dev_C3 | 0.25 | 0 | 0 | 0 | 3 | 0 | 3 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 53 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/180

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 11/20 = 55% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 16/20 = 80% (cần ≥ 80%) -> ĐẠT
