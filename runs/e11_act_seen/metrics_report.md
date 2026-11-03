Lần chạy e11_act_seen · engine=isaac · 2026-11-03T00:56:28+07:00 · hash arena 6d652a13 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | seen_C0 | 0 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.41/2.48 | 0.6/3.2 |
| ORACLE | seen_C0 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.40/2.42 | 0.6/2.9 |
| ORACLE | seen_C1 | 0 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.56/3.05 | 0.6/12.5 |
| ORACLE | seen_C1 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.38/2.48 | 0.6/3.6 |
| REMOTE:ACT_J0 | seen_C0 | 0 | 20 (20) | 16 | 80% [58%, 92%] | 80% | — | —/— | 5.4/16.0 |
| REMOTE:ACT_J0 | seen_C0 | 0.25 | 20 (20) | 15 | 75% [53%, 89%] | 75% | — | —/— | 5.4/15.8 |
| REMOTE:ACT_J0 | seen_C1 | 0 | 20 (20) | 14 | 70% [48%, 85%] | 70% | — | —/— | 5.4/15.6 |
| REMOTE:ACT_J0 | seen_C1 | 0.25 | 20 (20) | 10 | 50% [30%, 70%] | 50% | — | —/— | 5.4/15.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | seen_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| ORACLE | seen_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| ORACLE | seen_C1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| ORACLE | seen_C1 | 0.25 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| REMOTE:ACT_J0 | seen_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| REMOTE:ACT_J0 | seen_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| REMOTE:ACT_J0 | seen_C1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| REMOTE:ACT_J0 | seen_C1 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 |

Chặn dưới/trên: ORACLE seen_C0 L0 = 90% (n=20), ORACLE seen_C0 L0.25 = 90% (n=20), ORACLE seen_C1 L0 = 90% (n=20), ORACLE seen_C1 L0.25 = 90% (n=20)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 81 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/160

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a ORACLE seen_C0 L0: 18/20 = 90% (cần ≥ 95%) -> CHƯA ĐẠT
- S0a ORACLE seen_C0 L0.25: 18/20 = 90% (cần ≥ 95%) -> CHƯA ĐẠT
