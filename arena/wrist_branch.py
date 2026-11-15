"""W1 (paper-dev; KE_HOACH_PAPER.md P2): choose the grasp-yaw branch that keeps the wrist roll inside its limits while the arm follows the belt.

Why (PAPER_NOTES.md P1b, mechanism A).  A parallel gripper makes the same grasp at yaw th and th + 180 deg, and cl0.kinematics.ik matches the closing
axis mod 180 deg.  CL-0's BeltExecutor takes the branch nearest to the yaw filter's current value and its IK warm-starts from the last command, so the
arm keeps the branch it starts on.  For a top-down tool the closing-axis yaw is exactly c_pan*q1 + c_roll*q5 + K (SO-101 URDF: c_pan = -1,
c_roll = +1, K = 177.2 deg; WristModel fits and checks it by FK), so while the arm follows an object along the belt (constant yaw in the belt frame) the
wrist roll turns 1:1 with the pan.  At L0.5 the pan turns up to ~70 deg in one attempt; on the nearest branch the roll can reach its limit (-157.2 deg
+ 3 deg margin): the quick IK then fails, the command is held and steps 3 deg every 0.2 s (full IK + joint rate limit), and the TCP falls 30-50 mm
behind the object.

W1.  At selection, ``plan_branch`` predicts the joints over a tracking window (the object's position from now to ``window_s`` later, at grasp and lift
height) for each branch th + 180 k the yaw filter can turn to (|turn| <= 270 deg), with an IK whose wrist roll is unbounded so the predicted roll can
be compared with the real limits.  CL-0's nearest branch is kept unless its predicted wrist roll comes within ``h_min_deg`` of a limit (beyond
robot.joint_margin_deg) somewhere in the window.  Then the branch whose first violation (any joint out of its margin, wrist roll within ``h_min_deg``,
or no IK) comes latest is taken, if that is later than on CL-0's branch.  ``BranchExecutor`` then tracks that branch: th_ref is the representative nearest the plan, and its IK
is seeded with, and only accepts, solutions on the planned branch, so a large turn of the yaw filter cannot make the warm-started IK fall back to the
other branch.  Attempts W1 leaves on CL-0's branch run CL-0's code unchanged.
"""
from __future__ import annotations

import copy
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from cl0.executor import BeltExecutor
from cl0.geometry import perp, unit


def _wrap180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


class WristModel:
    """Closing-axis yaw of a top-down pose, unwrapped and continuous in the joints: yaw = c_pan*q1 + c_roll*q5 + K (deg).  Fitted and checked by FK."""

    CHECK = (((150.0, -120.0, 30.0), 30.0), ((240.0, 80.0, 50.0), 120.0), ((130.0, 140.0, 20.0), -60.0), ((220.0, -60.0, 70.0), 80.0))

    def __init__(self, kin, tilt_deg: float = 90.0):
        self.kin, self.tilt = kin, tilt_deg
        q_ref = self._topdown((200.0, 0.0, 60.0), 0.0)
        y0 = self.yaw_fk(q_ref)

        def slope(i: int) -> float:
            q = q_ref.copy()
            q[i] += 5.0
            return _wrap180(self.yaw_fk(q) - y0) / 5.0

        self.c_pan, self.c_roll = float(np.sign(slope(0))), float(np.sign(slope(4)))
        self.K = _wrap180(y0 - self.c_pan * q_ref[0] - self.c_roll * q_ref[4])
        self.check_residual_deg = max(abs(_wrap180(self.yaw_fk(q) - self.yaw(q))) for q in (self._topdown(p, y) for p, y in self.CHECK))
        if self.check_residual_deg > 0.5:
            raise RuntimeError(f"WristModel: top-down yaw is not c_pan*q1 + c_roll*q5 + K for this arm (residual {self.check_residual_deg:.2f} deg)")

    def _topdown(self, p, yaw) -> np.ndarray:
        r = self.kin.ik(list(p), yaw, tilt_deg=self.tilt)
        if not r.ok:
            raise RuntimeError(f"WristModel: no top-down IK at {p}, yaw {yaw}")
        return np.asarray(r.q_deg, float)

    def yaw_fk(self, q) -> float:
        _, R = self.kin.fk(q)
        return math.degrees(math.atan2(R[1, 0], R[0, 0]))

    def yaw(self, q) -> float:
        return self.c_pan * float(q[0]) + self.c_roll * float(q[4]) + self.K

    def q5(self, yaw: float, q1: float) -> float:
        return (yaw - self.c_pan * q1 - self.K) / self.c_roll


