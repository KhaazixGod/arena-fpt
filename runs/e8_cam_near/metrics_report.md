Lần chạy e8_cam_near · engine=isaac · 2026-10-31T20:09:02+07:00 · hash arena 1083206e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 (20) | 20 | 100% [84%, 100%] | 100% | — | 2.44/3.86 | 0.6/37.5 |
| CL0 | dev_C0 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.36/2.48 | 0.6/31.3 |
| CL0 | dev_C2 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 65% | — | 2.38/4.77 | 0.6/33.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |
| CL0 | dev_C2 | 0.25 | 0 | 0 | 1 | 0 | 0 | 3 | 2 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 44 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 20/20 = 100% (cần ≥ 80%) -> ĐẠT
- S0b CL0 dev_C0 L0.25: 18/20 = 90% (cần ≥ 80%) -> ĐẠT
