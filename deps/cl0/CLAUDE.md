# CLAUDE.md — CL-0 (baseline mô-đun gắp vật trên băng chuyền, SO-101)

Đồ án của người dùng: so một chính sách học từ ảnh với một baseline mô-đun mạnh (CL-0) trên vật lạ + xếp lộn xộn, nhắm một tạp chí Q3.
CL-0 là **đối chứng của bài báo**: nó phải mạnh, công bằng, và mọi con số về nó phải trung thực. Mã được viết và test bằng mô phỏng/thiết bị giả;
**chưa từng chạm phần cứng thật** (tay SO-101, băng chuyền bước, camera USB). Khi README và thực tế mâu thuẫn, tin thực tế, ghi lại, báo người dùng.

Đọc trước: `README_CL0.md` (lệnh, cờ, ngưỡng: nguồn sự thật) và `../KE_HOACH_HUONG_1.md` mục 3.4 (quy tắc công bằng), 4.3 (lượt hợp lệ), 5 (cổng G0).
Phiên mới: đọc `SETUP_REPORT.md`, `CALIB_LOG.md`, `TUNING_LOG.md`, `CODE_CHANGES.md` (nếu có) trước khi làm gì khác.

## 1. An toàn (phần cứng thật)

1. Claude Code **không tự chạy** lệnh làm tay hoặc băng chuyển động, hoặc tắt torque: `calibrate fk|board|belt|lag`, `run_g0` không có `--sim`,
   `tune watch --belt-speed`, mọi script tự viết có mở `LeRobotArm` hoặc `Belt`. Đưa lệnh nguyên văn cho người dùng chạy trong terminal của họ
   (`source scripts/env.sh`, rồi `cl0log <tên> <lệnh>`), kèm checklist: (a) vùng robot trống; (b) tay họ ở công tắc nguồn;
   (c) tay robot được đỡ nếu torque tắt; (d) lần đầu đặt `robot.q_dot_max_deg_s` ≤ 60.
   Các lệnh `calibrate intrinsics|board|belt|background|lag` và `run_g0` còn hỏi Enter nên Bash tool cũng không chạy được (`calibrate fk` thì chạy liên tục tới khi Ctrl-C).
2. Claude Code **được tự chạy**: pytest, `run_g0 --sim`, đọc thông tin hệ thống/thiết bị, chụp một khung camera, `tune reach`,
   `tune watch` (không `--belt-speed`), phân tích log/ảnh/video, sửa `cl0.toml`.
3. Không dùng `sudo`; không sửa udev, ROS, Python hệ thống. Cần thì đưa lệnh cho người dùng chạy.
4. **Không để LeRobot hiệu chuẩn lại**: không bao giờ gõ `c`. Nếu LeRobot hỏi "Press ENTER to use provided calibration file…", dừng và kiểm cổng đó đúng
   là **follower** (không phải leader) trước khi bảo người dùng nhấn Enter; Enter trên nhầm cổng ghi đè hiệu chuẩn của tay kia. Không đụng tay leader.
5. Chuyển động lạ, va chạm, tiếng gằn: người dùng cắt nguồn. Không chạy lại gì cho tới khi đã đọc log, nêu nguyên nhân khả dĩ nhất và một phép thử an toàn hơn.
6. Băng, camera và đế tay phải ở **vị trí cuối** trước `calibrate board`; dời bất kỳ thứ gì sau đó thì làm lại từ `board` (README mục 0 và 6).

## 2. Công bằng và trung thực

1. Tinh chỉnh CL-0 **chỉ** trên vật DEV (4) và sắp xếp DEV, **tối đa 16 giờ làm việc** (người dùng báo giờ; ghi vào `TUNING_LOG.md`).
   Không chạy robot với vật TEST và không chỉnh thông số theo chúng.