def free_roll(kin):
    """A copy of the kinematics whose wrist roll is unbounded (planning only: the predicted roll is then compared with the real limits)."""
    k2 = copy.deepcopy(kin)
    k2.lo_rad = k2.lo_rad.copy()
    k2.hi_rad = k2.hi_rad.copy()
    k2.lo_rad[4], k2.hi_rad[4] = -3.0 * math.pi, 3.0 * math.pi
    return k2


@dataclass
class BranchPlan:
    k0: int                                   # CL-0's branch: th_ref = th + 180 k0 (nearest to the current yaw)
    k: int                                    # branch taken
    th_plan: Optional[float]                  # th + 180 k when W1 switched, else None (CL-0's rule runs)
    m0: int                                   # yaw filter - 180 m0 = joint-implied yaw (fixed at the start of the attempt)
    at_risk: bool                             # CL-0's branch: predicted wrist roll within h_min of a limit somewhere in the window
    ttv: Dict[int, float] = field(default_factory=dict)         # time of the first violation per candidate (> window_s: none)
    why: Dict[int, str] = field(default_factory=dict)           # what the first violation is: roll | joint | ik | ""
    h5_min: Dict[int, float] = field(default_factory=dict)      # min predicted wrist-roll headroom beyond the margin (deg)
    q5_span: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    ms: float = 0.0

    @property
    def switched(self) -> bool:
        return self.th_plan is not None

    def event(self) -> dict:
        r = lambda x: round(float(x), 2)
        return dict(k0=self.k0, k=self.k, switched=self.switched, at_risk=self.at_risk, m0=self.m0,
                    th_plan=None if self.th_plan is None else r(self.th_plan),
                    ttv={str(k): r(v) for k, v in self.ttv.items()}, why={str(k): v for k, v in self.why.items()},
                    h5_min={str(k): r(v) for k, v in self.h5_min.items()},
                    q5_span={str(k): [r(a), r(b)] for k, (a, b) in self.q5_span.items()}, ms=r(self.ms))


