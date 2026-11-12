# PREREGISTRATION_E18: quy tắc ghi trước cho thử nghiệm 40 nhiệm vụ (phụ lục post-hoc)

**Trạng thái.** Người dùng chốt ngày 11/11/2026: 40 nhiệm vụ thao tác, một ACT đa nhiệm vụ (ACT_I2 + mã nhiệm vụ), làm ngay. File có hiệu lực khi được commit, và phải commit **trước khi huấn luyện** (các mục 1–5, 7) và **trước lượt TEST đầu tiên** (mục 6: băm checkpoint). Từ lúc commit không sửa nội dung; muốn đổi thì ghi vào mục 9 "Sai lệch".
Kết quả chính của luận văn vẫn là G2 (`PREREGISTRATION_G2.md`, NO-GO). E18 là **phụ lục post-hoc**, báo cáo dù kết quả thế nào. Kế hoạch: `KE_HOACH_TASKS.md`.
Chạy ô `test_T*` cần lệnh riêng của người dùng (`CONFIRM_TEST=yes`, `--allow-locked`, luật 5). File này không phải lệnh đó.

## 1. Nhiệm vụ (`arena/tasks.py`)

Băng đứng yên (L0). Kẹp thẳng đứng (tilt 90°). Mỗi cảnh có vật đích (đúng loại của nhiệm vụ) và 1 vật nhiễu khác loại.

| Họ | Nhiệm vụ | Thành công (`arena/task_labeler.py`, giữ liên tục) |
|---|---|---|
| `pick` | 6 loại vật | vật đích nhấc ≥ 25 mm, tâm kẹp cách vật ≤ w/2, giữ 2 s (M1) |
| `place` | 6 loại × vùng A/B | vật đích nằm đứng trên băng, tâm cách tâm vùng ≤ 25 mm, kẹp đã nhả; giữ 1 s |
| `pull` (15) | 6 loại × về robot; box, cyl, L, T, ring × xuôi băng; box, cyl, T, ring × ngược băng | dịch ≥ 35 mm theo hướng, lệch ngang ≤ 20 mm, chưa từng nhấc > 10 mm, đã nhả, còn đứng; giữ 1 s |
| `topple` (7) | {box, cyl} × {xuôi băng, ngược băng, về robot} + mug × về robot | trục vật nghiêng ≥ 60°, tâm dịch ≥ 10 mm theo hướng; giữ 1 s |

Mã nhiệm vụ 12 chiều (`observation.environment_state`): họ (one-hot 4) + loại (one-hot 6) + tham số 2 chiều trong hệ băng.

Tổng 6 + 12 + 15 + 7 = 40 (danh sách cuối sau cổng, mục 8).
**8 nhiệm vụ giữ lại (không có demo):** `pick:mug`, `place:L:A`, `place:cyl:B`, `pull:ring:robot`, `pull:T:down`, `pull:cyl:up`, `pull:ring:up`, `topple:box:-a`. Mỗi thành phần (họ, loại, tham số) của chúng đều có trong ít nhất một nhiệm vụ huấn luyện (`tasks.check_split`).

## 2. Vật và sheet

- Danh mục `configs/objects_tasks.json`: 36 vật E5 không đổi + 6 vật tháp (`twbox37..39`, `twcyl40..42`). Chỉ dùng vật split `train`. `topple` chỉ dùng vật cao/rộng ≥ 1,6 hoặc cốc.
- Sheet (sinh bằng `python -m arena.tasks sheets`, hạt giống cố định, trước mọi huấn luyện):
  - `arrangements/tasks/pilot_T.json` (hạt giống 181, 40 × 5): chỉ để kiểm và chỉnh chuyên gia.
  - `arrangements/tasks/train_T.json` (182, 32 × 25): demo.
  - `locked/tasks/test_Tseen.json` (183, 32 × 5) và `locked/tasks/test_Theld.json` (184, 8 × 10): TEST, không chạy trước lệnh.
- Băm sha256: điền ở mục 8 khi commit.

## 3. Chuyên gia `TASK_EXPERT` và cổng

Chuyên gia có đặc quyền (đọc GT như ORACLE), là trần và là nguồn demo. Nó chỉ được chỉnh trên `pilot_T` (lần chạy thử 11/11; chỉnh lật trên cảnh 01–02 của `pilot_T`, `runs/e18_tune_topple_*`). Cổng: chuyên gia ≥ 4/5 trên `pilot_T` cho mỗi nhiệm vụ (`scripts/e18_pilot.sh`). **Nhiệm vụ không qua cổng bị bỏ khỏi cả demo và TEST** (không thay thế), ghi ở mục 8; các ngưỡng mục 7 tính trên những nhiệm vụ còn lại.

## 4. Mô hình `ACT_I2T`

ACT LeRobot 0.6.1, giao diện I2 (`arena/i2.py`, hành động tương đối trong hệ băng, `train_act_i2.py`), thêm `observation.environment_state` = mã nhiệm vụ (`to_lerobot_i2.py --task-vec`). Dữ liệu: các lượt thành công của `TASK_EXPERT` trên `train_T` (chỉ nhiệm vụ huấn luyện). 100 000 bước, batch 8, hạt giống 1000, các tham số khác mặc định như ACT_I2. Suy luận: `ACT_REPLAN=0` (= n_action_steps 100), `ACT_COMMIT=0`, `ACT_T_S` = 20 s, mỗi lượt giới hạn 25 s ảo. Không chỉnh mô hình theo kết quả nào trên ô TEST.

