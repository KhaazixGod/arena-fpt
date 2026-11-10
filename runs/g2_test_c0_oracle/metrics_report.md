Lần chạy g2_test_c0_oracle · engine=isaac · 2026-11-10T17:12:29+07:00 · hash arena 7e7517d9 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E5 generated set configs/objects_sim.json sha256 aa49c57deff0

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| ORACLE | test_C0 | 0.5 | 30 (30) | 18 | 60% [42%, 75%] | 60% | — | 2.38/2.40 | 0.6/32.6 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| ORACLE | test_C0 | 0.5 | 0 | 0 | 3 | 0 | 2 | 2 | 0 | 5 |

Chặn dưới/trên: ORACLE test_C0 L0.5 = 60% (n=30)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 28 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/30

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a ORACLE test_C0 L0.5: 18/30 = 60% (cần ≥ 95%) -> CHƯA ĐẠT
