"""Công cụ hiệu chuẩn CL-0 (chạy với phần cứng thật; phần tính toán thuần nằm ở calib_tools.py và có test).

    python -m cl0.calibrate fk          --config cfg.toml            # kiểm FK: in vị trí TCP khi bạn kéo tay bằng tay, so với thước
    python -m cl0.calibrate intrinsics  --config cfg.toml            # (tuỳ chọn) nội tham số + gỡ méo từ bàn cờ
    python -m cl0.calibrate board       --config cfg.toml            # camera -> mặt băng (bàn cờ + chạm 9 điểm bằng TCP) => calib.json
    python -m cl0.calibrate belt        --config cfg.toml            # hướng băng, mm/xung, độ trễ ảnh<->băng bằng vạch phẳng
    python -m cl0.calibrate background  --config cfg.toml            # nền băng trống                                      => background.npz
    python -m cl0.calibrate lag         --config cfg.toml            # độ trễ servo của tay => gợi ý executor.lead_s

Thứ tự: fk -> (intrinsics) -> board -> belt -> background -> lag. Mỗi bước in "KẾT QUẢ" và việc cần chép vào cấu hình.
[chưa kiểm trên phần cứng] — các hàm tính toán đã có test với dữ liệu tổng hợp, phần vào/ra thiết bị thì chưa chạy trên máy bạn.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import math
import os
import sys
import time
from typing import List, Optional

import cv2
import numpy as np

from . import calib_tools as ct
from .config import Config, load_config
from .geometry import PlaneCalib, Rectifier, Window, auto_window, calib_from_board, fit_belt_motion, fit_rigid_2d, perp, unit
from .kinematics import SO101Kinematics
from .perception import build_background


# ------------------------------------------------------------------------------------------------------------ thiết bị
def _paths(cfg: Config, a):
    calib = a.calib or cfg.calib_path
    d = os.path.dirname(os.path.abspath(calib))
    return calib, os.path.join(d, "intrinsics.npz"), (a.background or cfg.background_path)


def open_camera(cfg: Config, calib_path: str):
    from .hw.camera import CameraThread, Undistorter
    und = None
    ip = os.path.join(os.path.dirname(os.path.abspath(calib_path)), "intrinsics.npz")
    if os.path.exists(ip):
        und = Undistorter(ip, (cfg.camera.width, cfg.camera.height))
        print(f"[camera] dùng gỡ méo từ {ip}")
    cam = CameraThread(cfg.camera, undistort=und)
    cam.start()
    return cam


def grab(cam, n: int = 1, timeout: float = 5.0, spacing: float = 0.0):
    out, t_end = [], time.monotonic() + timeout
    while len(out) < n and time.monotonic() < t_end:
        f = cam.poll()
        if f is None:
            time.sleep(0.004)
            continue
        out.append(f)
        if spacing:
            time.sleep(spacing)
    if len(out) < n:
        raise RuntimeError(f"camera chỉ trả {len(out)}/{n} khung trong {timeout}s")
    return out


def open_arm(cfg: Config, kin: SO101Kinematics):
    from .hw.arm import LeRobotArm
    lo, hi = kin.limits_deg
    arm = LeRobotArm(cfg.robot, limits_deg=np.stack([lo, hi], axis=1), max_jump_deg=45.0)
    arm.connect()
    return arm


def open_belt(cfg: Config, counts_only: bool = False):
    from .hw.belt import Belt
    bcfg = cfg.belt
    if counts_only and bcfg.kind == "counter" and bcfg.mm_per_step <= 0:
        bcfg = dataclasses.replace(bcfg, mm_per_step=1.0)          # đếm xung thô để hiệu chuẩn mm/xung
    b = Belt(bcfg)
    b.open()
    return b


def _kin(cfg: Config) -> SO101Kinematics:
    return SO101Kinematics(urdf=cfg.robot.urdf or None, tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)


# ------------------------------------------------------------------------------------------------------------ fk
def cmd_fk(a, cfg: Config) -> int:
    kin = _kin(cfg)
    arm = open_arm(cfg, kin)
    try:
        arm.torque(False)
        print("Torque ĐÃ TẮT: tay có thể sụp xuống. Đỡ tay bằng tay. Kéo tay tới vài tư thế, so TCP với thước đo (Ctrl-C để thoát).")
        print("Mốc: gốc W = khung đế robot (chân URDF base_link); x về phía trước, y sang trái nhìn từ phía sau robot, z lên. "
              "Trục pan nằm ở (x, y) ≈ (38.8, 0) mm.")
        print("Kiểm: (1) chạm điểm TCP vật lý xuống mặt bàn mà đế robot đặt trên đó -> z phải ≈ 0 (mặt gắn đế) nếu TCP đúng ở mũi má; "
              "(2) khoảng cách ngang TCP tới trục pan so với thước; (3) 'trục khép' là hướng x của khung công cụ trong W: dùng để biết dấu của "
              "robot.tcp_offset_mm[0] (dương = về phía mà vectơ này chỉ tới).")
        while True:
            st = arm.state()
            p, ap, cl, pitch, yaw = kin.tool_axes(st.q_deg)
            lo, hi = kin.limits_deg
            warn = "  <-- sát giới hạn khớp" if np.any(st.q_deg < lo + 3) or np.any(st.q_deg > hi - 3) else ""
            print(f"\rq={np.array2string(st.q_deg, precision=1, suppress_small=True)} gripper={st.gripper:5.1f} | "
                  f"TCP x={p[0]:7.1f} y={p[1]:7.1f} z={p[2]:7.1f} mm | tiến vào {np.array2string(ap, precision=2)} | khép {np.array2string(cl, precision=2)} | yaw={yaw:6.1f}°{warn}   ",
                  end="", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print()
    finally:
        arm.disconnect()
    return 0


# ------------------------------------------------------------------------------------------------------------ intrinsics
def cmd_intrinsics(a, cfg: Config) -> int:
    calib_path, intr_path, _ = _paths(cfg, a)
    if os.path.exists(intr_path):
        os.rename(intr_path, intr_path + ".bak")                 # để camera đọc ảnh chưa gỡ méo
    cam = open_camera(cfg, calib_path)
    objp = np.zeros((a.cols * a.rows, 3), np.float32)
    objp[:, :2] = ct.board_object_points(a.cols, a.rows, a.square_mm)
    obj, img = [], []
    size = None
    try:
        print(f"Cầm bàn cờ {a.cols}x{a.rows} góc trong, ô {a.square_mm} mm, đưa vào nhiều vị trí/góc nghiêng khác nhau, phủ cả rìa ảnh. "
              f"Cần >= {a.n} lần. Enter = chụp, q = xong.")
        while True:
            r = input(f"[{len(obj)}/{a.n}] Enter để chụp > ").strip().lower()
            if r == "q" and len(obj) >= 8:
                break
            f = grab(cam, 1)[0]
            c = ct.detect_board(f.img, a.cols, a.rows)
            if c is None:
                print("  không thấy bàn cờ")
                continue
            size = (f.img.shape[1], f.img.shape[0])
            obj.append(objp.copy())
            img.append(c.reshape(-1, 1, 2).astype(np.float32))
            if len(obj) >= a.n and r != "":
                break
        rms, K, dist, _, _ = cv2.calibrateCamera(obj, img, size, None, None)
        np.savez(intr_path, K=K, dist=dist, rms=rms, size=np.array(size))
        print(f"KẾT QUẢ: sai số chiếu lại {rms:.3f} px (tốt: < 0.5). Đã lưu {intr_path}. Camera sẽ tự gỡ méo từ giờ; LÀM LẠI board/belt/background.")
        if rms > 1.0:
            print("CẢNH BÁO: sai số lớn; chụp thêm ở các góc nghiêng/rìa ảnh.")
    finally:
        cam.stop()
    return 0


# ------------------------------------------------------------------------------------------------------------ board
def cmd_board(a, cfg: Config) -> int:
    calib_path, _, _ = _paths(cfg, a)
    kin = _kin(cfg)
    cam = open_camera(cfg, calib_path)
    try:
        input(f"Đặt bàn cờ {a.cols}x{a.rows} góc trong (ô {a.square_mm} mm) PHẲNG trên băng ĐỨNG YÊN, trong tầm nhìn và trong tầm với của tay. Enter > ")
        frames = grab(cam, a.frames, spacing=0.05)
        cs = [ct.detect_board(f.img, a.cols, a.rows) for f in frames]
        cs = [c for c in cs if c is not None]
        if len(cs) < max(3, a.frames // 2):
            print(f"Chỉ thấy bàn cờ ở {len(cs)}/{a.frames} khung. Kiểm tra ánh sáng/phản chiếu/kích thước.")
            return 1
        corners = np.median(np.stack(cs), axis=0)
        jitter = float(np.mean(np.std(np.stack(cs), axis=0)))
        board_xy = ct.board_object_points(a.cols, a.rows, a.square_mm)
        touch = [int(x) for x in a.touch.split(",")] if a.touch else ct.default_touch_indices(a.cols, a.rows)
        prev = os.path.join(os.path.dirname(os.path.abspath(calib_path)), "board_preview.png")
        cv2.imwrite(prev, ct.draw_board_preview(frames[-1].img, corners, touch))
        print(f"Đã thấy {a.cols * a.rows} góc (nhiễu giữa khung {jitter:.2f} px). Xem {prev}: vòng đỏ = góc cần chạm, theo thứ tự.")
    finally:
        cam.stop()
    arm = open_arm(cfg, kin)
    tw, tz = [], []
    try:
        arm.torque(False)
        print("Torque ĐÃ TẮT: đỡ tay. Với mỗi góc đỏ: đưa ĐIỂM TCP (điểm bạn muốn coi là tâm kẹp, nên là đầu má kẹp cố định ở độ cao mặt băng) "
              "chạm đúng góc rồi nhấn Enter.")
        for n, k in enumerate(touch):
            input(f"  Chạm góc #{k} ({n + 1}/{len(touch)}), Enter > ")
            qs = []
            for _ in range(10):
                qs.append(arm.state().q_deg)
                time.sleep(0.02)
            p, *_ = kin.tool_axes(np.mean(qs, axis=0))
            tw.append(p[:2])
            tz.append(p[2])
            print(f"     TCP = ({p[0]:.1f}, {p[1]:.1f}, {p[2]:.1f}) mm")
    finally:
        arm.disconnect()
    tb_xy, tw_xy, tz = board_xy[touch], np.array(tw), np.asarray(tz)
    keep, loo = ct.reject_touch_outliers(tb_xy, tw_xy)
    print("  sai số leave-one-out từng điểm chạm (mm): " + ", ".join(f"#{k}:{e:.1f}" for k, e in zip(touch, loo)))
    if not keep.all():
        bad = [touch[i] for i in np.nonzero(~keep)[0]]
        print(f"CẢNH BÁO: loại điểm chạm {bad} (lệch hẳn so với các điểm còn lại — chạm nhầm góc hoặc trượt tay?). Nên chạy lại nếu còn < 6 điểm tốt.")
    fs = fit_rigid_2d(tb_xy[keep], tw_xy[keep], allow_scale=True, allow_reflection=True)
    se = fs.rms * math.sqrt(keep.sum() / max(keep.sum() - 2, 1)) / max(math.sqrt(float(np.sum((tb_xy[keep] - tb_xy[keep].mean(axis=0)) ** 2))), 1e-6)
    print(f"  tỉ lệ kích thước thực/danh nghĩa của bàn cờ suy từ điểm chạm: {fs.s:.3f} ± {se:.3f} (đúng ≈ 1; bàn cờ in ra hay bị máy in co/giãn)")
    if abs(fs.s - 1.0) > max(0.015, 3 * se):
        print(f"CẢNH BÁO: ô bàn cờ thật có vẻ {'nhỏ' if fs.s < 1 else 'lớn'} hơn {a.square_mm} mm khoảng {abs(fs.s - 1) * 100:.1f}% — "
              f"đo lại ô in bằng thước và chạy lại với --square-mm đúng.")
    z_plane = float(np.mean(tz[keep])) + a.z_offset
    cal = calib_from_board(corners, board_xy, tb_xy[keep], tw_xy[keep], z_plane, image_size=(cfg.camera.width, cfg.camera.height))
    cal.n_points = len(corners)
    print(f"KẾT QUẢ: sai số chạm (rigid) {cal.touch_rms_mm:.2f} mm, khớp homography {cal.rms_mm:.2f} mm (leave-one-out {cal.loo_rms_mm:.2f} mm), "
          f"mặt băng z = {z_plane:.1f} mm (độ lệch giữa các lần chạm: {np.std(tz[keep]):.1f} mm). {cal.note}")
    if cal.touch_rms_mm > 3.0:
        print("CẢNH BÁO: sai số chạm > 3 mm — kiểm tra TCP chạm đúng góc, FK (bước `fk`), hoặc tcp_offset_mm.")
    if np.std(tz[keep]) > 3.0:
        print("CẢNH BÁO: z các điểm chạm lệch nhau > 3 mm — băng/bàn cờ không phẳng hoặc chạm lúc cao lúc thấp.")
    old = PlaneCalib.load(calib_path) if os.path.exists(calib_path) else None
    if old is not None:
        print("Lưu ý: hiệu chuẩn mới => hướng băng/mm-xung phải đo lại (`belt`) và dựng lại nền (`background`).")
    cal.save(calib_path)
    print(f"Đã lưu {calib_path}")
    return 0


# ------------------------------------------------------------------------------------------------------------ belt
def cmd_belt(a, cfg: Config) -> int:
    calib_path, _, _ = _paths(cfg, a)
    calib = PlaneCalib.load(calib_path)
    cam = open_camera(cfg, calib_path)
    belt = open_belt(cfg, counts_only=True)
    lat_assumed = cfg.camera.latency_s
    runs = []
    try:
        input("Dọn băng TRỐNG (không vật, tay ra khỏi ảnh). Enter để chụp ảnh nền tham chiếu > ")
        ref = np.mean([f.img.astype(np.float32) for f in grab(cam, 15, spacing=0.03)], axis=0).astype(np.uint8)
        for r in range(a.runs):
            input(f"[lượt {r + 1}/{a.runs}] Đặt VẠCH PHẲNG (giấy/băng dính màu tương phản, KHÔNG dùng khối cao) ở thượng nguồn trong tầm nhìn, "
                  f"vị trí ngang khác lần trước. Enter > ")
            tr, uv = [], []
            t_start = time.monotonic()
            started = False
            while True:
                now = time.monotonic()
                if not started and now - t_start > a.static_s:
                    belt.start(a.speed)
                    started = True
                    t_cmd = now
                if started and now - t_cmd > a.duration:
                    break
                f = cam.poll()
                if f is None:
                    time.sleep(0.003)
                    continue
                m = ct.find_marker(f.img, ref)
                if m is not None:
                    tr.append(f.t_capture + lat_assumed)          # = thời điểm NHẬN khung
                    uv.append(m[:2])
            belt.stop()
            time.sleep(a.speed / max(cfg.belt.accel_mm_s2, 1.0) + 1.0)
            if len(tr) < 20:
                print(f"  lượt {r + 1}: chỉ thấy vạch ở {len(tr)} khung — bỏ lượt")
                continue
            runs.append((np.asarray(tr), np.asarray(uv), t_start))
            print(f"  lượt {r + 1}: {len(tr)} khung")
            input("  Đưa vạch về vị trí thượng nguồn (băng dừng hẳn), Enter > ") if r + 1 < a.runs else None
        if len(runs) < 2:
            print("Cần >= 2 lượt hợp lệ.")
            return 1
        # --- hướng băng + mm/xung từ đoạn băng chạy
        if cfg.belt.kind == "counter":
            th, sh = belt.history()
            tracks = []
            for tr, uv, _ in runs:
                sel = tr > (tr[0] + a.static_s + 0.6)
                xy = calib.pix_to_world(uv[sel])
                steps = np.interp(tr[sel] - lat_assumed, th, sh)      # xung thô (mm_per_step tạm = 1)
                tracks.append((steps, xy))
            phi, mm_step, lat_rms = fit_belt_motion(tracks)
            print(f"KẾT QUẢ hướng băng φ = {phi:.2f}° (W), mm/xung = {mm_step:.5f}, lệch ngang {lat_rms:.2f} mm")
            hist_mm = (th, sh * mm_step)
        else:
            tracks = []
            for tr, uv, _ in runs:
                sel = tr > (tr[0] + a.static_s + 0.6)
                xy = calib.pix_to_world(uv[sel])
                tracks.append((tr[sel] - tr[sel][0], xy))
            phi, mm_s, lat_rms = fit_belt_motion(tracks)
            print(f"KẾT QUẢ hướng băng φ = {phi:.2f}° (W), tốc độ đo được {mm_s:.2f} mm/s (lệnh {a.speed:.1f}), lệch ngang {lat_rms:.2f} mm")
            mm_step = 0.0
            tt0 = min(r[2] for r in runs) - 2.0
            th = np.arange(tt0, max(r[0][-1] for r in runs) + 1.0, 0.005)
            hist_mm = (th, np.array([belt.s_at(t) for t in th]))
        # --- độ trễ ảnh <-> băng
        u_hat = unit(phi)
        lats = []
        for k, (tr, uv, t_start) in enumerate(runs):
            a_obs = calib.pix_to_world(uv) @ u_hat
            m_h = hist_mm[0] >= t_start - 0.05                       # chỉ phần lịch sử của lượt này: băng ĐỨNG YÊN lúc bắt đầu lượt
            try:
                d, e, sens = ct.estimate_latency(tr, a_obs, hist_mm[0][m_h], hist_mm[1][m_h])
            except ValueError as ex:
                print(f"  lượt {k + 1}: không ước lượng được độ trễ: {ex}")
                continue
            ok = sens > 0.2
            print(f"  lượt {k + 1}: δ = {d * 1e3:6.1f} ms (rms sai dư {e:.2f} mm, độ nhạy {sens:.2f} mm){'' if ok else '  <- độ nhạy thấp, bỏ'}")
            if ok:
                lats.append(d)
        if lats:
            lat = float(np.median(lats))
            print(f"KẾT QUẢ độ trễ ảnh<->băng: camera.latency_s = {lat:.3f}  (trung vị {len(lats)} lượt, phân tán {np.std(lats) * 1e3:.1f} ms)")
            calib.latency_s = lat
        calib.belt_dir_deg = float(phi)
        if cfg.belt.kind == "counter":
            calib.mm_per_step = float(mm_step)
            print(f"Chép vào cấu hình: [belt] mm_per_step = {mm_step:.6f}")
        calib.save(calib_path)
        print(f"Đã cập nhật {calib_path} (belt_dir_deg, mm_per_step, latency_s). Nhớ chép camera.latency_s vào cấu hình.")
    finally:
        try:
            belt.stop()
        finally:
            belt.close()
            cam.stop()
    return 0


# ------------------------------------------------------------------------------------------------------------ background
def cmd_background(a, cfg: Config) -> int:
    from .system import file_sha256
    calib_path, _, bg_path = _paths(cfg, a)
    calib = PlaneCalib.load(calib_path)
    if calib.belt_dir_deg == 0.0 and calib.method == "board" and calib.latency_s == 0.0:
        print("CẢNH BÁO: chưa thấy kết quả `belt` trong calib.json (hướng băng = 0°?). Chạy `belt` trước.")
    ar = tuple(float(x) for x in a.a_range.split(",")) if a.a_range else None
    br = tuple(float(x) for x in a.b_range.split(",")) if a.b_range else None
    win = auto_window(calib, cfg.perception.res_mm, a.shrink, ar, br)
    rect = Rectifier(calib, win)
    print(f"Cửa sổ nhìn từ trên: a ∈ [{win.a_min:.0f}, {win.a_max:.0f}] mm, b ∈ [{win.b_min:.0f}, {win.b_max:.0f}] mm, ảnh {rect.size[0]}x{rect.size[1]} px "
          f"({cfg.perception.res_mm} mm/px). Hạn chế bằng --a-range/--b-range nếu có vật tĩnh ngoài băng.")
    mpx = rect.size[0] * rect.size[1] / 1e6
    if mpx > 0.45:
        print(f"CẢNH BÁO: cửa sổ {mpx:.2f} Mpx — mỗi lần nhận thức tốn ~{mpx * 75:.0f} ms trên CPU cỡ máy phát triển (trễ vòng kín). "
              f"Khuyến nghị thu về băng + vùng với tới (--b-range b_min,b_max theo toạ độ in ở trên; --a-range tương tự) hoặc tăng perception.res_mm lên 1.0.")
    cam = open_camera(cfg, calib_path)
    belt = None
    try:
        input("Dọn băng TRỐNG; đưa tay robot về tư thế NHÀ (home) để cánh tay thành một phần của nền; tay người ra khỏi ảnh. Enter > ")
        frames = []
        if cfg.belt.textured:
            if cfg.belt.period_mm <= 0 or cfg.belt.kind != "counter":
                print("Băng có texture cần belt.period_mm > 0 và belt.kind = counter.")
                return 1
            belt = open_belt(cfg)
            belt.start(a.speed)
            time.sleep(a.speed / max(cfg.belt.accel_mm_s2, 1.0) + 1.0)
            t_run = 1.3 * cfg.belt.period_mm / a.speed
            print(f"Chạy băng {t_run:.0f} s để phủ hơn một vòng ({cfg.belt.period_mm:.0f} mm)…")
            t_end = time.monotonic() + t_run
            while time.monotonic() < t_end:
                f = cam.poll()
                if f is None:
                    time.sleep(0.003)
                    continue
                frames.append((f.img, belt.s_at(f.t_capture)))
            belt.stop()
            s_all = np.array([s for _, s in frames])
            print(f"  s phủ {s_all.max() - s_all.min():.0f} mm / chu vi {cfg.belt.period_mm:.0f} mm")
            if s_all.max() - s_all.min() < cfg.belt.period_mm:
                print("CẢNH BÁO: chưa phủ đủ một vòng; tăng thời gian/tốc độ.")
        else:
            fr = grab(cam, a.frames, spacing=0.1)
            frames = [(f.img, 0.0) for f in fr]
        bg = build_background(frames, rect, cfg.perception, textured=cfg.belt.textured, period_mm=cfg.belt.period_mm)
        bg.meta = dict(calib_sha=file_sha256(calib_path), created=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                       n_frames=len(frames), textured=cfg.belt.textured)
        bg.save(bg_path)
        sig = float(np.median(bg.sigma))
        print(f"KẾT QUẢ: {len(frames)} khung, độ lệch chuẩn nền (trung vị) {sig:.1f} mức xám. Ngưỡng hiệu dụng ≈ max(k_sigma·σ, t_min) = "
              f"{max(cfg.perception.k_sigma * sig, cfg.perception.t_min):.0f}. Đã lưu {bg_path}")
        prev = os.path.splitext(bg_path)[0] + "_preview.png"
        cv2.imwrite(prev, np.clip(bg.window(0.0)[0], 0, 255).astype(np.uint8))
        print(f"Xem {prev}: không được có vật lạ/bóng tay trên nền.")
        if frames:                                                    # khung camera gốc + viền cửa sổ + chiều băng
            pw = os.path.splitext(bg_path)[0] + "_window.png"
            img = frames[-1][0].copy()
            ab = np.array([[win.a_min, win.b_min], [win.a_max, win.b_min], [win.a_max, win.b_max], [win.a_min, win.b_max]])
            xy = ab[:, :1] * unit(calib.belt_dir_deg) + ab[:, 1:2] * perp(calib.belt_dir_deg)
            cv2.polylines(img, [np.round(calib.world_to_pix(xy)).astype(np.int32).reshape(-1, 1, 2)], True, (0, 255, 0), 2)
            c0 = calib.world_to_pix(xy.mean(axis=0))[0]
            c1 = calib.world_to_pix(xy.mean(axis=0) + 60.0 * unit(calib.belt_dir_deg))[0]
            cv2.arrowedLine(img, tuple(int(x) for x in c0), tuple(int(x) for x in c1), (0, 255, 255), 2, tipLength=0.3)
            cv2.imwrite(pw, img)
            print(f"Xem {pw}: viền xanh = cửa sổ nhận thức, mũi tên vàng = chiều băng chạy (+a).")
    finally:
        if belt is not None:
            belt.stop()
            belt.close()
        cam.stop()
    return 0


# ------------------------------------------------------------------------------------------------------------ lag
def cmd_lag(a, cfg: Config) -> int:
    calib_path, _, _ = _paths(cfg, a)
    calib = PlaneCalib.load(calib_path)
    from .system import get_reach
    kin = _kin(cfg)
    reach = get_reach(kin, cfg, os.path.join(os.path.expanduser("~"), ".cache", "cl0"))
    zb = calib.z_plane_mm
    z = zb + cfg.executor.z_grasp_above_belt_mm + cfg.executor.pre_height_mm
    phi = calib.belt_dir_deg
    u, v = unit(phi), perp(phi)
    # đoạn thẳng dọc băng, giữa băng, nằm trọn trong vùng với tới ở độ cao z
    c_ab = np.array(calib.pix_to_world(np.array([[cfg.camera.width / 2, cfg.camera.height / 2]]))[0]) @ np.c_[u, v]
    best = None
    for b in np.arange(c_ab[1] - 40, c_ab[1] + 41, 10.0):
        A = np.arange(c_ab[0] - 250, c_ab[0] + 250, 5.0)
        ok = [reach.contains(*(a_ * u + b * v), z, inner_mm=8.0) for a_ in A]
        run, i = [], 0
        while i < len(A):
            if ok[i]:
                j = i
                while j < len(A) and ok[j]:
                    j += 1
                run.append((A[i], A[j - 1]))
                i = j
            else:
                i += 1
        for r in run:
            if best is None or (r[1] - r[0]) > (best[1][1] - best[1][0]):
                best = (b, r)
    need = a.speed * (a.duration + 0.5)
    if best is None or (best[1][1] - best[1][0]) < need:
        print(f"Không có đoạn thẳng dọc băng dài ≥ {need:.0f} mm trong vùng với tới ở z={z:.0f} mm. Giảm --speed/--duration hoặc dời băng.")
        return 1
    b0, (a_lo, a_hi) = best
    a_start = a_lo + 0.5 * ((a_hi - a_lo) - need)
    print(f"Đoạn thử: b={b0:.0f}, a từ {a_start:.0f} đến {a_start + need:.0f} mm tại z={z:.0f}. Tay sẽ chạy dọc băng với {a.speed} mm/s trong {a.duration} s.")
    arm = open_arm(cfg, kin)
    try:
        input("Vùng robot TRỐNG, băng DỪNG. Enter để tay đi tới điểm đầu (chậm) > ")
        xy0 = a_start * u + b0 * v
        r = kin.ik([float(xy0[0]), float(xy0[1]), float(z)], phi + 90.0, q0_deg=arm.state().q_deg, tilt_deg=cfg.robot.tilt_deg)
        if not r.ok:
            print("IK không ra nghiệm ở điểm đầu.")
            return 1
        from .hw.arm import go_to
        go_to(arm, time.monotonic, r.q_deg, cfg.robot.gripper_open, 3.0, sleep=time.sleep)
        time.sleep(0.8)
        t_log, c_log, m_log = [], [], []
        q_last = arm.state().q_deg.copy()
        t0 = time.monotonic()
        next_t = t0
        dt_ = 1.0 / cfg.executor.control_hz
        while True:
            t = time.monotonic() - t0
            if t > a.duration:
                break
            xy = xy0 + a.speed * t * u
            rr = kin.ik([float(xy[0]), float(xy[1]), float(z)], phi + 90.0, q0_deg=q_last, tilt_deg=cfg.robot.tilt_deg, max_seeds=1)
            if not rr.ok:
                print("IK thất bại giữa chừng; dừng.")
                break
            q_last = rr.q_deg
            arm.send(rr.q_deg, cfg.robot.gripper_open)
            st = arm.state()
            p, *_ = kin.tool_axes(st.q_deg)
            t_log.append(t)
            c_log.append(float(xy @ u))
            m_log.append(float(p[:2] @ u))
            next_t += dt_
            time.sleep(max(0.0, next_t - time.monotonic()))
        tau, sd = ct.estimate_arm_lag(np.array(t_log), np.array(c_log), np.array(m_log), a.speed)
        print(f"KẾT QUẢ: độ trễ servo của tay τ = {tau * 1e3:.0f} ms (độ lệch chuẩn mẫu {sd * 1e3:.0f} ms). Gợi ý: executor.lead_s = {tau:.3f}")
        print("(Bộ thực thi còn có tích phân bù lag_ki nên giá trị này chỉ giúp hội tụ nhanh hơn; không cần chính xác tuyệt đối.)")
        go_to(arm, time.monotonic, np.asarray(cfg.robot.home_q_deg, float), cfg.robot.gripper_open, 3.0, sleep=time.sleep)
    finally:
        arm.disconnect()
    return 0


# ------------------------------------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--config", required=True)
        p.add_argument("--calib", default=None)
        p.add_argument("--background", default=None)

    p = sub.add_parser("fk"); common(p)
    p = sub.add_parser("intrinsics", help="(tuỳ chọn) nội tham số + gỡ méo từ bàn cờ"); common(p)
    p.add_argument("--cols", type=int, default=9, help="số góc TRONG theo chiều ngang của bàn cờ (ô = cols+1)")
    p.add_argument("--rows", type=int, default=6, help="số góc trong theo chiều dọc")
    p.add_argument("--square-mm", type=float, default=20.0, help="cạnh một ô (mm), đo bằng thước trên bản in")
    p.add_argument("--n", type=int, default=15, help="số góc nhìn khác nhau cần chụp")
    p = sub.add_parser("board", help="camera -> mặt băng: bàn cờ nằm yên trên băng + chạm các điểm bằng TCP"); common(p)
    p.add_argument("--cols", type=int, default=9, help="số góc TRONG theo chiều ngang (bàn cờ có cols+1 ô); phải khớp bản in")
    p.add_argument("--rows", type=int, default=6, help="số góc trong theo chiều dọc")
    p.add_argument("--square-mm", type=float, default=20.0,
                   help="cạnh một ô (mm). Ô to hơn => các điểm chạm cách xa nhau hơn => sai số xoay/tịnh tiến nhỏ hơn (nhiễu tay ~1 mm mỗi lần chạm)")
    p.add_argument("--frames", type=int, default=20, help="số khung trung bình để ổn định vị trí góc")
    p.add_argument("--touch", default=None,
                   help="chỉ số góc cần chạm, ví dụ 0,8,45,53,27 (mặc định: 9 điểm = 4 góc + 4 trung điểm cạnh + tâm, đi vòng viền rồi vào tâm)")
    p.add_argument("--z-offset", type=float, default=0.0, help="cộng vào z mặt băng (ví dụ độ dày giấy)")
    p = sub.add_parser("belt", help="hướng băng, mm/xung, độ trễ ảnh<->băng bằng vạch phẳng"); common(p)
    p.add_argument("--speed", type=float, default=60.0,
                   help="tốc độ chạy băng khi đo: mm/s nếu belt.mm_per_step > 0 trong cấu hình; nếu chưa biết mm/xung (= 0) thì là XUNG/GIÂY")
    p.add_argument("--runs", type=int, default=3, help="số lượt (vạch đặt ở vị trí ngang khác nhau); lấy trung vị")
    p.add_argument("--static-s", type=float, default=1.5, help="giây vạch đứng yên TRƯỚC khi bật băng (cần >= 5 khung; để ước lượng độ trễ ảnh)")
    p.add_argument("--duration", type=float, default=4.0, help="giây chạy băng mỗi lượt")
    p = sub.add_parser("background", help="nền băng trống (kèm tay robot ở tư thế nhà) => background.npz"); common(p)
    p.add_argument("--frames", type=int, default=60, help="số khung dựng nền")
    p.add_argument("--speed", type=float, default=60.0, help="tốc độ băng khi dựng nền có texture (mm/s)")
    p.add_argument("--shrink", type=float, default=10.0, help="co cửa sổ nhìn từ trên vào trong phần ảnh camera nhìn thấy (mm) để tránh méo/viền ảnh")
    p.add_argument("--a-range", default=None, help="giới hạn cửa sổ theo dọc băng: 'a_min,a_max' (mm, toạ độ W-căn-theo-băng đã in)")
    p.add_argument("--b-range", default=None, help="giới hạn cửa sổ theo ngang băng: 'b_min,b_max'")
    p = sub.add_parser("lag", help="độ trễ servo của tay => gợi ý executor.lead_s"); common(p)
    p.add_argument("--speed", type=float, default=40.0, help="tốc độ TCP dọc băng khi đo (mm/s)")
    p.add_argument("--duration", type=float, default=3.0, help="giây đo")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    return {"fk": cmd_fk, "intrinsics": cmd_intrinsics, "board": cmd_board, "belt": cmd_belt, "background": cmd_background,
            "lag": cmd_lag}[a.cmd](a, cfg)


if __name__ == "__main__":
    raise SystemExit(main())
