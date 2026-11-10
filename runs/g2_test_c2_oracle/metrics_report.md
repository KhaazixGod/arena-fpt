Lần chạy g2_test_c2_oracle · engine=isaac · 2026-11-10T16:43:53+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | test_C2 | 0.5 | 60 (60) | 28 | 47% [35%, 59%] | 42% | — | 2.38/2.42 | 0.6/28.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | test_C2 | 0.5 | 0 | 0 | 5 | 6 | 0 | 13 | 6 | 2 |

Chặn dưới/trên: ORACLE test_C2 L0.5 = 47% (n=60)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 28 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
