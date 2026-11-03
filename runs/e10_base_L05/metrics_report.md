Lần chạy e10_base_L05 · engine=isaac · 2026-11-02T18:15:09+07:00 · hash arena 9139d67f · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C2 | 0.5 | 20 (20) | 6 | 30% [15%, 52%] | 25% | — | 2.36/2.44 | 0.6/46.6 |
| ORACLE | dev_C2 | 0.5 | 20 (20) | 16 | 80% [58%, 92%] | 70% | +50% (p=0.002; [30, 70]%, N=20) | 2.38/2.43 | 0.6/15.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C2 | 0.5 | 0 | 0 | 0 | 2 | 0 | 4 | 8 | 0 |
| ORACLE | dev_C2 | 0.5 | 0 | 0 | 0 | 2 | 0 | 0 | 2 | 0 |

Chặn dưới/trên: ORACLE dev_C2 L0.5 = 80% (n=20)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 34 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
