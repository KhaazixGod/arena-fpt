Lần chạy e14_act_j0_dev2 · engine=isaac · 2026-11-05T23:47:45+07:00 · hash arena 7ca6903e · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_J0 | dev_C2 | 0.5 | 20 (20) | 4 | 20% [8%, 42%] | 5% | — | —/— | 4.8/15.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_J0 | dev_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 112 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/20
