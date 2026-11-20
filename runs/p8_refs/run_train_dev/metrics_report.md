Lần chạy run_train_dev · engine=isaac · 2026-11-20T04:25:36+07:00 · hash arena 1bc3a6fd · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REFCAP | refs_dev | 0 | 6 (6) | 0 | 0% [0%, 39%] | 0% | — | —/— | 0.0/0.0 |
| REFCAP | refs_train | 0 | 20 (20) | 0 | 0% [0%, 16%] | 0% | — | —/— | 0.0/0.0 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REFCAP | refs_dev | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| REFCAP | refs_train | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 4 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/26
