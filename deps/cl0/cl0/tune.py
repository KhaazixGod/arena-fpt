"""Công cụ cho giai đoạn chỉnh (≤ 2 ngày làm việc, §3.4): xem nhận thức trực tiếp và đặt băng đúng vùng tay với tới.

    python -m cl0.tune reach --config cfg.toml [--image khung.png] [--out reach.png]
        Vẽ lên ảnh camera vùng TCP với tới được (thẳng đứng) ở độ cao kẹp / chờ / nhấc, đường băng, và in bảng "đoạn băng nằm trọn trong vùng với tới"
        theo từng độ lệch ngang b => biết đặt băng ở đâu so với đế robot và cửa sổ nhặt a_pick_min/a_pick_max nên là bao nhiêu.
    python -m cl0.tune watch --config cfg.toml [--seconds 30] [--out tune_out] [--show] [--belt-speed 50]
        Chạy bộ nhận thức CL-0 trên camera thật với hiệu chuẩn + nền thật; lưu ảnh lớp phủ (viền mặt nạ, điểm kẹp, trục khép, bề rộng,
        lý do loại) và thống kê (thời gian xử lý, số phát hiện, bề rộng) => chỉnh perception.* và perception.grasp.* rồi chạy lại.

Mọi thứ ở đây chỉ ĐỌC (camera, file hiệu chuẩn); trừ ``--belt-speed`` (chạy băng). Không ra lệnh cho tay.
[chưa kiểm trên phần cứng] — logic đã có test với camera/băng ảo (xem tests/ và cl0/sim/lab.py).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from .config import Config, load_config
from .geometry import PlaneCalib, Rectifier, perp, unit
from .kinematics import SO101Kinematics
from .perception import BackgroundModel, Detector, window_of
from .reach import TopDownReach
from .viz import draw_detections


# ------------------------------------------------------------------------------------------------------------ vùng với tới
def reach_mask_world(reach: TopDownReach, xy: np.ndarray, z: float, inner_mm: float = 0.0) -> np.ndarray:
    """Với mỗi điểm W (N,2): TCP thẳng đứng có với tới được độ cao z không (có chừa biên inner_mm)? (N,) bool."""
    M = reach.mask_at_z(z)
    n = int(math.ceil(inner_mm / reach.step)) if inner_mm > 0 else 0
    if n > 0:
        M = cv2.erode(M.astype(np.uint8), np.ones((2 * n + 1, 2 * n + 1), np.uint8)) > 0
    xy = np.asarray(xy, float).reshape(-1, 2)
    ix = np.round((xy[:, 0] - reach.x0) / reach.step).astype(int)
    iy = np.round((xy[:, 1] - reach.y0) / reach.step).astype(int)
    ok = (ix >= 0) & (ix < reach.nx) & (iy >= 0) & (iy < reach.ny)
    out = np.zeros(len(xy), bool)
    out[ok] = M[iy[ok], ix[ok]]
    return out


def reach_mask_px(calib: PlaneCalib, reach: TopDownReach, z: float, inner_mm: float = 5.0, stride: int = 2) -> np.ndarray:
    """Mặt nạ (h/stride, w/stride) các điểm ảnh mà mặt băng tại đó nằm trong vùng với tới ở độ cao z."""
    w, h = calib.image_size
    us, vs = np.meshgrid(np.arange(0, w, stride), np.arange(0, h, stride))
    uv = np.stack([us.ravel(), vs.ravel()], axis=1).astype(float)
    return reach_mask_world(reach, calib.pix_to_world(uv), z, inner_mm).reshape(us.shape)


def belt_reach_table(reach: TopDownReach, phi_deg: float, zs: Sequence[float], b_values: Sequence[float], a_range: Tuple[float, float],
                     inner_mm: float = 5.0, step_mm: float = 2.0) -> List[dict]:
    """Với mỗi độ lệch ngang b (hệ băng): đoạn a dài nhất mà MỌI độ cao trong ``zs`` đều với tới được.

    Trả danh sách {b, a_lo, a_hi, length, xy_lo, xy_hi} (xy = toạ độ W của hai đầu đoạn)."""
    u, v = unit(phi_deg), perp(phi_deg)
    A = np.arange(a_range[0], a_range[1] + 1e-9, step_mm)
    out = []
    for b in b_values:
        xy = A[:, None] * u + b * v
        ok = np.ones(len(A), bool)
        for z in zs:
            ok &= reach_mask_world(reach, xy, z, inner_mm)
        best = (0, -1)
        i = 0
        while i < len(A):
            if ok[i]:
                j = i
                while j < len(A) and ok[j]:
                    j += 1
                if j - i > best[1] - best[0] + 1:
                    best = (i, j - 1)
                i = j
            else:
                i += 1
        if best[1] >= best[0]:
            lo, hi = float(A[best[0]]), float(A[best[1]])
            out.append(dict(b=float(b), a_lo=lo, a_hi=hi, length=hi - lo, xy_lo=(lo * u + b * v).tolist(), xy_hi=(hi * u + b * v).tolist()))
        else:
            out.append(dict(b=float(b), a_lo=float("nan"), a_hi=float("nan"), length=0.0, xy_lo=None, xy_hi=None))
    return out


def plan_belt(tab: Sequence[dict], width_mm: float, need_mm: float, phi_deg: float) -> Optional[dict]:
    """Chọn độ lệch ngang b0 của TÂM băng (rộng width_mm) sao cho đoạn a nằm trọn trong vùng với tới ở MỌI vị trí ngang băng dài nhất.
    Trả {b0, a_lo, a_hi, length, ok, xy_lo, xy_hi} hoặc None nếu không có vị trí nào phủ hết bề rộng băng."""
    rows = [r for r in tab]
    if not rows:
        return None
    bs = np.array([r["b"] for r in rows])
    best = None
    for b0 in bs:
        band = [r for r in rows if abs(r["b"] - b0) <= width_mm / 2.0 + 1e-9]
        n_need = int(np.sum(np.abs(bs - b0) <= width_mm / 2.0 + 1e-9))
        if len(band) < n_need or any(r["length"] <= 0 for r in band):
            continue
        lo, hi = max(r["a_lo"] for r in band), min(r["a_hi"] for r in band)
        L = hi - lo
        if L <= 0:
            continue
        if best is None or L > best["length"]:
            u, v = unit(phi_deg), perp(phi_deg)
            best = dict(b0=float(b0), a_lo=float(lo), a_hi=float(hi), length=float(L), ok=bool(L >= need_mm),
                        xy_lo=(lo * u + b0 * v).tolist(), xy_hi=(hi * u + b0 * v).tolist())
    return best


def draw_reach_overlay(img: np.ndarray, calib: PlaneCalib, reach: TopDownReach, zs: Dict[str, float], phi_deg: float,
                       inner_mm: float = 5.0) -> np.ndarray:
    """Vẽ viền vùng với tới ở các độ cao zs (tên -> z) lên ảnh camera; tô mờ vùng ở độ cao đầu tiên (độ cao kẹp)."""
    out = img.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    w, h = calib.image_size
    stride = 2
    cols = [(0, 220, 0), (0, 200, 255), (60, 60, 255), (255, 160, 0)]
    for k, (name, z) in enumerate(zs.items()):
        m = reach_mask_px(calib, reach, z, inner_mm, stride)
        m_full = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)[:h, :w]
        if k == 0:
            tint = out.copy()
            tint[m_full > 0] = (0.65 * tint[m_full > 0] + 0.35 * np.array(cols[0])).astype(np.uint8)
            out = tint
        cnts, _ = cv2.findContours(m_full, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cnts, -1, cols[k % len(cols)], 2)
        cv2.putText(out, f"{name} z={z:.0f}", (8, 18 + 16 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cols[k % len(cols)], 1, cv2.LINE_AA)
    c0 = calib.world_to_pix(calib.pix_to_world(np.array([[w / 2, h / 2]])))[0]
    c1 = calib.world_to_pix(calib.pix_to_world(np.array([[w / 2, h / 2]])) + 60.0 * unit(phi_deg))[0]
    cv2.arrowedLine(out, tuple(int(x) for x in c0), tuple(int(x) for x in c1), (255, 255, 0), 2, tipLength=0.3)
    cv2.putText(out, "chieu bang (+a)", (int(c1[0]) + 6, int(c1[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA)
    return out


def _grasp_heights(cfg: Config, z_plane: float) -> Dict[str, float]:
    ex = cfg.executor
    zg = z_plane + ex.z_grasp_above_belt_mm
    return {"kep": zg, "cho": zg + ex.pre_height_mm, "nhac": z_plane + ex.lift_height_mm}


def _kin(cfg: Config) -> SO101Kinematics:
    return SO101Kinematics(urdf=cfg.robot.urdf or None, tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)


def _calibrate_mod():
    from . import calibrate as C            # tra cứu muộn để test có thể vá open_camera/open_belt/time
    return C


def cmd_reach(a, cfg: Config) -> int:
    from .system import get_reach
    calib = PlaneCalib.load(a.calib or cfg.calib_path)
    kin = _kin(cfg)
    reach = get_reach(kin, cfg, os.path.join(os.path.expanduser("~"), ".cache", "cl0"))
    phi = calib.belt_dir_deg
    zs = _grasp_heights(cfg, calib.z_plane_mm)
    print(f"Mặt băng z = {calib.z_plane_mm:.1f} mm (W); độ cao: " + ", ".join(f"{k} {v:.0f}" for k, v in zs.items()) + " mm. Hướng băng φ = "
          f"{phi:.1f}°. Mặt băng so với mặt đế robot (z=0 của W): {calib.z_plane_mm:+.0f} mm "
          f"({'THẤP hơn đế — tốt' if calib.z_plane_mm < -15 else 'CAO ngang đế — vùng với tới thẳng đứng ở độ cao nhấc rất hẹp'}).")
    img = None
    if a.image:
        img = cv2.imread(a.image)
        if img is None:
            raise SystemExit(f"không đọc được ảnh {a.image}")
    else:
        try:
            C = _calibrate_mod()
            cam = C.open_camera(cfg, a.calib or cfg.calib_path)
            try:
                img = C.grab(cam, 1, timeout=5.0)[0].img
            finally:
                cam.stop()
        except Exception as e:                                   # noqa: BLE001 — không có camera: vẽ trên nền xám
            print(f"(không lấy được ảnh camera: {e}; vẽ trên nền xám)")
    if img is None:
        img = np.full((calib.image_size[1], calib.image_size[0], 3), 70, np.uint8)
    # --- bảng đoạn băng nằm trọn trong vùng với tới
    w, h = calib.image_size
    corners = calib.pix_to_world(np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], float))
    ab = np.c_[corners @ unit(phi), corners @ perp(phi)]
    a_rng = (float(ab[:, 0].min()), float(ab[:, 0].max()))
    b_vals = np.arange(math.ceil(ab[:, 1].min() / 10) * 10, ab[:, 1].max() + 1e-9, 10.0)
    tab = belt_reach_table(reach, phi, list(zs.values()), b_vals, a_rng, inner_mm=5.0)
    need = cfg.belt.speed_mm_s * (cfg.executor.t_to_grasp_s + cfg.executor.follow_margin_s)
    print(f"Đoạn băng (dọc a) nằm trọn trong vùng với tới ở CẢ ba độ cao, theo độ lệch ngang b (hệ băng; v̂ = bên trái chiều băng chạy). "
          f"Cần ≳ {need:.0f} mm (= {cfg.belt.speed_mm_s:.0f} mm/s × (t_to_grasp {cfg.executor.t_to_grasp_s} + follow {cfg.executor.follow_margin_s}) s):")
    shown = 0
    for r in tab:
        if r["length"] <= 0 or int(round(r["b"])) % 20 != 0:
            continue
        flag = "  <-- đủ" if r["length"] >= need else ""
        print(f"   b = {r['b']:7.0f}: a ∈ [{r['a_lo']:7.1f}, {r['a_hi']:7.1f}]  dài {r['length']:5.0f} mm   "
              f"W: ({r['xy_lo'][0]:6.0f},{r['xy_lo'][1]:6.0f}) → ({r['xy_hi'][0]:6.0f},{r['xy_hi'][1]:6.0f}){flag}")
        shown += 1
    if shown == 0:
        print("   (không có đường nào; băng quá xa/quá cao so với tầm với — hạ băng hoặc dời lại gần đế)")
    place = plan_belt(tab, cfg.belt.width_mm, need, phi)
    if place is None:
        print(f"KẾT QUẢ: KHÔNG có vị trí nào để băng rộng {cfg.belt.width_mm:.0f} mm nằm trọn trong vùng với tới ở cả ba độ cao. "
              f"Hạ băng (mặt băng thấp hơn đế), hẹp băng, hoặc chấp nhận chỉ nhặt phần băng gần (đặt executor.a_pick_*).")
    else:
        verdict = "ĐỦ" if place["ok"] else f"CHƯA ĐỦ (cần ≥ {need:.0f} mm: giảm tốc độ băng hoặc t_to_grasp_s/follow_margin_s)"
        print(f"KẾT QUẢ: đặt TÂM băng ở b ≈ {place['b0']:.0f} mm (phủ b ∈ [{place['b0'] - cfg.belt.width_mm / 2:.0f}, {place['b0'] + cfg.belt.width_mm / 2:.0f}]); "
              f"khi đó đoạn nhặt a ∈ [{place['a_lo']:.0f}, {place['a_hi']:.0f}] dài {place['length']:.0f} mm — {verdict}.")
        print(f"   Trong W (đế robot), đường tâm băng đi từ ({place['xy_lo'][0]:.0f}, {place['xy_lo'][1]:.0f}) tới ({place['xy_hi'][0]:.0f}, {place['xy_hi'][1]:.0f}) mm. "
              f"Gợi ý [executor] a_pick_min = {math.ceil(place['a_lo'] / 5) * 5:.0f}, a_pick_max = {math.floor(place['a_hi'] / 5) * 5:.0f} "
              f"(a đo từ gốc W; có thể hẹp hơn để vật vào vùng nhặt muộn hơn).")
    out = draw_reach_overlay(img, calib, reach, zs, phi)
    path = a.out or os.path.join(os.path.dirname(os.path.abspath(a.calib or cfg.calib_path)), "reach.png")
    cv2.imwrite(path, out)
    print(f"Đã lưu {path}: viền xanh lá = vùng kẹp, vàng = độ cao chờ, đỏ = độ cao nhấc; chỉ vật nằm trong CẢ ba mới nhặt được.")
    return 0


# ------------------------------------------------------------------------------------------------------------ watch
def cmd_watch(a, cfg: Config) -> int:
    from .system import get_reach
    C = _calibrate_mod()
    calib_path = a.calib or cfg.calib_path
    bg_path = a.background or cfg.background_path
    calib = PlaneCalib.load(calib_path)
    bg = BackgroundModel.load(bg_path)
    rect = Rectifier(calib, window_of(bg))
    det = Detector(rect, bg, cfg.perception)
    reach = None
    if a.reach:
        reach = get_reach(_kin(cfg), cfg, os.path.join(os.path.expanduser("~"), ".cache", "cl0"))
    zg = calib.z_plane_mm + cfg.executor.z_grasp_above_belt_mm
    out_dir = a.out
    os.makedirs(out_dir, exist_ok=True)
    cam = C.open_camera(cfg, calib_path)
    belt = None
    need_belt = bool(a.belt_speed) or cfg.belt.textured
    if need_belt:
        belt = C.open_belt(cfg)
    T = C.time
    stats: Dict[str, list] = {"ms": [], "n_ok": [], "n_wide": [], "n_other": [], "width": [], "reach_ok": []}
    n_saved, n_frames = 0, 0
    t0 = T.monotonic()
    t_save = t0 - 1e9
    try:
        if a.belt_speed:
            belt.start(a.belt_speed)
        while T.monotonic() - t0 < a.seconds:
            f = cam.poll()
            if f is None:
                T.sleep(0.004)
                continue
            s_img = belt.s_at(f.t_capture) if belt is not None else 0.0
            tp = time.perf_counter()
            res = det.detect(f.img, s_img)
            stats["ms"].append((time.perf_counter() - tp) * 1e3)
            n_frames += 1
            ok = [d for d in res.dets if d.ok]
            stats["n_ok"].append(len(ok))
            stats["n_wide"].append(sum(d.reject == "wide" for d in res.dets))
            stats["n_other"].append(sum((not d.ok) and d.reject != "wide" for d in res.dets))
            stats["width"] += [d.width_mm for d in ok]
            sel = None
            if reach is not None and ok:
                u, v = unit(calib.belt_dir_deg), perp(calib.belt_dir_deg)
                inr = [d for d in ok if reach.contains(*((d.a_mm) * u + d.b_mm * v), zg, inner_mm=5.0)
                       and cfg.executor.a_pick_min <= d.a_mm <= cfg.executor.a_pick_max]
                stats["reach_ok"].append(len(inr))
                if inr:
                    sel = max(inr, key=lambda d: d.a_mm)
            vis = draw_detections(res, rect, None if sel is None else (sel.a_mm, sel.b_mm))
            now = T.monotonic()
            if a.show:
                try:
                    cv2.imshow("cl0 watch (s = luu, q = thoat)", vis)
                    k = cv2.waitKey(1) & 0xFF
                    if k == ord("q"):
                        break
                    if k == ord("s"):
                        t_save = -1e9
                except cv2.error:
                    a.show = False
            if now - t_save >= a.save_every:
                t_save = now
                cv2.imwrite(os.path.join(out_dir, f"watch_{n_saved:04d}.png"), vis)
                cv2.imwrite(os.path.join(out_dir, f"watch_{n_saved:04d}_mask.png"), res.mask)
                n_saved += 1
    finally:
        try:
            if belt is not None:
                belt.stop()
        finally:
            if belt is not None:
                belt.close()
            cam.stop()
            if a.show:
                try:
                    cv2.destroyAllWindows()
                except cv2.error:
                    pass
    if n_frames == 0:
        print("Không nhận được khung nào từ camera.")
        return 1
    ms = np.asarray(stats["ms"])
    wd = np.asarray(stats["width"]) if stats["width"] else np.zeros(1)
    summ = dict(frames=n_frames, detect_ms_mean=float(ms.mean()), detect_ms_p95=float(np.percentile(ms, 95)),
                ok_per_frame_mean=float(np.mean(stats["n_ok"])), wide_per_frame_mean=float(np.mean(stats["n_wide"])),
                other_reject_per_frame_mean=float(np.mean(stats["n_other"])),
                width_mm_median=float(np.median(wd)), width_mm_p05=float(np.percentile(wd, 5)), width_mm_p95=float(np.percentile(wd, 95)),
                in_reach_per_frame_mean=float(np.mean(stats["reach_ok"])) if stats["reach_ok"] else None,
                images=n_saved, out_dir=out_dir)
    with open(os.path.join(out_dir, "watch_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summ, fh, indent=2, ensure_ascii=False)
    print(f"KẾT QUẢ: {n_frames} khung; nhận thức {summ['detect_ms_mean']:.0f} ms/khung (p95 {summ['detect_ms_p95']:.0f} ms); "
          f"vật hợp lệ/khung {summ['ok_per_frame_mean']:.2f}, bị loại 'wide' {summ['wide_per_frame_mean']:.2f}, loại khác {summ['other_reject_per_frame_mean']:.2f}; "
          f"bề rộng trung vị {summ['width_mm_median']:.0f} mm (p5–p95: {summ['width_mm_p05']:.0f}–{summ['width_mm_p95']:.0f}). "
          f"Đã lưu {n_saved} ảnh + watch_summary.json vào {out_dir}")
    if summ["detect_ms_p95"] > 0.8 * 1000.0 / max(cfg.camera.fps, 1):
        print("CẢNH BÁO: thời gian nhận thức gần/bằng chu kỳ camera — thu cửa sổ (calibrate background --a-range/--b-range) hoặc tăng perception.res_mm.")
    return 0


# ------------------------------------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--config", required=True)
        p.add_argument("--calib", default=None)
        p.add_argument("--background", default=None)

    p = sub.add_parser("reach"); common(p)
    p.add_argument("--image", default=None, help="ảnh camera để vẽ lên (mặc định: chụp 1 khung)")
    p.add_argument("--out", default=None)
    p = sub.add_parser("watch"); common(p)
    p.add_argument("--seconds", type=float, default=30.0)
    p.add_argument("--out", default="tune_out")
    p.add_argument("--save-every", type=float, default=1.0)
    p.add_argument("--show", action="store_true", help="mở cửa sổ xem trực tiếp (cần màn hình); phím s = lưu, q = thoát")
    p.add_argument("--belt-speed", type=float, default=0.0, help="chạy băng với tốc độ này (mm/s) trong lúc xem; 0 = không chạy")
    p.add_argument("--reach", action="store_true", help="đánh dấu vật nằm trong vùng với tới và cửa sổ nhặt")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    return {"reach": cmd_reach, "watch": cmd_watch}[a.cmd](a, cfg)


if __name__ == "__main__":
    raise SystemExit(main())
