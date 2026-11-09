Lần chạy g0_test_c2 · engine=isaac · 2026-11-08T22:12:08+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | test_C2 | 0.5 | 30 (30) | 10 | 33% [19%, 51%] | 33% | — | 2.38/3.12 | 0.6/35.3 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | test_C2 | 0.5 | 0 | 0 | 2 | 0 | 0 | 9 | 8 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 42 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/30
