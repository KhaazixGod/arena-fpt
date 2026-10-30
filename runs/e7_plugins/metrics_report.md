Lần chạy e7_plugins · engine=isaac · 2026-10-30T16:12:00+07:00 · hash arena 9a598a9d · Isaac 6.0.0.1 · cl0 006af1c9 · vật: INTERIM primitives (arena/arena/objects.py), not the E5 object set

| Phương pháp | Ô | L | n hợp lệ | Thành công | SR [Wilson 95%] | SR sạch | Δ so CL0 (p; bootstrap 95%) | t phát hiện→nhấc p50/p95 (s) | ms/bước p50/p95 |
|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 3 | 2 | 67% [21%, 94%] | 67% | — | 2.44/2.48 | 0.6/31.5 |
| CL0 | dev_C0 | 0.25 | 3 | 0 | 0% [0%, 56%] | 0% | — | 2.26/2.33 | 0.6/29.5 |
| REMOTE:CL0 | dev_C0 | 0 | 3 | 2 | 67% [21%, 94%] | 67% | +0% (p=1.000; [0, 0]%, N=3) | 2.44/2.48 | 2.0/30.4 |
| REMOTE:CL0 | dev_C0 | 0.25 | 3 | 0 | 0% [0%, 56%] | 0% | +0% (p=1.000; [0, 0]%, N=3) | 2.26/2.33 | 2.0/28.4 |
| arena.methods.examples.blob:make_method | dev_C0 | 0 | 3 | 3 | 100% [44%, 100%] | 100% | +33% (p=1.000; [0, 100]%, N=3) | 2.48/2.53 | 0.6/16.6 |
| arena.methods.examples.blob:make_method | dev_C0 | 0.25 | 3 | 1 | 33% [6%, 79%] | 33% | +33% (p=1.000; [0, 100]%, N=3) | 2.32/2.34 | 0.6/15.8 |

Nguyên nhân thất bại (đếm, gán tự động theo `LABEL_RULES.md`):
| Phương pháp | Ô | L | merge | seg_miss | grasp_point | timing | calib | slip | collision | other |
|---|---|---|---|---|---|---|---|---|---|---|
| CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| CL0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 1 | 2 | 0 | 0 |
| REMOTE:CL0 | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| REMOTE:CL0 | dev_C0 | 0.25 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 |
| arena.methods.examples.blob:make_method | dev_C0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| arena.methods.examples.blob:make_method | dev_C0 | 0.25 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |

Chặn dưới/trên: chưa chạy NOOP/ORACLE
Độ lặp lại: chưa đo (dùng --repeat)
Tốc độ: 41 giây thật/lượt (trung bình các nhóm) · lượt không hợp lệ: 0/18

Cổng sim (§7, ngưỡng [đề xuất]):
- S0b CL0 dev_C0 L0: 2/3 = 67% (cần ≥ 80%) -> CHƯA ĐẠT
- S0b CL0 dev_C0 L0.25: 0/3 = 0% (cần ≥ 80%) -> CHƯA ĐẠT
