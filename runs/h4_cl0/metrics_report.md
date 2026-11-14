Lần chạy h4_cl0 · engine=isaac · 2026-11-09T17:15:21+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 1 | 30 (30) | 0 | 0% [0%, 11%] | 0% | — | —/— | 0.6/44.4 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 1 | 0 | 0 | 0 | 7 | 13 | 0 | 0 | 10 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 25 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/30

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L1: 0/30 = 0% (cần ≥ 80%) -> CHƯA ĐẠT
