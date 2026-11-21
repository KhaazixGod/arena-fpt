Lần chạy p8_test_c2_l05_p05_cns_w · engine=isaac · 2026-11-20T12:41:40+07:00 · hash arena 4a8f7dd4 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| P05_CNS_W | test_C2 | 0.5 | 60 (60) | 15 | 25% [16%, 37%] | 25% | — | 2.40/4.38 | 0.7/507.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| P05_CNS_W | test_C2 | 0.5 | 0 | 0 | 17 | 14 | 0 | 11 | 3 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 70 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