2. Mỗi lần chỉ đổi **một** thông số, ghi `TUNING_LOG.md`: ngày, thông số, giá trị cũ → mới, lý do, bằng chứng (đường dẫn log/ảnh/số), số giờ đã dùng.
3. Không chạy G0 (các ô `seen_C0`, `novel_*`) và không chạy `python -m cl0.freeze` khi người dùng chưa nói rõ. Sau đóng băng không sửa `cl0/*.py` hay cấu hình;
   bắt buộc thì theo `--force` ở README mục 8 và báo người dùng (phải công bố).
4. `perception.grasp.yaw_mode="local"` và `perception.split="watershed"` không thuộc CL-0 gốc: mặc định TẮT; bật chỉ khi người dùng đồng ý và phải ghi vào `--notes` khi đóng băng.
5. Số liệu là bằng chứng: không sửa tay CSV/JSON kết quả, không xoá lượt hay log. Lượt "không hợp lệ" **chỉ** vì lỗi phần cứng, ngắt khẩn cấp, mất giao tiếp
   camera/servo/băng (kế hoạch 4.3); mọi thứ khác là thành công hoặc thất bại của CL-0. Tỉ lệ không hợp lệ > 10% thì dừng và sửa.
6. Bất kỳ cảnh báo `CẢNH BÁO` nào của lệnh, hoặc số ngoài ngưỡng trong README (sai số chạm > 3 mm, tỉ lệ ô lệch > 1,5%, …): dừng và sửa tại đó.
   Không nới ngưỡng, không bỏ lần đo xấu để cho qua.
7. Sửa mã gói: được khi là lỗi rõ của lớp phần cứng (tên khoá LeRobot, chuỗi serial, V4L2), kèm test hoặc lý do ngắn và một dòng trong `CODE_CHANGES.md`;
   sau mỗi sửa chạy lại bộ test nhanh (204) và `--sim`. Đổi logic nhận thức / chọn vật / điều khiển thì **hỏi người dùng trước**: đó là thay đổi thuật toán của baseline và tính vào 16 giờ.
8. Không nói "chạy được / xong" khi chưa có bằng chứng (đường dẫn log, ảnh, con số). Điều chưa kiểm ghi `[chưa kiểm]`. Không rõ thì hỏi, đừng đoán.

## 3. Cách làm việc

* Mỗi terminal của người dùng: `source scripts/env.sh` (venv, `unset PYTHONPATH`, hàm `cl0log`). Log lưu ở `logs/`. Sau khi người dùng báo xong một lệnh, đọc log tương ứng.
  Mỗi lệnh Bash của Claude Code là một shell mới nên viết `source scripts/env.sh && <lệnh>` (hoặc gọi thẳng `~/venvs/cl0/bin/python`).
* Nhật ký (đặt trong thư mục dự án): `SETUP_REPORT.md` (môi trường, thiết bị, kết quả kiểm), `CALIB_LOG.md` (mỗi lần hiệu chuẩn: giờ, lệnh, số chính, quyết định),
  `TUNING_LOG.md`, `CODE_CHANGES.md`.
* Cấu hình chỉ sửa trong `cl0.toml` (kèm chú thích lý do). Không sửa `configs/config_template.toml` (sinh tự động, có test khớp mã).
* Ảnh kết quả (`background_preview.png`, `reach.png`, `tune_out/*.png`, khung video) thì mở ra xem, đừng chỉ tin con số.
* Trả lời người dùng bằng tiếng Việt, ngắn: kết luận trước, rồi con số kèm đường dẫn bằng chứng, rồi việc người dùng cần làm tiếp.

## 4. Dừng và hỏi người dùng khi

* LeRobot hỏi về hiệu chuẩn, hoặc thiếu file hiệu chuẩn của `robot_id`.
* Băng chuyền không giao tiếp bằng "đếm xung qua serial" (GRBL, GPIO, …): trình bày 2–3 lựa chọn, đừng tự viết hay nạp firmware.
* Bất kỳ bước nào cần `sudo`.
* Số ngoài ngưỡng, phần cứng phản ứng lạ, hoặc phải đổi thuật toán.
