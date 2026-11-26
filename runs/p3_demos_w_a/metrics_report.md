Lần chạy p3_demos_w_a · engine=isaac · 2026-11-15T23:43:06+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | train_C0 | 0 | 70 (70) | 56 | 80% [69%, 88%] | 80% | — | 2.40/2.50 | 0.6/3.6 |
| ORACLE_W | train_C0 | 0.25 | 70 (70) | 59 | 84% [74%, 91%] | 84% | — | 2.38/2.46 | 0.6/3.0 |
| ORACLE_W | train_C0 | 0.5 | 70 (70) | 52 | 74% [63%, 83%] | 74% | — | 2.38/2.46 | 0.6/3.0 |
| ORACLE_W | train_C1 | 0 | 70 (70) | 56 | 80% [69%, 88%] | 80% | — | 2.52/2.60 | 0.6/4.9 |
| ORACLE_W | train_C1 | 0.25 | 70 (70) | 60 | 86% [76%, 92%] | 86% | — | 2.38/2.46 | 0.6/2.6 |
| ORACLE_W | train_C1 | 0.5 | 70 (70) | 54 | 77% [66%, 85%] | 77% | — | 2.38/2.46 | 0.6/2.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | train_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 1 | 1 |
| ORACLE_W | train_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 |
| ORACLE_W | train_C0 | 0.5 | 0 | 0 | 0 | 1 | 1 | 16 | 0 | 0 |
| ORACLE_W | train_C1 | 0 | 0 | 0 | 1 | 0 | 0 | 10 | 3 | 0 |
| ORACLE_W | train_C1 | 0.25 | 0 | 0 | 0 | 1 | 0 | 9 | 0 | 0 |
| ORACLE_W | train_C1 | 0.5 | 0 | 0 | 0 | 3 | 0 | 13 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 46 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/420
