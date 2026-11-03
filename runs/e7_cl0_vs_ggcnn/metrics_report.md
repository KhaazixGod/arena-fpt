Lần chạy e7_cl0_vs_ggcnn · engine=isaac · 2026-10-31T16:08:40+07:00 · hash arena c07f59c6 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 20 (20) | 17 | 85% [64%, 95%] | 85% | — | 2.48/2.98 | 0.6/34.9 |
| CL0 | dev_C0 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.32/2.40 | 0.6/34.0 |
| CL0 | dev_C2 | 0 | 20 (20) | 17 | 85% [64%, 95%] | 85% | — | 2.74/4.97 | 0.6/44.0 |
| CL0 | dev_C2 | 0.25 | 20 (20) | 15 | 75% [53%, 89%] | 60% | — | 2.34/5.60 | 0.6/39.4 |
| GGCNN | dev_C0 | 0 | 20 (20) | 18 | 90% [70%, 97%] | 90% | +5% (p=1.000; [-10, 20]%, N=20) | 2.48/2.55 | 0.6/20.3 |
| GGCNN | dev_C0 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 90% | +0% (p=1.000; [-20, 20]%, N=20) | 2.31/2.40 | 0.6/18.1 |
| GGCNN | dev_C2 | 0 | 20 (20) | 14 | 70% [48%, 85%] | 70% | -15% (p=0.508; [-45, 15]%, N=20) | 2.72/2.86 | 0.6/26.0 |
| GGCNN | dev_C2 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 80% | +15% (p=0.453; [-10, 40]%, N=20) | 2.30/2.39 | 0.6/15.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 |
| CL0 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| CL0 | dev_C2 | 0.25 | 0 | 0 | 1 | 0 | 0 | 3 | 1 | 0 |
| GGCNN | dev_C0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| GGCNN | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| GGCNN | dev_C2 | 0 | 0 | 0 | 1 | 1 | 0 | 4 | 0 | 0 |
| GGCNN | dev_C2 | 0.25 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 47 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/160

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 17/20 = 85% (cần ≥ 80%) -> ĐẠT
- S0b CL0 dev_C0 L0.25: 18/20 = 90% (cần ≥ 80%) -> ĐẠT
