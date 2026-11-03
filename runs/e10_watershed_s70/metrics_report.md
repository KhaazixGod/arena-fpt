Lần chạy e10_watershed_s70 · engine=isaac · 2026-11-02T17:44:11+07:00 · hash arena 9139d67f · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C2 | 0 | 20 (20) | 15 | 75% [53%, 89%] | 75% | — | 2.50/5.04 | 0.6/41.2 |
| CL0 | dev_C3 | 0 | 20 (20) | 11 | 55% [34%, 74%] | 55% | — | 2.47/2.99 | 0.6/38.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C2 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 1 |
| CL0 | dev_C3 | 0 | 0 | 0 | 1 | 1 | 0 | 6 | 0 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 45 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
