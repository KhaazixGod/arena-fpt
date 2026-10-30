# CLAUDE.md — arena (Isaac Sim, so sánh các phương pháp gắp vật trên băng chuyền)

Chép từ `../KE_HOACH_DAU_TRUONG.md` mục 3 (nguồn sự thật: mục 3 của file đó; có hiệu lực cùng `../cl0/CLAUDE.md`).
Đường dẫn thực tế trên máy này: `~/Projects/dir1_tools/{arena,cl0,dir1}` (prompt gốc ghi `~/thesis/...`, thư mục đó không tồn tại; 29/10/2026).
Đọc trước khi làm: `../cl0/CLAUDE.md`, `../cl0/README_CL0.md`, `../KE_HOACH_HUONG_1.md` §3.4–3.5, §4.2–4.3, `../KE_HOACH_DAU_TRUONG.md` (toàn bộ).
Phiên mới: đọc `ARENA_SETUP_REPORT.md`, `ARENA_TUNING_LOG.md`, `CODE_CHANGES.md` (nếu có) trước.

## 3. Luật cho Claude Code (chép vào `arena/CLAUDE.md`; có hiệu lực cùng `cl0/CLAUDE.md`)

1. **An toàn.** Kế hoạch này chỉ chạy mô phỏng. Không mở `LeRobotArm`, `Belt` thật hay camera thật. Isaac chạy không giao diện (headless) trừ khi bạn nhờ xem. Không `sudo`; việc cần quyền thì đưa lệnh cho bạn. Không chạy Isaac song song với huấn luyện (tranh VRAM 8 GB).
2. **Vị trí mã.** Mã đấu trường nằm ở `arena/`, **ngoài** `cl0/`. Lý do: `cl0.system.code_sha256()` băm mọi `*.py` trong `cl0/` trừ `sim/` và `tests/` `[đã kiểm]`; thêm hay sửa file trong `cl0/` làm vỡ dấu đóng băng. Cần sửa `cl0/*.py` (ví dụ chỗ nào gọi `time` thay vì đồng hồ chèn vào): **dừng và hỏi bạn**, ghi `CODE_CHANGES.md`, chạy lại `pytest -m "not slow"` (204) và `run_g0 --sim`, và việc đó phải xong **trước** khi bạn đóng băng CL-0.
3. **Cấu hình riêng.** `arena/configs/arena.toml` (bản sao từ `cl0.toml`, chú thích lý do mỗi khác biệt). Không sửa `cl0.toml` của máy thật.
4. **Tinh chỉnh CL-0 trong sim** `[đề xuất]`: chỉ trên vật DEV và sắp xếp DEV của sim, tối đa 16 giờ làm việc (bạn báo giờ), mỗi lần một thông số, ghi `ARENA_TUNING_LOG.md` (ngày, thông số, cũ → mới, lý do, bằng chứng, giờ đã dùng). Đổi logic nhận thức/chọn vật/điều khiển của CL-0 là đổi thuật toán: **hỏi bạn trước**. Tham số tinh chỉnh trong sim **không** mang sang robot thật.
5. **Ô TEST của sim:** sinh sẵn, để trong `arena/locked/`, **không chạy** khi bạn chưa ra lệnh.
6. **Trung thực.** Không nói "chạy được / xong" khi chưa có log, ảnh hay con số kèm đường dẫn. Điều chưa kiểm ghi `[chưa kiểm]`. Không sửa tay CSV/JSON kết quả, không xoá lượt hay log. Mọi số sim ghi `engine=isaac`; không trộn với số thật.
7. **Lượt không hợp lệ** (`valid=0`) **chỉ** vì lỗi mô phỏng (Isaac sập, NaN vật lý, vật xuyên băng, mất đồng bộ lockstep). Thất bại của phương pháp luôn được tính. Tỉ lệ `valid=0` > 10% thì dừng và sửa.
8. **Dừng và hỏi bạn khi:** FK của USD lệch ngưỡng; cần tải dữ liệu lớn hoặc giấy phép chưa rõ (mesh vật); phải đổi thuật toán baseline; VRAM không đủ; số ngoài ngưỡng ở §7.
9. **Báo cáo bằng tiếng Việt, ngắn:** kết luận trước, rồi bảng metrics (§6.3) kèm đường dẫn bằng chứng, rồi việc bạn cần làm.

