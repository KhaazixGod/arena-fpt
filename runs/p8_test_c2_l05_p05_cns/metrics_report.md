Lần chạy p8_test_c2_l05_p05_cns · engine=isaac · 2026-11-20T15:11:47+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P05_CNS | test_C2 | 0.5 | 60 (60) | 10 | 17% [9%, 28%] | 15% | — | 2.40/3.47 | 1.6/645.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P05_CNS | test_C2 | 0.5 | 0 | 0 | 16 | 17 | 0 | 7 | 8 | 2 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 69 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
