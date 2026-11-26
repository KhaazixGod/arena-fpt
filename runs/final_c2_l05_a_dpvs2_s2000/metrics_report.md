Lần chạy final_c2_l05_a_dpvs2_s2000 · engine=isaac · 2026-11-25T11:31:27+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DPVS2_S2000_l05a | test_C2 | 0.5 | 60 (60) | 38 | 63% [51%, 74%] | 62% | — | —/— | 7.2/58.0 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DPVS2_S2000_l05a | test_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 10 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 181 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
