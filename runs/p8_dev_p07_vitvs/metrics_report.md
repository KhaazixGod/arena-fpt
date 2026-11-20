Lần chạy p8_dev_p07_vitvs · engine=isaac · 2026-11-20T08:08:30+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P07_VITVS | dev_C2 | 0.5 | 20 (20) | 8 | 40% [22%, 61%] | 40% | — | 2.38/2.47 | 9.2/133.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P07_VITVS | dev_C2 | 0.5 | 0 | 0 | 0 | 1 | 0 | 0 | 9 | 2 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 70 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/20
