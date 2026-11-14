Lần chạy p1_video_042 · engine=isaac · 2026-11-14T18:24:39+07:00 · hash arena af25841d · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C2 | 0.5 | 1 (1) | 0 | 0% [0%, 79%] | 0% | — | 2.42/2.42 | 0.6/14.6 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | train_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |

Chặn dưới/trên: ORACLE train_C2 L0.5 = 0% (n=1)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 80 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/1
