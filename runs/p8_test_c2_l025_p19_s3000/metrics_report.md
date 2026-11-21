Lần chạy p8_test_c2_l025_p19_s3000 · engine=isaac · 2026-11-21T08:48:32+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| REMOTE:P19_ACT_TE_S3000 | test_C2 | 0.25 | 60 (60) | 16 | 27% [17%, 39%] | 27% | — | —/— | 14.5/26.6 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| REMOTE:P19_ACT_TE_S3000 | test_C2 | 0.25 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 8 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 157 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/60
