Lần chạy p1_slip_C_vz60 · engine=isaac · 2026-11-14T15:02:45+07:00 · hash arena 49a7505d · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C2 | 0.5 | 60 (60) | 40 | 67% [54%, 77%] | 60% | — | 2.60/2.66 | 0.6/17.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C2 | 0.5 | 0 | 0 | 2 | 1 | 0 | 10 | 7 | 0 |

Chặn dưới/trên: ORACLE train_C2 L0.5 = 67% (n=60)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 24 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