## 5. TEST (`scripts/e18_test.sh`)

ACT_I2T, TASK_EXPERT (trần) và NOOP (sàn) trên cùng cảnh: `test_Theld` (nhiệm vụ giữ lại × 10) và `test_Tseen` (nhiệm vụ đã học × 5 cảnh mới). Chấm bằng `scripts/e18_summary.py test`.

## 6. Checkpoint (điền sau huấn luyện, commit trước TEST)

```
act_i2t_s1000: f49b73cd5239bd7d3912de844c968facfab640d5879168501ab20c572ab982c8
```

## 7. Quy tắc quyết định

- **H-skills** ("một ACT học được nhiều kỹ năng"): được ủng hộ khi và chỉ khi ACT_I2T đạt **≥ 50%** trên các nhiệm vụ đã học (gộp `test_Tseen`) **và ≥ 30% ở mỗi họ**.
- **H-compose** ("tổng quát tổ hợp"): được ủng hộ khi và chỉ khi ACT_I2T đạt **≥ 30%** trên nhiệm vụ giữ lại (gộp `test_Theld`) **và** kiểm nhị thức một phía so với tỉ lệ của NOOP trên cùng cảnh (sàn tối thiểu 1%) cho **p ≤ 0,05**.
- Mô tả (không quyết định): tỉ lệ theo họ và theo nhiệm vụ, khoảng tin cậy Wilson 95%, so với trần TASK_EXPERT, nguyên nhân hỏng.
- Ngưỡng là [đề xuất] của Claude, chốt trước huấn luyện. Một hạt giống: nhiễu giữa các lần chạy chưa đo cho E18 (E16: 3/20 lượt đổi kết quả trên một ô n = 20).
- `valid=0` chỉ vì lỗi mô phỏng (luật 7); chạy bù cùng cấu hình. Từ lượt TEST đầu tiên không sửa mô hình, chuyên gia, nhãn, sheet hay ngưỡng.

## 8. Điền khi commit

**Kết quả cổng và thay nhiệm vụ (11/11, trước mọi demo và huấn luyện).**
- Cổng lần 1 trên `pilot_T` (40 nhiệm vụ bản đầu, `logs/2026-11-11_*_e18_gate.txt`): 36 đạt, 4 không đạt: `pull:mug:down` 1/5, `topple:box:-b` 3/5, `topple:cyl:-b` 2/5, `topple:mug:+a` 2/5 (hai cái sau nằm trong 8 nhiệm vụ giữ lại bản đầu). Nguyên nhân: đẩy ra xa robot không làm vật đổ; cốc trượt trong kẹp.
- Thay bằng `pull:{box,cyl,L,T}:up` (cổng trên `pilot_T2`, hạt giống 185): box 4/5, cyl 5/5, T 5/5, **L 0/5** (chữ L xoay quanh điểm kẹp) → `pull:L:up` thay bằng `pull:ring:up` (`pilot_T3`, hạt giống 186): 5/5.
- Bộ 40 cuối: **40/40 nhiệm vụ đạt ≥ 4/5, chuyên gia 191/200 = 95,5% [92, 98]** (`logs/*_e18_gate_final.txt`; `runs/e18_pilot_a`, `_b`, `e18_pilot2`, `e18_pilot3`).
- Hệ quả: 8 nhiệm vụ giữ lại bản cuối có 2 nhiệm vụ kéo ngược băng thay cho 2 nhiệm vụ lật; họ `topple` chỉ còn 1 nhiệm vụ giữ lại. Thay đổi này làm trước khi có bất kỳ demo, huấn luyện hay lượt TEST nào.
- Chỉnh chuyên gia (chỉ trên cảnh `pilot_T`): kẹp ở nửa chiều cao vật, mang vật 70 mm/s, góc kẹp thay thế cho hộp vuông, lật bằng cú đẩy nhanh (250 mm/s) ngay dưới đỉnh vật (`runs/e18_tune_topple_*`: đẩy chậm làm vật trượt chứ không đổ).

**Băm sha256 (bản commit này):**
```
34ba91c64208557e9e6e1bf117945b94c5e2de0b59d172c28b346dc2c5b237ca  configs/objects_tasks.json
23dc252b1959bf3a491d149dfa6077a132141a52925936c35c5836bdcdb11014  arrangements/tasks/train_T.json
5e2bf6eaf94a9e4c48a0c37dceeb749d9847343c4d85b065efda9dc5983a8906  locked/tasks/test_Tseen.json
c7d22d7614fa4971d842acb7ac18e28b7ea2006896ae588543a33327cb141a48  locked/tasks/test_Theld.json
7a97997b9d9ed5478b36a58d2b093a09ed82cfd92a26b674ab5c5b847befcc0f  arena/tasks.py
6b8d416057a5e5367613649a72d469dbb7dcb0e777de73383a6e66c6226a2585  arena/task_labeler.py
d094e0f84caf41f1e7f0d6a4db34f75c067bcef2ac59c7221fa42d843f5415ac  arena/methods/task_expert.py
```

## 9. Sai lệch (điền sau nếu có)

_(chưa có)_
