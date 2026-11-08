Lần chạy e15_demos_fast · engine=isaac · 2026-11-06T17:26:25+07:00 · hash arena 519767a2 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C2 | 0.5 | 60 (60) | 41 | 68% [56%, 79%] | 65% | — | 2.36/2.42 | 0.6/22.8 |
| ORACLE | train_C3 | 0.5 | 60 (60) | 35 | 58% [46%, 70%] | 42% | — | 2.38/2.46 | 0.6/27.7 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C2 | 0.5 | 0 | 0 | 2 | 1 | 0 | 12 | 4 | 0 |
| ORACLE | train_C3 | 0.5 | 0 | 0 | 3 | 2 | 0 | 10 | 10 | 0 |

Chặn dưới/trên: ORACLE train_C2 L0.5 = 68% (n=60), ORACLE train_C3 L0.5 = 58% (n=60)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 58 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/120
