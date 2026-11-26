Lần chạy p2_oraclew_train_c3_l05 · engine=isaac · 2026-11-15T17:14:37+07:00 · hash arena cbf1d6e6 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | train_C3 | 0.5 | 60 (60) | 44 | 73% [61%, 83%] | 58% | — | 2.38/2.43 | 0.7/4.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE_W | train_C3 | 0.5 | 0 | 0 | 0 | 2 | 0 | 8 | 6 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 28 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
