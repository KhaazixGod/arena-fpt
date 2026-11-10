Lần chạy g2_test_c0_i2s1000 · engine=isaac · 2026-11-10T17:11:47+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2_S1000 | test_C0 | 0.5 | 30 (30) | 9 | 30% [17%, 48%] | 30% | — | —/— | 64.3/86.0 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:ACT_I2_S1000 | test_C0 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 1 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 148 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/30
