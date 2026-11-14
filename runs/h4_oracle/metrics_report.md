Lần chạy h4_oracle · engine=isaac · 2026-11-09T16:10:54+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C0 | 1 | 30 (30) | 0 | 0% [0%, 11%] | 0% | — | —/— | 0.7/24.1 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | dev_C0 | 1 | 0 | 0 | 0 | 20 | 7 | 0 | 0 | 3 |

Chặn dưới/trên: ORACLE dev_C0 L1 = 0% (n=30)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 13 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/30

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a ORACLE dev_C0 L1: 0/30 = 0% (cần ≥ 95%) -> CHƯA ĐẠT
