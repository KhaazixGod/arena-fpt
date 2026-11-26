Lần chạy kin_dev_dev_c2_l05 · engine=isaac · 2026-11-25T01:25:19+07:00 · hash arena cd5aa2b0 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| m4v2.kin_cv_ik:make_method | dev_C2 | 0.5 | 10 (10) | 4 | 40% [17%, 69%] | 30% | — | 2.38/2.42 | 0.7/54.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| m4v2.kin_cv_ik:make_method | dev_C2 | 0.5 | 0 | 0 | 0 | 2 | 0 | 3 | 1 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 71 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/10
