Lần chạy p5_oracle_dev_c2_l025 · engine=isaac · 2026-11-16T13:16:38+07:00 · hash arena 0603069a · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C2 | 0.25 | 30 (30) | 27 | 90% [74%, 97%] | 83% | — | 2.39/2.45 | 0.6/19.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C2 | 0.25 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 |

Chặn dưới/trên: ORACLE dev_C2 L0.25 = 90% (n=30)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 28 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/30
