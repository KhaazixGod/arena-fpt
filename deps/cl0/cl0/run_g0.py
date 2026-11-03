"""Bộ chạy G0 (và các lượt thử CL-0 nói chung): đặt vật theo tờ sắp xếp -> chạy -> hỏi người thử -> ghi CSV đúng định dạng g0_analyze.py.

    # thật (cần cấu hình, calib.json, background.npz):
    python -m cl0.run_g0 --config configs/cl0.toml --arrangements arr_novel_C2.csv --cell novel_C2 --out runs/g0 --require-frozen
    # thử quy trình trong mô phỏng, không cần phần cứng:
    python -m cl0.run_g0 --sim --config configs/cl0.toml --arrangements arr.csv --cell novel_C2 --out /tmp/g0_sim --only 1-5

Mỗi lượt ghi vào <out>: trial_NNNN.json (sự kiện, pha, chẩn đoán), trial_NNNN_log.csv (nhật ký điều khiển), trial_NNNN.mp4 (video gốc),
và một dòng vào g0_trials.csv. Chạy lại cùng lệnh sẽ TIẾP TỤC (bỏ qua sắp xếp đã có lượt hợp lệ ở ô đó).
Quy tắc §4.3: chỉ lỗi phần cứng/ngắt khẩn cấp/mất giao tiếp mới là lượt KHÔNG hợp lệ (nhập 'i'); lượt đó được chạy lại.
Nếu một lượt bị CẮT giữa chừng bởi lỗi (mất camera/băng, lệnh nhảy bị chặn...), chương trình hỏi phân loại (i/f/q) và ghi dòng CSV
tương ứng (outcome = aborted:<loại lỗi>) cùng trial_NNNN.json có traceback; mất liên lạc thiết bị mặc định gợi ý 'i'.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import queue
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .arrangements import Arrangement, read_arrangements
from .config import Config, load_config
from .placement import draw_placement, placement_text
from .types import LinkLost

CAUSES = ["merge", "seg_miss", "grasp_point", "timing", "calib", "slip", "collision", "other"]
CSV_COLUMNS = ["trial_id", "method", "cell", "arrangement_id", "success", "valid", "fail_cause", "note", "outcome", "picked_hint",
               "speed_mm_s", "t_end_s", "session", "config_sha", "code_sha", "operator", "time_iso", "video"]


def suggest_cause(outcome: str, grasp_reason: str = "") -> str:
    """Gợi ý nguyên nhân thất bại từ kết quả bộ điều khiển (người thử xem video rồi quyết định)."""
    m = {"no_target": "seg_miss", "late": "timing", "timeout": "timing", "hard_timeout": "timing", "ik_fail": "other",
         "empty_grasp": "grasp_point", "dropped_in_hold": "slip"}
    if grasp_reason in ("collision",):
        return "collision"
    if grasp_reason in ("miss",):
        return "timing"
    return m.get(outcome, "other")


# ----------------------------------------------------------------------------------------------------------- video
class VideoRecorder:
    def __init__(self, path: str, fps: float, size):
        import cv2
        self.q: queue.Queue = queue.Queue(maxsize=120)
        self.w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), max(fps, 1.0), size)
        self.size, self.dropped = size, 0
        self._th = threading.Thread(target=self._run, daemon=True)
        self._th.start()

    def write(self, img: np.ndarray) -> None:
        try:
            self.q.put_nowait(img)
        except queue.Full:
            self.dropped += 1

    def _run(self) -> None:
        while True:
            img = self.q.get()
            if img is None:
                break
            if (img.shape[1], img.shape[0]) != tuple(self.size):
                import cv2
                img = cv2.resize(img, self.size)
            self.w.write(img)

    def close(self) -> None:
        self.q.put(None)
        self._th.join(timeout=5.0)
        self.w.release()


# ----------------------------------------------------------------------------------------------------------- dữ liệu
@dataclass
class TrialData:
    outcome: str
    t_end: float
    phases: list
    events: list
    log: List[dict]
    diag: dict
    finished: bool
    picked_hint: str = ""
    truth_success: Optional[bool] = None         # chỉ có trong mô phỏng
    grasp_reason: str = ""
    video: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class Judgement:
    success: int
    valid: int
    fail_cause: str = ""
    note: str = ""


# ----------------------------------------------------------------------------------------------------------- người thử
class ConsoleOperator:
    def __init__(self, input_fn=input, print_fn=print):
        self.inp, self.out = input_fn, print_fn

    def before_trial(self, arr: Arrangement, text: str, img_path: str) -> str:
        self.out("\n" + "=" * 100 + "\n" + text)
        if img_path:
            self.out(f"(ảnh tờ đặt vật: {img_path})")
        self.out("Đặt vật lên băng ĐANG DỪNG đúng vị trí. Tay rời vùng robot. Một tay đặt gần công tắc nguồn/ngắt khẩn cấp.")
        r = self.inp("[Enter] chạy   [s] bỏ qua sắp xếp này   [q] thoát > ").strip().lower()
        return {"": "run", "s": "skip", "q": "quit"}.get(r, "run" if r == "" else "skip")

    def judge(self, td: TrialData) -> Judgement:
        auto = int(td.outcome == "picked_hold_complete")
        self.out(f"\nKết quả bộ điều khiển: {td.outcome}  (vật nhặt: {td.picked_hint or '-'})  gợi ý success={auto}")
        while True:
            r = self.inp("success? [Enter]=theo gợi ý  1=thành công  0=thất bại  i=KHÔNG hợp lệ (lỗi phần cứng/ngắt khẩn cấp) > ").strip().lower()
            if r in ("", "1", "0", "i"):
                break
        if r == "i":
            note = self.inp("lý do không hợp lệ (bắt buộc) > ").strip()
            return Judgement(0, 0, "", note or "không hợp lệ")
        succ = auto if r == "" else int(r)
        cause = ""
        if not succ:
            sug = suggest_cause(td.outcome, td.grasp_reason)
            while True:
                c = self.inp(f"nguyên nhân thất bại {CAUSES} [Enter={sug}] > ").strip().lower()
                if c == "":
                    c = sug
                if c in CAUSES:
                    cause = c
                    break
        note = self.inp("ghi chú (có thể để trống) > ").strip()
        if r != "" and succ != auto:
            note = (note + " | " if note else "") + f"người thử đổi success {auto}->{succ}"
        return Judgement(succ, 1, cause, note)


    def after_fault(self, msg: str, link_lost: bool) -> str:
        """Lượt bị cắt giữa chừng bởi một lỗi (camera/băng/servo/an toàn). Trả "invalid" | "fail" | "quit".
        Mất liên lạc thiết bị mặc định là KHÔNG hợp lệ (§4.3); lỗi khác (vd. lệnh nhảy bị chặn = nghi lỗi phần mềm/IK) phải do người thử chọn,
        vì gọi nhầm là "không hợp lệ" sẽ che thất bại thật của CL-0."""
        self.out("Phân loại lượt bị cắt:\n"
                 "  i = KHÔNG hợp lệ (lỗi phần cứng / mất giao tiếp / ngắt khẩn cấp; lượt PHẢI chạy lại)\n"
                 "  f = THẤT BẠI hợp lệ (lỗi của hệ thống hoặc phần mềm; tính là thất bại, nguyên nhân 'other')\n"
                 "  q = thoát, KHÔNG ghi gì (chạy lại cùng lệnh sẽ thử lại sắp xếp này)")
        default = "i" if link_lost else ""
        while True:
            r = (self.inp(f"i / f / q{' [Enter = i]' if default else ''} > ").strip().lower()) or default
            if r in ("i", "f", "q"):
                return {"i": "invalid", "f": "fail", "q": "quit"}[r]


class AutoOperator:
    """Dùng trong mô phỏng/test: lấy sự thật từ thế giới mô phỏng."""

    def after_fault(self, msg: str, link_lost: bool) -> str:
        return "quit"                                     # trong mô phỏng một lỗi là lỗi của mã: dừng, không "hợp lệ hoá"

    def before_trial(self, arr, text, img_path) -> str:
        return "run"

    def judge(self, td: TrialData) -> Judgement:
        succ = int(bool(td.truth_success))
        return Judgement(succ, 1, "" if succ else suggest_cause(td.outcome, td.grasp_reason), "auto (mô phỏng)")


# ----------------------------------------------------------------------------------------------------------- CSV
def read_csv_rows(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


def append_csv(path: str, row: dict) -> None:
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)


def parse_only(spec: Optional[str]) -> Optional[set]:
    if not spec:
        return None
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(str(i) for i in range(int(a), int(b) + 1))
        elif part:
            out.add(part)
    return out


def write_trial_files(out_dir: str, trial_id: int, td: TrialData, meta: dict) -> None:
    base = os.path.join(out_dir, f"trial_{trial_id:04d}")
    d = dict(meta)
    d.update(outcome=td.outcome, t_end=td.t_end, finished=td.finished, picked_hint=td.picked_hint, diag=td.diag, phases=td.phases,
             events=[dict(t=e.t, name=e.name, data={k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in e.data.items()})
                     for e in td.events], extra=td.extra)
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False, default=str)
    if td.log:
        keys: List[str] = []
        for r in td.log:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(base + "_log.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            flat_keys: List[str] = []
            for k in keys:
                v = next((r[k] for r in td.log if k in r and r[k] is not None), None)
                if isinstance(v, tuple):
                    flat_keys += [f"{k}{i}" for i in range(len(v))]
                else:
                    flat_keys.append(k)
            w.writerow(flat_keys)
            for r in td.log:
                row = []
                for k in keys:
                    v = r.get(k)
                    ref = next((rr[k] for rr in td.log if k in rr and rr[k] is not None), None)
                    if isinstance(ref, tuple):
                        row += list(v) if v is not None else [""] * len(ref)
                    else:
                        row.append("" if v is None else v)
                w.writerow(row)


def write_fault_file(out_dir: str, trial_id: int, exc: BaseException, meta: dict) -> None:
    import traceback
    d = dict(meta)
    d.update(outcome=f"aborted:{type(exc).__name__}", error=str(exc), link_lost=isinstance(exc, LinkLost),
             traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    with open(os.path.join(out_dir, f"trial_{trial_id:04d}.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------------------------------------------- người chạy
class SimTrialRunner:
    def __init__(self, cfg: Config, setup=None, async_perception: bool = False):
        from .sim.harness import SimSetup, build_system
        self.setup = setup or SimSetup()
        self.cfg = cfg
        self.sys = build_system(self.setup, cfg)

    def run(self, arr: Arrangement, speed: float, out_dir: str, trial_id: int, record_video: bool) -> TrialData:
        from .sim.harness import arrangement_to_placed, run_trial
        items = [(it.obj, it.x_mm, it.y_mm, it.yaw_deg) for it in arr.items]
        r = run_trial(self.sys, arrangement_to_placed(self.sys, items), v_mm_s=speed)
        return TrialData(r.outcome, r.t_end, r.phases, r.events, r.log, r.diag, True, r.picked, r.success, r.grasp,
                         extra=dict(off_mm=r.off_mm))

    def close(self) -> None:
        pass


class HardwareTrialRunner:
    def __init__(self, cfg: Config, args):
        from .hw.arm import LeRobotArm, go_to
        from .hw.belt import Belt
        from .hw.camera import CameraThread, Undistorter
        from .hw.platform import HardwarePlatform
        from .system import build_stack
        self.cfg, self.go_to = cfg, go_to
        cache = os.path.join(os.path.expanduser("~"), ".cache", "cl0")
        self.stack = build_stack(cfg, async_perception=True, cache_dir=cache)
        und = None
        und_path = os.path.join(os.path.dirname(os.path.abspath(cfg.calib_path)), "intrinsics.npz")
        if os.path.exists(und_path):
            und = Undistorter(und_path, (cfg.camera.width, cfg.camera.height))
        self.camera = CameraThread(cfg.camera, undistort=und)
        lo, hi = self.stack.kin.limits_deg
        limits = np.stack([lo + cfg.robot.joint_margin_deg, hi - cfg.robot.joint_margin_deg], axis=1)
        if args.arm_adapter:
            import importlib
            mod, cls = args.arm_adapter.split(":")
            self.arm = getattr(importlib.import_module(mod), cls)(cfg.robot)
        else:
            self.arm = LeRobotArm(cfg.robot, limits_deg=limits, max_jump_deg=45.0)
        self.belt = Belt(cfg.belt)
        self.platform = HardwarePlatform(cfg, self.camera, self.arm, self.belt)
        self.home = np.asarray(cfg.robot.home_q_deg, float)

    def start(self) -> None:
        self.arm.connect()
        self.camera.start()
        self.belt.open()
        self.go_home(3.0)

    def go_home(self, T: float) -> None:
        self.go_to(self.arm, time.monotonic, self.home, self.cfg.robot.gripper_open, T)

    def run(self, arr: Arrangement, speed: float, out_dir: str, trial_id: int, record_video: bool) -> TrialData:
        from .runner import run_controller
        cfg = self.cfg
        self.go_home(2.0)
        rec = None
        vpath = ""
        fr0 = self.camera.latest()
        if record_video and fr0 is not None:
            vpath = os.path.join(out_dir, f"trial_{trial_id:04d}.mp4")
            h, w = fr0.img.shape[:2]
            rec = VideoRecorder(vpath, self.camera.fps_measured() or cfg.camera.fps, (w, h))

        def on_tick(t, frame, state, cmd):
            if rec is not None and frame is not None:
                rec.write(frame.img)

        self.platform.reset_run()
        self.platform.start_belt(speed)
        err = None
        try:
            rr = run_controller(self.stack.ctrl, self.platform, t_limit_s=cfg.executor.hard_timeout_s + 10.0, on_tick=on_tick)
        except BaseException as e:                         # noqa: BLE001  (gồm KeyboardInterrupt, SafetyError)
            err = e
            rr = None
        finally:
            self.platform.stop_belt()
            if rec is not None:
                rec.close()
        if err is not None:
            self._soft_stop()
            raise err
        picked = ""
        extra = dict(n_ticks=self.platform.n_ticks, n_late=self.platform.n_late, max_late_ms=1e3 * self.platform.max_late_s,
                     cam_fps=self.camera.fps_measured(), cam_jitter_ms=self.camera.jitter_ms(),
                     video_dropped=0 if rec is None else rec.dropped)
        return TrialData(rr.outcome, rr.t_end, rr.phases, rr.events, rr.log, rr.diag, rr.finished, picked, None, "", vpath, extra)

    def _soft_stop(self) -> None:
        """Sau lỗi/ngắt: mở kẹp và về nhà chậm (nếu còn liên lạc được). Vật đang kẹp sẽ rơi."""
        try:
            self.go_home(3.0)
        except Exception as e:                              # noqa: BLE001
            print(f"[soft-stop] không về nhà được: {e}", file=sys.stderr)

    def close(self) -> None:
        for fn in (self.platform.stop_belt, self._soft_stop, self.stack.ctrl.close, self.belt.close, self.camera.stop, self.arm.disconnect):
            try:
                fn()
            except Exception as e:                          # noqa: BLE001
                print(f"[close] {getattr(fn, '__name__', fn)}: {e}", file=sys.stderr)


# ----------------------------------------------------------------------------------------------------------- chính
def run_session(cfg: Config, args, runner, operator, out_dir: str, arrangements: Dict[str, Arrangement], diam: Dict[str, float],
                code_sha: str, config_sha: str, say=print) -> List[dict]:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = args.csv or os.path.join(out_dir, "g0_trials.csv")
    rows = read_csv_rows(csv_path)
    next_id = 1 + max([int(r["trial_id"]) for r in rows if (r.get("trial_id") or "").isdigit()] + [0])
    done = {r["arrangement_id"] for r in rows if r.get("method") == args.method and r.get("cell") == args.cell and r.get("valid") == "1"}
    only = parse_only(args.only)
    speed = args.speed if args.speed is not None else cfg.belt.speed_mm_s
    session = os.path.basename(os.path.abspath(out_dir))
    out_rows = []
    cal_files = _calibration_hashes(cfg)             # hiệu chuẩn đổi theo buổi và KHÔNG nằm trong băm đóng băng: ghi vào từng lượt để truy vết
    for aid in sorted(arrangements, key=lambda x: (len(x), x)):
        if only is not None and aid not in only:
            continue
        if aid in done:
            say(f"sắp xếp #{aid}: đã có lượt hợp lệ ở ô {args.cell} -> bỏ qua (xoá dòng trong CSV nếu muốn chạy lại)")
            continue
        arr = arrangements[aid]
        img_path = os.path.join(out_dir, f"placement_{aid}.png")
        draw_placement(arr, cfg.belt.width_mm, diam, path=img_path)
        act = operator.before_trial(arr, placement_text(arr), img_path)
        if act == "quit":
            break
        if act == "skip":
            continue
        tid = next_id
        t_wall = time.time()
        try:
            td = runner.run(arr, speed, out_dir, tid, not args.no_video)
        except KeyboardInterrupt:
            say("\nNgắt bởi người dùng (Ctrl-C): đã dừng băng, mở kẹp, về nhà. Lượt này CHƯA ghi.")
            break
        except Exception as e:                              # noqa: BLE001  lỗi phần cứng / giao tiếp / an toàn giữa lượt
            if not hasattr(operator, "after_fault"):
                raise                                       # người thử không biết phân loại: không nuốt lỗi
            msg = f"{type(e).__name__}: {e}"
            say(f"\nLƯỢT BỊ CẮT bởi lỗi: {msg}\n(runner đã cố dừng băng, mở kẹp, về nhà; kiểm tra bằng mắt.)")
            choice = operator.after_fault(msg, isinstance(e, LinkLost))
            if choice == "quit":
                say("Thoát; lượt này CHƯA ghi. Chạy lại cùng lệnh sẽ thử lại sắp xếp này.")
                break
            valid = 0 if choice == "invalid" else 1
            meta = dict(trial_id=tid, arrangement_id=aid, cell=args.cell, method=args.method, speed_mm_s=speed, session=session,
                        config_sha=config_sha, code_sha=code_sha, wall_s=time.time() - t_wall, **cal_files)
            vname = f"trial_{tid:04d}.mp4"
            row = dict(trial_id=tid, method=args.method, cell=args.cell, arrangement_id=aid, success=0, valid=valid,
                       fail_cause="" if valid == 0 else "other", note=f"lượt bị cắt: {msg}"[:400], outcome=f"aborted:{type(e).__name__}",
                       picked_hint="", speed_mm_s=speed, t_end_s=round(time.time() - t_wall, 2), session=session, config_sha=config_sha[:12],
                       code_sha=code_sha[:12], operator=args.operator, time_iso=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                       video=vname if os.path.exists(os.path.join(out_dir, vname)) else "")
            write_fault_file(out_dir, tid, e, meta)
            append_csv(csv_path, row)
            out_rows.append(row)
            next_id += 1
            say(f"-> ghi lượt {tid} (success=0, valid={valid}; {'sẽ phải chạy lại' if valid == 0 else 'tính là thất bại, nguyên nhân other'}).")
            _warn_invalid_rate(csv_path, args, say)
            continue
        jd = operator.judge(td)
        meta = dict(trial_id=tid, arrangement_id=aid, cell=args.cell, method=args.method, speed_mm_s=speed, session=session,
                    config_sha=config_sha, code_sha=code_sha, wall_s=time.time() - t_wall, **cal_files)
        write_trial_files(out_dir, tid, td, meta)
        row = dict(trial_id=tid, method=args.method, cell=args.cell, arrangement_id=aid, success=jd.success, valid=jd.valid,
                   fail_cause=jd.fail_cause, note=jd.note, outcome=td.outcome, picked_hint=td.picked_hint, speed_mm_s=speed,
                   t_end_s=round(td.t_end, 2), session=session, config_sha=config_sha[:12], code_sha=code_sha[:12],
                   operator=args.operator, time_iso=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                   video=os.path.basename(td.video))
        append_csv(csv_path, row)
        out_rows.append(row)
        next_id += 1
        cell_rows = [r for r in read_csv_rows(csv_path) if r["method"] == args.method and r["cell"] == args.cell and r["valid"] == "1"]
        say(f"-> ghi lượt {tid} (success={jd.success}, valid={jd.valid}). Ô {args.cell}: {sum(int(r['success']) for r in cell_rows)}/{len(cell_rows)} hợp lệ.")
        if not jd.valid:
            _warn_invalid_rate(csv_path, args, say)
    return out_rows


def _calibration_hashes(cfg: Config) -> dict:
    from .system import file_sha256
    out = {}
    for key, path in (("calib_sha256", cfg.calib_path), ("background_sha256", cfg.background_path)):
        try:
            out[key] = file_sha256(path)
        except OSError:
            out[key] = None
    return out


def _warn_invalid_rate(csv_path: str, args, say=print) -> None:
    """§4.3: tỉ lệ lượt không hợp lệ > 10% thì dừng và sửa (quy tắc ghi trước để không loại bớt thất bại một cách có chọn lọc)."""
    rows = [r for r in read_csv_rows(csv_path) if r.get("method") == args.method and r.get("cell") == args.cell]
    n_bad = sum(1 for r in rows if r.get("valid") == "0")
    say(f"   Lượt không hợp lệ ở ô {args.cell}: {n_bad}/{len(rows)}.")
    if len(rows) >= 5 and n_bad / len(rows) > 0.10:
        say("   CẢNH BÁO §4.3: > 10% lượt không hợp lệ -> DỪNG và sửa nguyên nhân phần cứng trước khi chạy tiếp.")


def load_diameters(path: Optional[str]) -> Dict[str, float]:
    rows = read_csv_rows(path) if path else []
    return {r["name"]: float(r["diameter_mm"]) for r in rows if r.get("name")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--arrangements", required=True)
    ap.add_argument("--cell", required=True, help="seen_C0 | novel_C0 | novel_C2 | novel_C3 | dev_...")
    ap.add_argument("--out", default="runs/g0")
    ap.add_argument("--method", default="CL0")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--objects", default=None, help="objects.csv (để vẽ đúng cỡ vật trên tờ đặt)")
    ap.add_argument("--speed", type=float, default=None, help="mm/s; mặc định belt.speed_mm_s; 0 = thử tĩnh")
    ap.add_argument("--only", default=None, help="ví dụ 1-5,9")
    ap.add_argument("--operator", default="")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--require-frozen", action="store_true", help="từ chối chạy nếu mã/cấu hình khác bản đã đóng băng")
    ap.add_argument("--frozen", default=None)
    ap.add_argument("--arm-adapter", default=None, help="mô_đun:Lớp thay LeRobotArm")
    ap.add_argument("--sim", action="store_true", help="mô phỏng tự động, không cần phần cứng")
    ap.add_argument("--sim-phi", type=float, default=90.0)
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    from .system import code_sha256, file_sha256
    csha, ksha = file_sha256(a.config), code_sha256()
    if a.require_frozen:
        from .freeze import check_frozen
        ok, msg = check_frozen(a.config, a.frozen)
        print(f"[đóng băng] {msg}")
        if not ok:
            return 2
    arrs = read_arrangements(a.arrangements)
    diam = load_diameters(a.objects)
    if a.sim:
        from .sim.harness import SimSetup, belt_center_for
        runner = SimTrialRunner(cfg, SimSetup(phi_deg=a.sim_phi, belt_center_w=belt_center_for(a.sim_phi)))
        operator = AutoOperator()
    else:
        runner = HardwareTrialRunner(cfg, a)
        operator = ConsoleOperator()
        print("Kiểm tra trước khi chạy: (1) vùng robot trống; (2) băng ở đúng tốc độ an toàn đã thử; (3) đã chạy `calibrate fk` và "
              "lượt thử tĩnh (--speed 0) thành công; (4) tay gần công tắc nguồn; (5) robot.home_q_deg đúng là tư thế an toàn của bạn "
              "(ngay sau khi kết nối, tay TỰ ĐI tới đó trong ≥ 3 s).")
        if input("Nhập 'chay' để kết nối robot/camera/băng > ").strip().lower() != "chay":
            return 1
        runner.start()
    try:
        run_session(cfg, a, runner, operator, a.out, arrs, diam, ksha, csha)
    finally:
        runner.close()
    print(f"Xong. Phân tích: python3 dir1/g0_analyze.py cells {a.csv or os.path.join(a.out, 'g0_trials.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
