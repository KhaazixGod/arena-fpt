Lần chạy e18_test_seen_ref · engine=isaac · 2026-11-12T16:38:34+07:00 · hash arena 8fcb74d6 · Isaac 6.0.0.1 · cl0 006af1c9 · vật: E18 task catalog configs/objects_tasks.json sha256 34ba91c64208

| Phương pháp | Ô | L | n sắp xếp (lượt) | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| NOOP | test_Tseen | 0 | 160 (160) | 0 | 0% [0%, 2%] | 0% | — | —/— | 0.0/0.0 |
| TASK_EXPERT | test_Tseen | 0 | 160 (160) | 144 | 90% [84%, 94%] | 88% | — | —/— | 0.6/2.2 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| NOOP | test_Tseen | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| TASK_EXPERT | test_Tseen | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Chặn dưới/trên: NOOP test_Tseen L0 = 0% (n=160)
Độ lặp lại: chưa đo (dùng --repeat hoặc --reps ≥ 2)
Tốc độ: 32 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/320

Cổng sim (§7, ngưỡng [đề xuất]):
- S0a NOOP test_Tseen L0: 0/160 = 0% (cần ≈ 0%) -> ĐẠT
