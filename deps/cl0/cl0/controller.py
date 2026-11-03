"""Bộ điều khiển CL-0: nhận thức -> theo dõi trong hệ băng -> chọn vật -> thực thi bám băng -> hạ, khép, nhấc, giữ.

Bộ thực thi là dạng I2 của §3.2 áp cho trường hợp mục tiêu cố định trong hệ băng p_b:
    p_w,lệnh(t_x) = p_b,mục tiêu + s(t_x)·u_hat           (đúng p_w,EE(t_img) + a + (s(t_x) − s(t_img))·u_hat khi a = p_b,mục tiêu − p_b,EE(t_img))
Độ dịch của băng trong khoảng trễ do bộ thực thi gánh (đọc s(t_x) tại lúc thực thi); thêm ``lead_s`` để bù độ trễ của chính cánh tay.
Chuyển động của TCP là bộ lọc tới hạn bậc hai TRONG HỆ BĂNG (có chặn tốc độ), nên cập nhật mục tiêu liên tục mà không giật.

Máy trạng thái: WAIT -> APPROACH -> DESCEND -> CLOSE -> LIFT -> MOVE_HOLD -> HOLD -> RELEASE -> RETURN -> DONE.
Điều kiện chuyển pha dùng cả lệnh lẫn **vị trí đo được** (FK của khớp đọc về), nên cánh tay tụt lại thì không hạ sớm.
Bộ điều khiển không biết gì về phần cứng: chỉ nhận Frame, BeltLike, RobotState và trả Command (xem types.py).
"""
from __future__ import annotations

import math
import threading
from typing import Dict, List, Optional, Tuple

import numpy as np

from .config import Config
from .executor import BeltExecutor
from .geometry import perp, unit, wrap_axis_diff
from .kinematics import SO101Kinematics
from .perception import Detector
from .reach import TopDownReach
from .tracker import Tracker
from .types import BeltLike, Command, Frame, RobotState, TrialEvent

PHASES = ("WAIT", "APPROACH", "DESCEND", "CLOSE", "LIFT", "MOVE_HOLD", "HOLD", "RELEASE", "RETURN", "DONE")


def _minjerk(tau: float) -> float:
    tau = min(max(tau, 0.0), 1.0)
    return 10 * tau ** 3 - 15 * tau ** 4 + 6 * tau ** 5


class _AsyncDetector:
    """Chạy ``Detector.detect`` ở luồng riêng (OpenCV/numpy nhả GIL phần lớn thời gian) để vòng điều khiển 50 Hz không bị khựng.
    Chỉ giữ MỘT việc đang chờ (khung mới thay khung cũ chưa xử lý) và MỘT kết quả mới nhất."""

    def __init__(self, det: Detector):
        self.det = det
        self._cv = threading.Condition()
        self._job = None
        self._res = None
        self._stop = False
        self._th = threading.Thread(target=self._run, name="cl0-detect", daemon=True)
        self._th.start()

    def submit(self, img, s_img, t_capture, exclude) -> None:
        with self._cv:
            self._job = (img, s_img, t_capture, exclude)
            self._cv.notify()

    def poll(self):
        with self._cv:
            r, self._res = self._res, None
            return r

    def clear(self) -> None:
        with self._cv:
            self._job = None
            self._res = None

    def close(self) -> None:
        with self._cv:
            self._stop = True
            self._cv.notify()
        self._th.join(timeout=2.0)

    def _run(self) -> None:
        while True:
            with self._cv:
                while self._job is None and not self._stop:
                    self._cv.wait()
                if self._stop:
                    return
                job, self._job = self._job, None
            img, s_img, t_capture, exclude = job
            try:
                res = self.det.detect(img, s_img, exclude)
            except Exception as e:                      # không để luồng chết im lặng
                res = e
            with self._cv:
                self._res = (res, s_img, t_capture)


