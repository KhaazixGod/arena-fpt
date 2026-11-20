Lần chạy p8_dev_p07_vitvs_w · engine=isaac · 2026-11-20T08:32:42+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P07_VITVS_W | dev_C2 | 0.5 | 20 (20) | 13 | 65% [43%, 82%] | 60% | — | 2.40/2.48 | 0.7/106.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P07_VITVS_W | dev_C2 | 0.5 | 0 | 0 | 1 | 3 | 0 | 2 | 1 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 64 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/20
