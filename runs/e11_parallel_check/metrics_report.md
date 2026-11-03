Lần chạy e11_parallel_check · engine=isaac · 2026-11-02T21:42:00+07:00 · hash arena 6d652a13 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C1 | 0.25 | 10 (10) | 10 | 100% [72%, 100%] | 100% | — | 2.32/2.41 | 0.6/3.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C1 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: ORACLE dev_C1 L0.25 = 100% (n=10)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 32 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/10
