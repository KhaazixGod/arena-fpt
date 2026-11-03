Lần chạy e6_demos_real · engine=isaac · 2026-11-01T13:52:39+07:00 · hash arena 1083206e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C0 | 0 | 70 (70) | 52 | 74% [63%, 83%] | 74% | — | 2.42/4.20 | 0.6/12.5 |
| ORACLE | train_C0 | 0.25 | 70 (70) | 55 | 79% [68%, 87%] | 79% | — | 2.38/2.46 | 0.6/3.3 |
| ORACLE | train_C1 | 0 | 70 (70) | 54 | 77% [66%, 85%] | 77% | — | 2.54/3.45 | 0.6/12.5 |
| ORACLE | train_C1 | 0.25 | 70 (70) | 56 | 80% [69%, 88%] | 80% | — | 2.38/2.46 | 0.6/3.2 |
| ORACLE | train_C2 | 0 | 70 (70) | 59 | 84% [74%, 91%] | 81% | — | 2.60/3.43 | 0.6/13.2 |
| ORACLE | train_C2 | 0.25 | 70 (70) | 58 | 83% [72%, 90%] | 81% | — | 2.36/2.42 | 0.6/3.4 |
| ORACLE | train_C3 | 0 | 70 (70) | 56 | 80% [69%, 88%] | 67% | — | 2.60/5.16 | 0.6/14.3 |
| ORACLE | train_C3 | 0.25 | 70 (70) | 54 | 77% [66%, 85%] | 67% | — | 2.40/2.73 | 0.6/4.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 2 | 3 |
| ORACLE | train_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 15 | 0 | 0 |
| ORACLE | train_C1 | 0 | 0 | 0 | 1 | 0 | 0 | 12 | 3 | 0 |
| ORACLE | train_C1 | 0.25 | 0 | 0 | 0 | 1 | 0 | 13 | 0 | 0 |
| ORACLE | train_C2 | 0 | 0 | 0 | 2 | 0 | 0 | 7 | 2 | 0 |
| ORACLE | train_C2 | 0.25 | 0 | 0 | 2 | 2 | 0 | 8 | 0 | 0 |
| ORACLE | train_C3 | 0 | 0 | 0 | 3 | 0 | 0 | 4 | 7 | 0 |
| ORACLE | train_C3 | 0.25 | 0 | 0 | 4 | 2 | 0 | 6 | 4 | 0 |

Chặn dưới/trên: ORACLE train_C0 L0 = 74% (n=70), ORACLE train_C0 L0.25 = 79% (n=70), ORACLE train_C1 L0 = 77% (n=70), ORACLE train_C1 L0.25 = 80% (n=70), ORACLE train_C2 L0 = 84% (n=70), ORACLE train_C2 L0.25 = 83% (n=70), ORACLE train_C3 L0 = 80% (n=70), ORACLE train_C3 L0.25 = 77% (n=70)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 128 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/560

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a ORACLE train_C0 L0: 52/70 = 74% (cần ≥ 95%) -> CHƯA ĐẠT
- S0a ORACLE train_C0 L0.25: 55/70 = 79% (cần ≥ 95%) -> CHƯA ĐẠT
