Lần chạy p2_cl0w_dev_c2_l05 · engine=isaac · 2026-11-15T17:43:12+07:00 · hash arena 3f1ffbad · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0_W | dev_C2 | 0.5 | 60 (60) | 52 | 87% [76%, 93%] | 87% | — | 2.36/2.42 | 0.7/36.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0_W | dev_C2 | 0.5 | 0 | 0 | 0 | 3 | 0 | 3 | 2 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 61 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
