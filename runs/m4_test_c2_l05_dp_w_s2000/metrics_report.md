Lần chạy m4_test_c2_l05_dp_w_s2000 · engine=isaac · 2026-11-22T06:06:19+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DP_W_S2000 | test_C2 | 0.5 | 60 (60) | 28 | 47% [35%, 59%] | 42% | — | —/— | 5.6/7.9 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DP_W_S2000 | test_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 13 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 115 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