def plan_branch(kin, kin_free, wm: WristModel, cfg, phi_deg: float, z_belt_mm: float, q_now, th_now_bf: float,
                tgt_a_b: float, tgt_b: float, th_tgt: float, s_now: float, sdot: float,
                window_s: float = 4.0, dt_s: float = 0.2, h_min_deg: float = 10.0, max_turn_deg: float = 270.0,
                t_start_s: float = 0.5, t_descend_s: float = 1.0) -> BranchPlan:
    """Branch plan for one attempt (see the module doc).  ``th_now_bf``: the yaw filter's start value (measured TCP yaw, belt frame); ``th_tgt``: target yaw.
    Object positions from ``t_start_s`` on: the TCP reaches the object about 0.5 s after selection (freeze event at 0.46-0.54 s in
    runs/p1_oracle_train_c2_l05), so earlier positions are never visited.  Heights: pre-grasp height until ``t_descend_s`` (APPROACH; select -> DESCEND
    took 1.12 s median at L0.5 there), then grasp and lift height."""
    t0 = time.perf_counter()
    ex, rb = cfg.executor, cfg.robot
    lo, hi = kin.limits_deg
    lo_m, hi_m = lo + rb.joint_margin_deg, hi - rb.joint_margin_deg
    u, v = unit(phi_deg), perp(phi_deg)
    zg, zp, zl = z_belt_mm + ex.z_grasp_above_belt_mm, z_belt_mm + ex.z_grasp_above_belt_mm + ex.pre_height_mm, z_belt_mm + ex.lift_height_mm
    q_now = np.asarray(q_now, float)[:5]
    yaw_now = wm.yaw(q_now)
    m0 = int(round((phi_deg + th_now_bf - yaw_now) / 180.0))
    k0 = int(round((th_now_bf - th_tgt) / 180.0))
    taus = np.arange(t_start_s, window_s + 1e-9, dt_s)
    pts = [(tgt_a_b + s_now + sdot * float(tau)) * u + tgt_b * v for tau in taus]

    # a top-down solution near the first point (any branch) to seed the joints other than the roll
    r0 = kin.ik([float(pts[0][0]), float(pts[0][1]), zp], phi_deg + th_tgt, tilt_deg=rb.tilt_deg)
    q_seed0 = np.asarray(r0.q_deg, float) if r0.ok else np.array([0.0, 0.0, 45.0, 45.0, 0.0])

    ks = [k for k in range(k0 - 2, k0 + 3) if abs(th_tgt + 180.0 * k - th_now_bf) <= max_turn_deg]
    plan = BranchPlan(k0=k0, k=k0, th_plan=None, m0=m0, at_risk=False)
    for k in ks:
        yaw_j = phi_deg + th_tgt + 180.0 * (k - m0)            # joint-implied yaw the arm turns to on this branch (continuous from q_now)
        # transient: the yaw filter (omega_yaw) reaches its target before the pan has moved much, so check the roll at (target yaw, current pan)
        q5_corners = [wm.q5(yaw_j, q_now[0])]
        ttv, why, h5s, q5s = float("inf"), "", [], []
        for c in q5_corners:
            h = min(c - lo_m[4], hi_m[4] - c)
            h5s.append(h)
            q5s.append(c)
            if h < h_min_deg and ttv == float("inf"):
                ttv, why = 0.0, "roll"
        prev, last = {}, q_seed0
        for tau, xy in zip(taus, pts):
            for z in ((zp,) if tau < t_descend_s else (zg, zl)):
                seed = prev.get(z, last).copy()
                seed[4] = wm.q5(yaw_j, seed[0])
                r = kin_free.ik([float(xy[0]), float(xy[1]), z], yaw_j, q0_deg=seed, tilt_deg=rb.tilt_deg, max_seeds=1, max_iter=40)
                q = np.asarray(r.q_deg, float)
                if not (r.ok and abs(wm.yaw(q) - yaw_j) < 1.0):
                    if ttv == float("inf"):
                        ttv, why = float(tau), "ik"
                    continue
                prev[z] = last = q
                h14 = float(np.min(np.minimum(q[:4] - lo_m[:4], hi_m[:4] - q[:4])))
                h5 = float(min(q[4] - lo_m[4], hi_m[4] - q[4]))
                h5s.append(h5)
                q5s.append(float(q[4]))
                if ttv == float("inf"):
                    if h14 < 0.0:
                        ttv, why = float(tau), "joint"
                    elif h5 < h_min_deg:
                        ttv, why = float(tau), "roll"
        plan.ttv[k] = ttv if ttv != float("inf") else window_s + dt_s
        plan.why[k] = why
        plan.h5_min[k] = min(h5s) if h5s else -90.0
        plan.q5_span[k] = (min(q5s), max(q5s)) if q5s else (float("nan"), float("nan"))

    plan.at_risk = plan.h5_min.get(k0, -90.0) < h_min_deg
    if plan.at_risk:
        best = max(ks, key=lambda k: (plan.ttv[k], plan.h5_min[k]))
        if best != k0 and plan.ttv[best] > plan.ttv[k0]:
            plan.k = best
            plan.th_plan = th_tgt + 180.0 * best
    plan.ms = 1000.0 * (time.perf_counter() - t0)
    return plan


