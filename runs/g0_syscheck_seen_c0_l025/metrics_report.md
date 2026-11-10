Lần chạy g0_syscheck_seen_c0_l025 · engine=isaac · 2026-11-09T18:04:16+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | seen_C0 | 0.25 | 20 (20) | 14 | 70% [48%, 85%] | 70% | — | 2.40/6.02 | 0.6/31.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | seen_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 47 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/20