class CL0Controller:
    def __init__(self, cfg: Config, kin: SO101Kinematics, detector: Detector, reach: TopDownReach, phi_deg: float, z_belt_mm: float,
                 async_perception: bool = False):
        self.cfg, self.kin, self.det, self.reach = cfg, kin, detector, reach
        self._async = _AsyncDetector(detector) if async_perception else None
        self.phi, self.zb = phi_deg, z_belt_mm
        self.u, self.v = unit(phi_deg), perp(phi_deg)
        self.home_q = np.asarray(cfg.robot.home_q_deg, float)
        self.hold_q = np.asarray(cfg.robot.hold_q_deg, float)
        self.exe = BeltExecutor(cfg, kin, phi_deg, z_belt_mm)
        self.reset(0.0, None)

    # --------------------------------------------------------------------------- vòng đời
    def reset(self, t0: float, state: Optional[RobotState]) -> None:
        self.phase = "WAIT"
        self.t_start = t0
        self._t_prev = t0
        self.t_phase = t0
        self.tracker = Tracker(self.cfg.track)
        self.last_dets = []
        if self._async is not None:
            self._async.clear()
        self.target_tid: Optional[int] = None
        self.target_est: Optional[Tuple[float, float, float]] = None     # (a_b, b, theta) hệ băng
        self.frozen = False
        self.exe.reset(state.q_deg if state is not None else self.home_q)
        self.events: List[TrialEvent] = []
        self.log: List[dict] = []
        self.outcome = ""
        self._lost_n = 0
        self.lost = False
        self.diag: Dict[str, int] = {"frames": 0, "reject_wide": 0, "reject_other": 0, "n_ok_dets": 0}
        self._settle = 0.0
        self._q_move0 = None
        self._grasp_dt = 0.0
        self.s_at_select = None

    @property
    def finished(self) -> bool:
        return self.phase == "DONE"

    def close(self) -> None:
        if self._async is not None:
            self._async.close()
            self._async = None

    def _event(self, t, name, **data):
        self.events.append(TrialEvent(t, name, data))

    def _goto(self, t, phase):
        self._event(t, "phase:" + phase)
        self.phase, self.t_phase = phase, t

    # --------------------------------------------------------------------------- tiện ích
    def _tcp(self, state: RobotState):
        p, a, c, pitch, yaw = self.kin.tool_axes(state.q_deg)
        return dict(x=float(p[0]), y=float(p[1]), z=float(p[2]), a=float(p @ np.r_[self.u, 0.0]), b=float(p @ np.r_[self.v, 0.0]),
                    theta=float(yaw - self.phi))

    def _zs(self):
        ex = self.cfg.executor
        zg = self.zb + ex.z_grasp_above_belt_mm
        return zg, zg + ex.pre_height_mm, self.zb + ex.lift_height_mm

    # --------------------------------------------------------------------------- nhận thức
    def _perceive(self, t, frame: Optional[Frame], belt: BeltLike, tcp: dict) -> None:
        exclude = [(tcp["a"], tcp["b"], self.cfg.executor.arm_exclusion_mm)] if self.phase != "WAIT" else []
        if frame is not None:
            s_img = belt.s_at(frame.t_capture)
            if self._async is not None:
                self._async.submit(frame.img, s_img, frame.t_capture, exclude)
            else:
                self._ingest(t, self.det.detect(frame.img, s_img, exclude), s_img, frame.t_capture)
        if self._async is not None:
            r = self._async.poll()
            if r is not None:
                res, s_img, t_cap = r
                if isinstance(res, Exception):
                    raise RuntimeError("luồng nhận thức báo lỗi") from res
                self._ingest(t, res, s_img, t_cap)

    def _ingest(self, t, res, s_img: float, t_capture: float) -> None:
        self.diag["frames"] += 1
        for d in res.dets:
            if d.ok:
                self.diag["n_ok_dets"] += 1
            elif d.reject == "wide":
                self.diag["reject_wide"] += 1
            else:
                self.diag["reject_other"] += 1
        if self.frozen:
            return
        self.last_dets = res.dets
        self.tracker.update(res.dets, s_img, t_capture)
        self.tracker.prune(t, keep=self.target_tid)
        if self.target_tid is not None:
            tr = self.tracker.get(self.target_tid)
            if tr is not None and tr.obs:
                a, b, th, w, std = tr.estimate()
                self.target_est = (a, b, th)

    def _pick_a_grasp(self, a_b: float, b: float, s_now: float, sdot: float) -> Optional[float]:
        """Vị trí a (W-căn-theo-băng) dự kiến lúc kẹp nếu vật (đứng yên trong hệ băng) còn nằm trong vùng với tới VÀ cửa sổ nhặt suốt
        đoạn từ BÂY GIỜ tới hết lúc nhấc; không thì None.

        Phải kiểm cả 'bây giờ' (ở độ cao chờ): bộ thực thi bám vị trí HIỆN TẠI của vật rồi mới trượt theo băng, nên chọn một vật còn ở
        ngoài vùng với tới (chỉ vào vùng ở lúc kẹp) làm lệnh IK rơi ngoài vùng trong lúc tay đuổi theo -> ``ik_fail`` (mô phỏng φ=0 bắt
        được lỗi này). Lệnh thực tế dẫn trước ``lead_s`` nên kiểm cả vị trí dẫn trước. Cửa sổ nhặt a_pick_* chỉ áp cho lúc kẹp/nhấc."""
        ex = self.cfg.executor
        zg, zp, zl = self._zs()
        tg, tl = ex.t_to_grasp_s, ex.t_to_grasp_s + ex.follow_margin_s
        for ahead, zs, windowed in ((0.0, (zp,), False), (0.5 * tg, (zp,), False), (tg, (zg, zp), True), (tl, (zg, zl), True)):
            a_obj = a_b + s_now + sdot * ahead
            if windowed and not (ex.a_pick_min <= a_obj <= ex.a_pick_max):
                return None
            for a in (a_obj, a_obj + sdot * ex.lead_s):
                xy = a * self.u + b * self.v
                if not all(self.reach.contains(float(xy[0]), float(xy[1]), z, inner_mm=5.0) for z in zs):
                    return None
        return a_b + s_now + sdot * tg

    def _select(self, t, s_now, sdot) -> bool:
        best, best_a = None, -1e18
        for tr in self.tracker.confirmed():
            a_b, b, th, w, std = tr.estimate()
            a_g = self._pick_a_grasp(a_b, b, s_now, sdot)
            if a_g is not None and a_g > best_a:
                best, best_a = tr, a_g
        if best is None:
            return False
        self.target_tid = best.tid
        a, b, th, w, std = best.estimate()
        self.target_est = (a, b, th)
        self._event(t, "select", tid=best.tid, a_b=a, b=b, theta=th, width=w, std=std)
        return True

    def _lift_feasible(self, s_now: float, sdot: float, ahead_s: float) -> bool:
        """Vật (đứng yên trong hệ băng) còn nằm trong vùng với tới ở độ cao nhấc sau ``ahead_s`` giây không?"""
        zg, zp, zl = self._zs()
        tgt, _ = self._target()
        for dt_ahead, z in ((0.0, zg), (ahead_s, zl)):
            a = tgt[0] + s_now + sdot * dt_ahead
            xy = a * self.u + tgt[1] * self.v
            if not self.reach.contains(float(xy[0]), float(xy[1]), z, inner_mm=3.0):
                return False
        return True

    # --------------------------------------------------------------------------- bước điều khiển
    def step(self, t: float, frame: Optional[Frame], belt: BeltLike, state: RobotState) -> Command:
        dt = min(max(t - self._t_prev, 1e-3), 0.1)
        self._t_prev = t
        ex, rb = self.cfg.executor, self.cfg.robot
        s_now, sdot = belt.s_at(t), belt.speed_at(t)
        tcp = self._tcp(state)
        if self.phase in ("WAIT", "APPROACH"):
            self._perceive(t, frame, belt, tcp)

        # chốt cứng cho cả lượt
        if self.phase not in ("RELEASE", "RETURN", "DONE") and (t - self.t_start) > ex.hard_timeout_s:
            self.outcome = self.outcome or "hard_timeout"
            self._event(t, "abort", reason="hard_timeout")
            self._goto(t, "RELEASE")
        # hết giờ: chỉ huỷ trước khi nhấc
        if self.phase in ("WAIT", "APPROACH", "DESCEND", "CLOSE") and (t - self.t_start) > ex.trial_timeout_s:
            self.outcome = self.outcome or ("no_target" if self.target_tid is None else "timeout")
            self._event(t, "abort", reason=self.outcome)
            self._goto(t, "RELEASE")
        if self.phase in ("APPROACH", "DESCEND", "CLOSE") and self.exe.ik_fail_t > ex.ik_fail_abort_s:
            self.outcome = "ik_fail"
            self._event(t, "abort", reason="ik_fail")
            self._goto(t, "RELEASE")

        if self.phase in ("LIFT", "MOVE_HOLD", "HOLD") and not self.lost:
            held_now = state.gripper > rb.gripper_closed + rb.gripper_held_margin
            self._lost_n = 0 if held_now else self._lost_n + 1
            if self._lost_n >= 3:
                self.lost = True
                self._event(t, "lost_object", gripper=state.gripper, phase=self.phase)
        cmd = getattr(self, "_do_" + self.phase.lower())(t, dt, s_now, sdot, state, tcp)
        self._record(t, s_now, state, tcp, cmd)
        return cmd

    def _record(self, t, s_now, state, tcp, cmd):
        row = dict(t=t, phase=self.phase, s=s_now, tcp_a_b=tcp["a"] - s_now, tcp_b=tcp["b"], tcp_z=tcp["z"], tcp_th=tcp["theta"],
                   grip=state.gripper, q=tuple(float(x) for x in state.q_deg),
                   qc=None if cmd.q_deg is None else tuple(float(x) for x in cmd.q_deg), gc=cmd.gripper)
        if self.target_est is not None:
            row.update(tgt_a_b=self.target_est[0], tgt_b=self.target_est[1], tgt_th=self.target_est[2])
        if self.exe.started:
            row.update(cmd_a_b=float(self.exe.fxy.x[0] + self.exe.int_xy[0]), cmd_b=float(self.exe.fxy.x[1] + self.exe.int_xy[1]),
                       cmd_z=float(self.exe.fz.x + self.exe.int_z), cmd_th=float(self.exe.fth.x),
                       int_a=float(self.exe.int_xy[0]), int_b=float(self.exe.int_xy[1]), int_z=float(self.exe.int_z))
        self.log.append(row)

    # --------------------------------------------------------------------------- các pha
    def _do_wait(self, t, dt, s_now, sdot, state, tcp) -> Command:
        if self.tracker.confirmed() and self._select(t, s_now, sdot):
            self.exe.start(tcp, s_now, sdot)
            self._settle = 0.0
            self._goto(t, "APPROACH")
            return self._do_approach(t, dt, s_now, sdot, state, tcp)
        return Command(None, self.cfg.robot.gripper_open, "WAIT")

    def _target(self):
        a, b, th = self.target_est
        return np.array([a, b]), th

    def _track(self, t, dt, s_now, sdot, state, tcp, ref_z: float, hold_z_if_far: bool = False) -> Tuple[np.ndarray, float, float]:
        tgt, th = self._target()
        return self.exe.step(t, dt, s_now, sdot, tcp, tgt, th, ref_z, hold_z_if_far=hold_z_if_far)

    def _maybe_freeze(self, t, err_meas):
        if not self.frozen and err_meas < self.cfg.executor.freeze_radius_mm:
            self.frozen = True
            self._event(t, "freeze", est=self.target_est)

    def _do_approach(self, t, dt, s_now, sdot, state, tcp) -> Command:
        ex = self.cfg.executor
        zg, zp, zl = self._zs()
        q, err_meas, th_ref = self._track(t, dt, s_now, sdot, state, tcp, zp)
        self._maybe_freeze(t, err_meas)
        tgt, _ = self._target()
        fe = self.exe
        ok_f = (np.linalg.norm(fe.fxy.x - tgt) < ex.tol_xy_mm and abs(fe.fth.x - th_ref) < ex.tol_yaw_deg
                and abs(fe.fz.x - zp) < ex.tol_z_mm)
        ok_m = (err_meas < ex.tol_meas_xy_mm and abs(tcp["z"] - zp) < ex.tol_z_mm + 3.0
                and abs(wrap_axis_diff(tcp["theta"] - th_ref)) < ex.tol_yaw_deg + 3.0)
        self._settle = self._settle + dt if (ok_f and ok_m) else 0.0
        if self._settle >= ex.settle_s:
            self.frozen = True
            if not self._lift_feasible(s_now, sdot, ex.t_after_settle_s):
                self.outcome = "late"
                self._event(t, "abort", reason="late: vật sắp ra khỏi vùng với tới trước khi nhấc xong")
                self._goto(t, "RELEASE")
            else:
                self._goto(t, "DESCEND")
        return Command(q, self.cfg.robot.gripper_open, "APPROACH")

    def _do_descend(self, t, dt, s_now, sdot, state, tcp) -> Command:
        ex = self.cfg.executor
        zg, zp, zl = self._zs()
        q, err_meas, _ = self._track(t, dt, s_now, sdot, state, tcp, zg, hold_z_if_far=True)
        if tcp["z"] <= zg + ex.tol_z_mm and err_meas < 1.5 * ex.tol_meas_xy_mm:
            self._goto(t, "CLOSE")
        return Command(q, self.cfg.robot.gripper_open, "DESCEND")

    def _do_close(self, t, dt, s_now, sdot, state, tcp) -> Command:
        ex, rb = self.cfg.executor, self.cfg.robot
        zg, zp, zl = self._zs()
        q, err_meas, _ = self._track(t, dt, s_now, sdot, state, tcp, zg)
        if t - self.t_phase >= ex.close_wait_s:
            held = state.gripper > rb.gripper_closed + rb.gripper_held_margin
            self._event(t, "close_done", gripper=state.gripper, held=held, err_meas=err_meas)
            if held:
                self._goto(t, "LIFT")
            else:
                self.outcome = "empty_grasp"
                self._event(t, "abort", reason="empty_grasp")
                self._goto(t, "RELEASE")
        return Command(q, rb.gripper_closed, "CLOSE")

    def _do_lift(self, t, dt, s_now, sdot, state, tcp) -> Command:
        ex, rb = self.cfg.executor, self.cfg.robot
        zg, zp, zl = self._zs()
        q, err_meas, _ = self._track(t, dt, s_now, sdot, state, tcp, zl)
        lifted = tcp["z"] >= zl - 5.0 and (t - self.t_phase) >= ex.lift_wait_s
        stuck = (t - self.t_phase) >= ex.lift_timeout_s or self.exe.ik_fail_t > 0.3
        if lifted or stuck:
            if stuck and not lifted:
                self._event(t, "lift_stuck", z=tcp["z"], ik_fail_t=self.exe.ik_fail_t)
            self._q_move0 = state.q_deg.copy()
            self._goto(t, "MOVE_HOLD")
        return Command(q, rb.gripper_closed, "LIFT")

    def _move_T(self, q0, q1, T_min: float) -> float:
        """Thời gian di chuyển trong không gian khớp: không nhỏ hơn T_min và đỉnh tốc độ (min-jerk: 1.875·Δ/T) <= move_peak_deg_s."""
        d = float(np.max(np.abs(np.asarray(q1, float) - np.asarray(q0, float))))
        return max(T_min, 1.875 * d / self.cfg.executor.move_peak_deg_s)

    def _joint_move(self, t, q0, q1, T) -> np.ndarray:
        q = q0 + (q1 - q0) * _minjerk((t - self.t_phase) / T)
        self.exe.set_q_last(q)
        return q

    def _do_move_hold(self, t, dt, s_now, sdot, state, tcp) -> Command:
        ex, rb = self.cfg.executor, self.cfg.robot
        T = self._move_T(self._q_move0, self.hold_q, ex.move_hold_s)
        q = self._joint_move(t, self._q_move0, self.hold_q, T)
        if t - self.t_phase >= T:
            self._event(t, "hold_start")
            self._goto(t, "HOLD")
        return Command(q, rb.gripper_closed, "MOVE_HOLD")

    def _do_hold(self, t, dt, s_now, sdot, state, tcp) -> Command:
        ex, rb = self.cfg.executor, self.cfg.robot
        if t - self.t_phase >= ex.hold_s:
            self.outcome = self.outcome or ("dropped_in_hold" if self.lost else "picked_hold_complete")
            self._event(t, "hold_done", gripper=state.gripper, lost=self.lost)
            self._goto(t, "RELEASE")
        return Command(self.hold_q.copy(), rb.gripper_closed, "HOLD")

    def _do_release(self, t, dt, s_now, sdot, state, tcp) -> Command:
        rb = self.cfg.robot
        if t - self.t_phase >= 0.6:
            self._q_move0 = state.q_deg.copy()
            self._goto(t, "RETURN")
        return Command(None, rb.gripper_open, "RELEASE")

    def _do_return(self, t, dt, s_now, sdot, state, tcp) -> Command:
        rb = self.cfg.robot
        T = self._move_T(self._q_move0, self.home_q, 1.5)
        q = self._joint_move(t, self._q_move0, self.home_q, T)
        if t - self.t_phase >= T:
            self._goto(t, "DONE")
        return Command(q, rb.gripper_open, "RETURN")

    def _do_done(self, t, dt, s_now, sdot, state, tcp) -> Command:
        return Command(None, None, "DONE")
