Lần chạy g0inv_oracle_seen_c0_l025 · engine=isaac · 2026-11-09T20:36:09+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | seen_C0 | 0.25 | 20 (20) | 18 | 90% [70%, 97%] | 90% | — | 2.40/2.42 | 0.6/3.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | seen_C0 | 0.25 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |

Chặn dưới/trên: ORACLE seen_C0 L0.25 = 90% (n=20)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 27 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/20

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a ORACLE seen_C0 L0.25: 18/20 = 90% (cần ≥ 95%) -> CHƯA ĐẠT
