# ARENA_SETUP_REPORT — môi trường Isaac Sim cho đấu trường

## 29/10/2026 — E0: môi trường và khả thi

Chỉ mô phỏng, không headless-GUI, không chạm robot/băng/camera thật. Lệnh: `env -u PYTHONPATH -u VIRTUAL_ENV ~/env_isaac/bin/python arena/scripts/e0_probe.py --out arena/runs/e0 --width W --height H`.

### Khác với prompt/kế hoạch (ghi lại, không tự sửa)
| Điều | Thực tế | Xử lý |
|---|---|---|
| Đường dẫn `~/thesis/{arena,cl0,...}` | không tồn tại; mọi thứ ở `~/Projects/dir1_tools/{arena,cl0,dir1}` | `arena/` tạo cạnh `cl0/`; đã ghi vào `arena/CLAUDE.md` |
| Kế hoạch đấu trường dẫn "`KE_HOACH_HUONG_1.md` §3.6" và bảng "Khớp sim–thật" | file hiện có chỉ có mục 3.1–3.5 (`grep -n "3\.6"` không ra gì) | **hỏi người dùng**: §3.6 chưa được thêm vào kế hoạch chính? Mình chưa đọc được nội dung đó (S0, S1, S2, bảng khớp sim–thật) |

### Máy và Isaac Sim
| Mục | Giá trị | Nguồn |
|---|---|---|
| Isaac Sim | 6.0.0.1 (pip), `~/env_isaac/bin/python`, Python 3.12.3 | `pip list`, `e0_probe.json` |
| Isaac Lab | không thấy (`~/IsaacLab*`, `pip list` không có) `[chưa kiểm sâu]` | |
| GPU | RTX 3070 Ti 8192 MiB, driver 595.99.02; nền (màn hình/desktop) đang dùng ≈ 850–950 MiB, không có tiến trình tính toán nào khác | `nvidia-smi` |
| numpy trong Isaac | 2.3.1 (LeRobot 0.6.1 đòi 2.0–2.2; chỉ ảnh hưởng nếu import `lerobot`, đường mô phỏng của CL-0 không import) | |
| Khởi động `SimulationApp` headless | ≈ 17,5 s (cache shader nóng) | `app_start_s` |
| Extension có sẵn khi khởi động | `omni.replicator.core`, `isaacsim.sensors.camera`, `omni.physx`, `isaacsim.core.api`: bật. `isaacsim.asset.gen.conveyor`, `isaacsim.ros2.bridge`: **tắt**, phải bật bằng `set_extension_enabled_immediate` | `e0_probe.json` |
| Bật conveyor lúc chạy | chạy được, khung hình bình thường (`runs/e0_conv/e0_probe.json`) | |
| Bật CẢ conveyor lẫn ros2.bridge lúc chạy | **segfault** một lần, ở `app.update()` đầu tiên sau `timeline.play()` (stack Python: `omni.kit.manipulator.prim.core ... xform_set_time`); `arena/logs/2026-10-29_015114_e0_probe_1080p_v2.log` (Isaac ghi stack Python vào `.py.txt` trong `~/env_isaac/.../isaacsim/kit/data/Kit/Isaac-Sim Python/6.0/`). Không lặp lại khi chỉ bật conveyor ⇒ arena **không bật ROS 2 bridge** (không cần) `[chưa lặp lại riêng ros2.bridge để chắc nguyên nhân]` | |

### Hai lỗi cảnh đã gặp (để E1 không dẫm lại)
1. Khung hình **đen/phẳng** ở các lần chạy đầu. Nguyên nhân tìm được (`scripts/e0_black_diag.py`, ảnh `runs/e0/diag_*.png`): (a) camera USD có mặt phẳng gần mặc định = 1 *đơn vị cảnh* = 1 m khi `metersPerUnit = 1`, nên mặt bàn cách 0,8 m bị cắt mất ⇒ đặt `clippingRange = (0,01; 20)`; (b) `DistantLight` đơn lẻ cho ảnh đen, `DomeLight` mới sáng `[chưa tìm ra vì sao; E1 sẽ chọn ánh sáng và đo độ phơi sáng]`.
2. Cảnh hiện tại chỉ là một khối lập phương trên nền, không phải cảnh thật.

### Đo (cảnh trống + 1 khối đỏ rơi lên nền, 1 camera, RGB annotator; `app.update` có timeline đang chạy)
| Độ phân giải | ms / khung (`orchestrator.step` + đọc ảnh) p50 / p95 | VRAM đỉnh | file |
|---|---|---|---|
| 640×480 | 67,2 / 72,2 | 2,49 GiB | `runs/e0/e0_probe_640x480.json` |
| 1280×720 | 72,1 / 85,1 | 2,76 GiB | `runs/e0/e0_probe_1280x720_v6.json` |
| 1920×1080 | 152,3 / 154,5 (lần chạy khác: 153,0 / 154,8) | 3,58 GiB | `runs/e0/e0_probe_1920x1080_v6.json` |

Một lần chạy 1080p trước khi sửa clipping cho 87 ms nhưng khung đen (không có gì để vẽ): **không dùng số đó**.
* Bước vật lý trực tiếp (`simulate()+fetch_results()`, 240 Hz, 1 vật): **0,62 ms/bước** (3 lần: 0,616 / 0,621 / 0,629). Chỉ là vật lý; cảnh có tay + băng + nhiều vật sẽ chậm hơn `[chưa đo, E1]`. `[chưa kiểm]` cách này có phải đường lockstep đúng khi timeline đang chạy hay không; E2 xác nhận.
* Khối lập phương nằm yên ở z = 0,02 m sau 30 lần cập nhật (đúng cạnh 4 cm / 2) ⇒ vật lý chạy theo timeline.
* Ước tính thô `[ước lượng]`: một lượt 20 s ở 30 fps camera = 600 khung ⇒ ≈ 40 s (480p/720p) tới ≈ 90 s (1080p) chỉ riêng render, trước khi cộng tay + vật lý.

### Quyết định tiến trình (đề xuất, chờ E2 xác nhận)
**Cùng một tiến trình, Python của Isaac.** Lý do: Isaac Python 3.12.3 = Python của venv CL-0; `import cl0.runner, cl0.system, cl0.kinematics, cl0.sim.platform, cl0.run_g0` chạy được trong `~/env_isaac` (numpy 2.3.1, opencv 4.13 có sẵn) mà không cần LeRobot (`PYTHONPATH=…/cl0 ~/env_isaac/bin/python -c …`, 29/10). Không cài thêm gì vào `~/env_isaac`.
`[chưa kiểm]` chạy `pytest` của CL-0 trong `~/env_isaac` (pytest chưa có ở đó; vẫn chạy bộ test bằng `~/venvs/cl0`); chạy một lượt CL-0 thật trong Isaac (E2).
Tách tiến trình (socket, lockstep) chỉ cần nếu sau này cần LeRobot trong cùng tiến trình với Isaac.

### Ảnh render
`runs/e0/e0_frame_1920x1080.png` (khối đỏ giữa khung trên nền xám; mở xem được), `runs/e0/e0_frame_640x480.png`.

### Điều E0 CHƯA trả lời
* Ánh sáng và phơi sáng thật cho cảnh băng (E1).
* Vật lý có tay + gắp (E1/E4).
* Băng: chưa dựng; `isaacsim.asset.gen.conveyor` bật được, chưa thử đo vận tốc vật.