class BranchExecutor(BeltExecutor):
    """cl0.executor.BeltExecutor with W1: when a plan is set (``set_plan``), th_ref is the representative of the target yaw nearest the planned yaw
    (CL-0: nearest the filter's current yaw), and the IK is seeded with, and only accepts, solutions on the planned branch.  Without a plan every call
    goes to CL-0's code.  step() and _ik_cmd() below are CL-0's code (cl0/executor.py, frozen) with only those changes."""

    def __init__(self, cfg, kin, phi_deg: float, z_belt_mm: float, wm: WristModel):
        super().__init__(cfg, kin, phi_deg, z_belt_mm)
        self.wm = wm
        lo, hi = kin.limits_deg
        self._lo5, self._hi5 = float(lo[4]), float(hi[4])
        self.th_plan: Optional[float] = None
        self.m0 = 0

    def reset(self, q_deg=None) -> None:
        super().reset(q_deg)
        self.th_plan, self.m0 = None, 0

    def start(self, tcp: dict, s_now: float, sdot: float) -> None:
        super().start(tcp, s_now, sdot)
        self.th_plan, self.m0 = None, 0

    def set_plan(self, th_plan: Optional[float], m0: int) -> None:
        self.th_plan, self.m0 = th_plan, int(m0)

    def _ik_cmd(self, t: float, dt: float, xy_w, z: float, yaw_w: float) -> np.ndarray:
        if self.th_plan is None:
            return super()._ik_cmd(t, dt, xy_w, z, yaw_w)
        ex, rb = self.cfg.executor, self.cfg.robot
        z = max(z, self.zb + ex.min_z_above_belt_mm)
        tgt = [float(xy_w[0]), float(xy_w[1]), float(z)]
        yaw_j = yaw_w - 180.0 * self.m0                                         # W1: joint-implied yaw of the planned branch
        q0 = self.q_last.copy()
        q0[4] = float(np.clip(self.wm.q5(yaw_j, q0[0]), self._lo5, self._hi5))  # W1: seed the roll on the planned branch

        def good(r) -> bool:                                                    # W1: + on the planned branch
            return bool(r.ok and self.kin.within_margin(r.q_deg, rb.joint_margin_deg) and abs(self.wm.yaw(r.q_deg) - yaw_j) < 1.0)

        r = self.kin.ik(tgt, yaw_w, q0_deg=q0, tilt_deg=rb.tilt_deg, max_seeds=1, max_iter=15)
        ok = good(r)
        if not ok and (t - self._last_full_ik) > 0.2:
            self._last_full_ik = t
            r = self.kin.ik(tgt, yaw_w, q0_deg=q0, tilt_deg=rb.tilt_deg, max_seeds=4, max_iter=25)
            ok = good(r)
        if not ok:
            self.ik_fail_t += dt
            return self.q_last.copy()
        self.ik_fail_t = 0.0
        return self._rate_limit(r.q_deg, dt)

    def step(self, t: float, dt: float, s_now: float, sdot: float, tcp: dict, tgt_bf: np.ndarray, th_deg: float, z_ref: float,
             hold_z_if_far: bool = False) -> Tuple[np.ndarray, float, float]:
        if self.th_plan is None:
            return super().step(t, dt, s_now, sdot, tcp, tgt_bf, th_deg, z_ref, hold_z_if_far=hold_z_if_far)
        ex = self.cfg.executor
        tgt_bf = np.asarray(tgt_bf, float)
        th_ref = th_deg + 180.0 * round((self.th_plan - th_deg) / 180.0)          # W1: nearest the plan (CL-0: nearest self.fth.x)
        meas = np.array([tcp["a"] - s_now, tcp["b"]])
        err_meas = float(np.hypot(*(meas - tgt_bf)))
        if hold_z_if_far and err_meas > 1.5 * ex.tol_meas_xy_mm:
            z_ref = float(self.fz.x)
        if ex.lag_ki > 0.0:
            quasi = float(np.linalg.norm(self.fxy.v)) < ex.lag_int_vmax_mm_s and abs(float(self.fz.v)) < ex.lag_int_vmax_mm_s
            e_xy = self.fxy.x - meas
            if quasi and float(np.linalg.norm(e_xy)) < ex.lag_int_window_mm:
                self.int_xy = np.clip(self.int_xy + ex.lag_ki * e_xy * dt, -ex.lag_int_max_mm, ex.lag_int_max_mm)
            e_z = float(self.fz.x) - tcp["z"]
            if quasi and abs(e_z) < ex.lag_int_window_mm:
                self.int_z = float(np.clip(self.int_z + ex.lag_ki * e_z * dt, -ex.lag_int_max_mm, ex.lag_int_max_mm))
        self.fxy.step(tgt_bf, dt)
        self.fz.step(z_ref, dt)
        self.fth.step(th_ref, dt)
        s_cmd = s_now + sdot * ex.lead_s
        a = self.fxy.x[0] + self.int_xy[0] + s_cmd
        b = self.fxy.x[1] + self.int_xy[1]
        xy = a * self.u + b * self.v
        q = self._ik_cmd(t, dt, xy, float(self.fz.x) + self.int_z, self.phi + float(self.fth.x))
        return q, err_meas, th_ref
