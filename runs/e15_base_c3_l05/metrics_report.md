Lần chạy e15_base_c3_l05 · engine=isaac · 2026-11-06T19:23:58+07:00 · hash arena 519767a2 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C3 | 0.5 | 20 (20) | 8 | 40% [22%, 61%] | 40% | — | 2.41/2.47 | 0.7/42.4 |
| ORACLE | dev_C3 | 0.5 | 20 (20) | 13 | 65% [43%, 82%] | 45% | +25% (p=0.302; [-15, 60]%, N=20) | 2.36/4.52 | 0.7/24.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C3 | 0.5 | 0 | 0 | 3 | 0 | 0 | 1 | 7 | 1 |
| ORACLE | dev_C3 | 0.5 | 0 | 0 | 0 | 1 | 0 | 1 | 5 | 0 |

Chặn dưới/trên: ORACLE dev_C3 L0.5 = 65% (n=20)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 51 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/40
