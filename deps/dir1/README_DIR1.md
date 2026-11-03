# Bộ công cụ cho KE_HOACH_HUONG_1.md

Yêu cầu: Python 3.8+. `stats_tables.py` cần numpy và scipy; các script còn lại chỉ dùng thư viện chuẩn.

```bash
# 1) Tự kiểm bộ phân tích (so khớp scipy nếu có; 21 kiểm tra)
python3 g0_analyze.py selftest

# 2) Sinh sắp xếp vật có hạt giống cố định. Sửa LEVELS trong make_arrangements.py cho hợp kẹp của bạn TRƯỚC khi sinh bộ test.
#    G0 dùng các sắp xếp ĐẦU danh sách (seen_C0 1-20, novel_C0 1-20, novel_C2 1-30, novel_C3 1-20); G2 dùng cả danh sách (n = 60 ở novel_C2, 30 ở các ô còn lại).
W=200                                      # bề rộng băng (mm) = belt.width_mm trong cấu hình CL-0; ví dụ, thay bằng số đo của bạn
cp objects_template.csv objects.csv        # điền tên, đường kính (mm), split = train|dev|test
python3 make_arrangements.py --objects objects.csv --split train --clutter C0 --n 30 --belt-width $W --seed 12 --out arr_seen_C0.csv
python3 make_arrangements.py --objects objects.csv --split test  --clutter C0 --n 30 --belt-width $W --seed 13 --out arr_novel_C0.csv
python3 make_arrangements.py --objects objects.csv --split test  --clutter C2 --n 60 --belt-width $W --seed 11 --out arr_novel_C2.csv
python3 make_arrangements.py --objects objects.csv --split test  --clutter C3 --n 30 --belt-width $W --seed 14 --out arr_novel_C3.csv

# 3) Sau khi chạy lượt thử: điền CSV theo g0_template.csv rồi
python3 g0_analyze.py cells trials.csv                       # bảng Wilson theo (phương pháp, ô)
python3 g0_analyze.py g0    trials.csv --method CL0          # quy tắc G0 (ô kiểm hệ thống seen_C0, ô quyết định novel_C2)
python3 g0_analyze.py g2    trials.csv --base CL0 --chal ACT --cell novel_C2   # ghép cặp theo arrangement_id

# 4) Đổi giả định (số phút/lượt, rho, ngưỡng...) rồi tính lại bảng và file kế hoạch
python3 stats_tables.py && python3 build_plan1.py            # ra ../KE_HOACH_HUONG_1.md
```

Đóng băng tiêu chí trước lượt thử đầu tiên:

```bash
# chạy từ thư mục chứa cả KE_HOACH_HUONG_1.md và dir1/ (khi giải nén gói: thư mục cha của dir1/)
sha256sum KE_HOACH_HUONG_1.md dir1/g0_analyze.py > dir1/FROZEN.txt
```

Ngưỡng nằm ở đầu `g0_analyze.py` (GO_MAX, PIVOT_MIN, SANITY_MIN, ATTRIB_MIN, G2_MIN_DIFF, G2_MIN_ABS, G2_MIN_PAIRS) và khối PARAMS của `stats_tables.py`;
`build_plan1.py` dừng với lỗi nếu hai nơi lệch nhau.

`success`: 1/0. `valid`: 1/0 — 0 chỉ dành cho lỗi phần cứng / ngắt khẩn cấp / mất giao tiếp; lượt đó bị loại và PHẢI chạy lại.

CL-0 (baseline mô-đun + bộ thực thi hệ băng, 26/10/2026) nằm ở thư mục `../cl0/` khi giải nén `dir1_tools.tar.gz`; hướng dẫn cài đặt, hiệu chuẩn và chạy G0 ở `../cl0/README_CL0.md`. `python -m cl0.run_g0` ghi `g0_trials.csv` đúng định dạng của `g0_analyze.py`.
