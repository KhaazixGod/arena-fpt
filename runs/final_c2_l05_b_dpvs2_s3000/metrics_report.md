Lần chạy final_c2_l05_b_dpvs2_s3000 · engine=isaac · 2026-11-25T17:26:53+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DPVS2_S3000_l05b | test_C2 | 0.5 | 60 (60) | 35 | 58% [46%, 70%] | 57% | — | —/— | 7.0/61.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:DPVS2_S3000_l05b | test_C2 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 3 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 177 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
