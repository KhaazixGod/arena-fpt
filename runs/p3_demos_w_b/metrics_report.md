Lần chạy p3_demos_w_b · engine=isaac · 2026-11-16T01:10:12+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | train_C2 | 0 | 70 (70) | 61 | 87% [77%, 93%] | 84% | — | 2.56/2.66 | 0.6/7.5 |
| ORACLE_W | train_C2 | 0.25 | 70 (70) | 60 | 86% [76%, 92%] | 84% | — | 2.36/2.42 | 0.6/3.3 |
| ORACLE_W | train_C2 | 0.5 | 70 (70) | 57 | 81% [71%, 89%] | 80% | — | 2.36/2.42 | 0.6/3.3 |
| ORACLE_W | train_C3 | 0 | 70 (70) | 56 | 80% [69%, 88%] | 69% | — | 2.58/3.24 | 0.6/7.2 |
| ORACLE_W | train_C3 | 0.25 | 70 (70) | 54 | 77% [66%, 85%] | 69% | — | 2.40/2.74 | 0.6/3.9 |
| ORACLE_W | train_C3 | 0.5 | 70 (70) | 52 | 74% [63%, 83%] | 61% | — | 2.38/2.42 | 0.6/4.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | train_C2 | 0 | 0 | 0 | 2 | 0 | 0 | 5 | 2 | 0 |
| ORACLE_W | train_C2 | 0.25 | 0 | 0 | 2 | 2 | 0 | 6 | 0 | 0 |
| ORACLE_W | train_C2 | 0.5 | 0 | 0 | 2 | 2 | 0 | 9 | 0 | 0 |
| ORACLE_W | train_C3 | 0 | 0 | 0 | 3 | 0 | 0 | 3 | 8 | 0 |
| ORACLE_W | train_C3 | 0.25 | 0 | 0 | 3 | 2 | 0 | 6 | 5 | 0 |
| ORACLE_W | train_C3 | 0.5 | 0 | 0 | 2 | 2 | 0 | 8 | 6 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 46 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/420
