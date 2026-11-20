Lần chạy p8_dev_p17_odil · engine=isaac · 2026-11-20T08:54:53+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P17_ODIL | dev_C2 | 0.5 | 20 (20) | 7 | 35% [18%, 57%] | 35% | — | 2.36/2.46 | 0.7/204.7 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P17_ODIL | dev_C2 | 0.5 | 0 | 0 | 0 | 1 | 0 | 4 | 8 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 73 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/20
