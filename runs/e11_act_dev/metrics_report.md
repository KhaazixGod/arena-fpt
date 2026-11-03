Lần chạy e11_act_dev · engine=isaac · 2026-11-02T21:40:59+07:00 · hash arena 6d652a13 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_J0 | dev_C0 | 0 | 20 (20) | 15 | 75% [53%, 89%] | 75% | — | —/— | 5.4/15.6 |
| REMOTE:ACT_J0 | dev_C0 | 0.25 | 20 (20) | 19 | 95% [76%, 99%] | 95% | — | —/— | 5.4/16.1 |
| REMOTE:ACT_J0 | dev_C1 | 0 | 20 (20) | 14 | 70% [48%, 85%] | 70% | — | —/— | 5.4/16.2 |
| REMOTE:ACT_J0 | dev_C1 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 70% | — | —/— | 5.4/15.7 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_J0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 2 |
| REMOTE:ACT_J0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| REMOTE:ACT_J0 | dev_C1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| REMOTE:ACT_J0 | dev_C1 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 142 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/80
