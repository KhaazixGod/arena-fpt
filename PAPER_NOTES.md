# PAPER_NOTES (nhánh paper-dev; không thuộc bản đồ án đóng băng `thesis-freeze-2026-11-14`)

## P1. Chẩn đoán trần ORACLE (14/11/2026, sheet không khóa `arrangements/sim/train_C2.csv`, ORACLE, n = 60)
ORACLE = bộ thực thi CL-0 + nhận thức hoàn hảo. Ghép cặp trên cùng 60 cảnh, mỗi lần đổi một thứ (`scripts/p1_oracle_diag.sh`, `p1_slip_mech.sh`, `p1_slip_mech2.sh`; cấu hình sao chép `configs/arena_p1_*.toml`, không sửa file gốc).

| Biến thể (L0.5 nếu không ghi) | Thành công | Lỗi chính | Ghép cặp vs gốc (mất/được), McNemar chính xác |
|---|---|---|---|
| Gốc (`runs/p1_oracle_train_c2_l05`) | 41/60 | `dropped_in_hold` 11, `ik_fail` 3, `late` 2 | |
| A ma sát đệm 1,5 → 3,0 | 39/60 | `dropped_in_hold` 10 | 4/2, p = 0,69 |
| B kẹp cao 10 → 16 mm | 41/60 | `dropped_in_hold` 12 | 3/3, p = 1,0 |
| C nhấc chậm `vmax_z` 150 → 60 | 40/60 | `dropped_in_hold` 9, `ik_fail` 6 | 3/2, p = 1,0 |
| E ma sát xoắn đệm 5 → 12 mm | 41/60 | `dropped_in_hold` 10 | 2/2, p = 1,0 |
| **D băng đứng yên (L0)** | **50/60** | `dropped_in_hold` 4, `picked_hold_complete` 5 | 4/13, p = 0,049 |

Kết luận (thăm dò, hậu nghiệm, một lần chạy mỗi biến thể): thông số vật lý của kẹp (ma sát, ma sát xoắn, độ cao kẹp, tốc độ nhấc) **không** cải thiện trần; chuyển động của băng làm trần giảm (83% → 68%). Cơ chế cụ thể **chưa xác định**: sai số bám tại thời điểm kẹp có trung vị như nhau giữa lượt đạt và lượt hỏng (0,1 mm), chỉ vài lượt hỏng có sai số lớn. Vật nghiêng 18–25° ngay khi nhấc ở cả lượt đạt lẫn lượt hỏng (`runs/p1_oracle_train_c2_l05/trial_*_gt.npz`).
Chưa kiểm: đáp ứng theo tốc độ (L0.25), vận tốc tương đối của đệm kẹp và vật lúc đóng kẹp, ảnh hưởng của gia tốc băng.
