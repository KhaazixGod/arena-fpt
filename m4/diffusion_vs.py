"""M4 of the thesis (Chapter 6): Diffusion Policy with a visual-servoing correction.

DP_W (arena/methods/diffusion_i2.py) is used unchanged: same checkpoints, same observation queue, same replanning every n_action_steps frames, same executor
(belt frame -> world with the belt counter at execution time, IK seeded with the last command, joint-rate limit, z guard).  What is added, between the chunk target and
the IK, is a correction that is driven by CL-0's belt-frame tracker (Detector + Tracker, unchanged):

    e_t   = P_target,t - P_ee,t            (belt frame, x_b y_b; P_ee from the measured joints by FK, P_target = the tracked grasp point of the gated track)
    e_psi = wrap_(-90,90](psi_target - psi_ee)                       (closing axis, mod 180; skipped for isotropic objects)
    c    += lambda(phase) * K * e * dt                               (offset on the policy reference; |dc/dt| and |c| saturated)
    target' = target_DP + c

The correction restarts (c = 0) at every replanning: the new chunk is anchored at the measured pose of its newest observation, which already contains the
previous correction.  Phases: APPROACH (lambda 0) until |e_xy| <= r_align, ALIGN (lambda ramps to lambda_max), GRASPED (measured gripper closed; correction frozen,
perception frozen), BLIND (no track within the gate: DP alone).  Optional grasp authorization: while the policy commands CLOSE, the gripper command is held open
until |e_xy| <= eps_xy (and |e_psi| <= eps_psi) for n_hold ticks, or t_hold_max has passed, or there is no track.

Tracks are kept for 6 s without an observation (CL-0: 1.5 s), because the arm exclusion zone hides the object from the detector while the gripper is above it.
All parameters come from the environment (VS_*; defaults in m4/m4_vs.env), so that they can be fixed on the development sheet and hashed with the run.  VS_OFF=1 disables the correction
(the method then behaves as DP_I2, apart from the detector running).  Served like DP_I2:

    DP_CKPT=runs/dp_w_s1000/checkpoints/last/pretrained_model env -u PYTHONPATH ~/venvs/lerobot_data/bin/python remote_server.py \
        --factory diffusion_vs:make_method --name DPVS --port 6201 --path m4 --path . --path ../cl0 --repeat
"""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, asdict, replace
from typing import List, Optional

import numpy as np

try:
    from cl0.types import Command, TrialEvent
except Exception:                          # noqa: BLE001  (remote_server.py's fallbacks have the same fields)
    from remote_server import Command, TrialEvent  # type: ignore
from cl0.config import config_from_dict
from cl0.geometry import PlaneCalib, Rectifier, perp, unit, wrap_axis_diff
from cl0.kinematics import SO101Kinematics
from cl0.perception import BackgroundModel, Detector, window_of
from cl0.tracker import Tracker

from arena.i2 import to_vec, to_world
from arena.methods.diffusion_i2 import DPI2Method

ISO_RATIO = 1.15                           # cl0.grasp.GraspParams.isotropic_ratio: below it the object is isotropic and the closing yaw is a fixed convention
THETA_STD_MAX = 12.0                       # deg: a track whose closing yaw scatters more than this (near-round objects) gets no yaw correction


def _f(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


@dataclass
class VSParams:
    off: bool = False            # VS_OFF: no correction, no authorization
    lam_max: float = 1.0         # VS_LAMBDA
    kxy: float = 3.0             # VS_KXY (1/s); stability needs K * loop delay < pi/2 (Section 6.2)
    kyaw: float = 3.0            # VS_KYAW (1/s)
    use_yaw: bool = True         # VS_YAW
    yaw_aspect_min: float = 1.3  # VS_YAW_ASPECT: yaw is corrected only for tracks whose silhouette aspect ratio is at least this (a clear long axis)
    r_align: float = 40.0        # VS_RALIGN (mm): |e_xy| below this -> ALIGN
    ramp_s: float = 0.3          # VS_RAMP_S: lambda ramp in ALIGN
    gate_mm: float = 35.0        # VS_GATE: radius between the policy reference and a track
    gate_ahead_s: float = 0.5    # VS_GATE_AHEAD_S: the reference point of the gate is the chunk target this far ahead
    vsat: float = 80.0           # VS_VSAT (mm/s): saturation of the correction speed
    wsat: float = 90.0           # VS_WSAT (deg/s)
    cmax: float = 30.0           # VS_CMAX (mm): |c_xy| bound
    cpsimax: float = 60.0        # VS_CPSIMAX (deg)
    auth: bool = True            # VS_AUTH: grasp authorization
    eps_xy: float = 3.0          # VS_EPS_XY (mm)
    eps_yaw: float = 15.0        # VS_EPS_YAW (deg)
    n_hold: int = 6              # VS_NHOLD (control ticks, 50 Hz)
    t_hold_max: float = 1.0      # VS_THOLD_MAX (s): longest wait for the authorization
    close_cmd_thr: float = 20.0  # policy gripper command below this = wants to close (open 40, close 0 in the demos)
    closed_meas_thr: float = 25.0  # measured gripper below this = closed

    @staticmethod
    def from_env() -> "VSParams":
        return VSParams(off=os.environ.get("VS_OFF", "0") == "1", lam_max=_f("VS_LAMBDA", 1.0), kxy=_f("VS_KXY", 3.0), kyaw=_f("VS_KYAW", 3.0),
                        use_yaw=os.environ.get("VS_YAW", "1") == "1", yaw_aspect_min=_f("VS_YAW_ASPECT", 1.3), r_align=_f("VS_RALIGN", 40.0), ramp_s=_f("VS_RAMP_S", 0.3), gate_mm=_f("VS_GATE", 35.0),
                        gate_ahead_s=_f("VS_GATE_AHEAD_S", 0.5), vsat=_f("VS_VSAT", 80.0), wsat=_f("VS_WSAT", 90.0), cmax=_f("VS_CMAX", 30.0),
                        cpsimax=_f("VS_CPSIMAX", 60.0), auth=os.environ.get("VS_AUTH", "1") == "1", eps_xy=_f("VS_EPS_XY", 3.0), eps_yaw=_f("VS_EPS_YAW", 15.0),
                        n_hold=int(_f("VS_NHOLD", 6)), t_hold_max=_f("VS_THOLD_MAX", 1.0))


class DPVSMethod(DPI2Method):
    phase = "DPVS"

    def __init__(self, ckpt, duration_s, kin: SO101Kinematics, belt_dir_deg, z_belt_mm, robot, executor, replan, device, n_infer_steps,
                 det: Detector, track_cfg, arm_excl_mm: float, vs: VSParams):
        self.det, self.track_cfg, self.arm_excl, self.vs = det, track_cfg, float(arm_excl_mm), vs     # before super(): its __init__ calls self.reset
        self.phi = float(belt_dir_deg)
        self.uu, self.vv = unit(self.phi), perp(self.phi)
        super().__init__(ckpt, duration_s, kin, belt_dir_deg, z_belt_mm, robot, executor, replan, device, n_infer_steps)

    # ------------------------------------------------------------------------------------------------------ state
    def reset(self, t0, state) -> None:
        super().reset(t0, state)
        self.events = [TrialEvent(t0, "phase:DPVS", {"ckpt": self.ckpt, "replan": self.replan, "infer_steps": int(self.policy.diffusion.num_inference_steps),
                                                      "vs": asdict(self.vs)})]
        self.tracker = Tracker(self.track_cfg)
        self.aspect: dict = {}
        self.tid: Optional[int] = None
        self.c = np.zeros(3)                       # correction: x_b mm, y_b mm, yaw deg
        self.vs_phase = "APPROACH"
        self.t_align: Optional[float] = None
        self.want_close_t: Optional[float] = None
        self.n_ok = 0
        self.authorised = False
        self.closed_seen = False
        self.g_open = 40.0
        self.diag.update({"vs_frames": 0, "vs_det_s": 0.0, "vs_fallback": 0, "vs_wait_ticks": 0, "vs_auth_timeout": 0, "vs_align_ticks": 0, "vs_blind_ticks": 0})

    def _event(self, t, name, **data) -> None:
        self.events.append(TrialEvent(t, name, data))

    # ------------------------------------------------------------------------------------------------------ perception
    def _perceive(self, t, frame, belt, p_ee_w) -> None:
        """Detector + tracker of CL-0 on every camera frame until the gripper has closed (then the tracks are frozen, as CL-0 does at selection)."""
        if self.closed_seen:
            return
        s_img = belt.s_at(frame.t_capture)
        exclude = [(float(p_ee_w @ np.r_[self.uu, 0.0]), float(p_ee_w @ np.r_[self.vv, 0.0]), self.arm_excl)]
        t0 = time.perf_counter()
        res = self.det.detect(frame.img, s_img, exclude)
        self.diag["vs_det_s"] += time.perf_counter() - t0
        self.diag["vs_frames"] += 1
        self.tracker.update(res.dets, s_img, frame.t_capture)
        self.tracker.prune(t, keep=self.tid)
        for d in res.dets:
            if d.ok:
                tr = self.tracker.match(d.a_mm - s_img, d.b_mm)
                if tr is not None:
                    self.aspect.setdefault(tr.tid, []).append(float(d.aspect))
                    self.aspect[tr.tid] = self.aspect[tr.tid][-6:]

    def _gate(self, t):
        """The confirmed track nearest to the policy reference `gate_ahead_s` ahead, within the gate radius (hysteresis: a held track is kept up to 2x the radius)."""
        k = int(max((t - self.t_img) * self.fps, 0.0)) + int(round(self.vs.gate_ahead_s * self.fps))
        ref = self.chunk[min(k, len(self.chunk) - 1)][:2]
        best, held = None, None
        for tr in self.tracker.confirmed():
            a, b, th, w, std = tr.estimate()
            xy = a * self.uu + b * self.vv
            d = float(np.hypot(*(xy - ref)))
            o = np.asarray(tr.obs, float)
            th_std = float(np.sqrt(max(-2.0 * math.log(max(math.hypot(np.sin(np.radians(2 * o[:, 3])).mean(), np.cos(np.radians(2 * o[:, 3])).mean()), 1e-9)), 0.0)) / 2.0 * 180.0 / math.pi) if len(o) > 1 else 0.0
            item = (d, tr.tid, xy, th, th_std)
            if tr.tid == self.tid and d <= 2.0 * self.vs.gate_mm:
                held = item
            if d <= self.vs.gate_mm and (best is None or d < best[0]):
                best = item
        pick = held or best
        return pick

    # ------------------------------------------------------------------------------------------------------ correction
    def _correct(self, t, tgt: np.ndarray, x: np.ndarray, s_now: float, dt: float):
        vs = self.vs
        g_cmd = float(np.clip(tgt[5], 0.0, 100.0))
        tgt_c, g_out = tgt.copy(), g_cmd
        g_meas = float(x[5])
        p_ee, _, _, _, yaw_ee = self.kin.tool_axes(x[:5])
        ee_b = np.asarray(p_ee[:2], float) - s_now * self.uu
        row = {"vs_t": round(float(t), 4), "vs_phase": self.vs_phase, "vs_tid": -1, "vs_lam": 0.0}
        if vs.off:
            return tgt_c, g_out, row
        # a re-opened gripper (the policy retries) starts the cycle again
        if self.closed_seen and g_meas > vs.closed_meas_thr + 10.0:
            self.closed_seen, self.tid, self.t_align, self.want_close_t, self.n_ok, self.authorised = False, None, None, None, 0, False
            self.c[:] = 0.0
        if g_meas < vs.closed_meas_thr:
            if not self.closed_seen:
                self._event(t, "vs_closed", c=[round(float(v), 2) for v in self.c], tid=self.tid)
            self.closed_seen = True
            self.vs_phase = "GRASPED"
            row["vs_phase"] = "GRASPED"
        else:
            if g_cmd >= vs.close_cmd_thr:
                self.g_open = g_cmd
            gate = self._gate(t)
            e_xy = np.zeros(2); e_psi = 0.0; iso = True; have = gate is not None
            if have:
                d_ref, tid, xy_t, th, th_std = gate
                if tid != self.tid:
                    self._event(t, "vs_track", tid=tid, d_ref=round(d_ref, 1), xy=[round(float(v), 1) for v in xy_t])
                    self.tid, self.t_align = tid, None
                asp = self.aspect.get(tid)
                a_med = float(np.median(asp)) if asp else 1.0
                iso = a_med < max(ISO_RATIO, vs.yaw_aspect_min) or th_std > THETA_STD_MAX      # no reliable long axis: no yaw correction
                yaw_t = wrap_axis_diff(th + self.phi)
                e_xy = np.asarray(xy_t, float) - ee_b
                e_psi = wrap_axis_diff(yaw_t - yaw_ee)
                n = float(np.hypot(*e_xy))
                if n > vs.r_align:
                    self.vs_phase, self.t_align = "APPROACH", None
                else:
                    if self.t_align is None:
                        self.t_align = t
                        self._event(t, "vs_phase:ALIGN", e_xy=round(n, 2), e_psi=round(e_psi, 1), iso=iso)
                    self.vs_phase = "ALIGN"
                row.update(vs_tid=tid, vs_exy=round(n, 2), vs_ex=round(float(e_xy[0]), 2), vs_ey=round(float(e_xy[1]), 2), vs_epsi=round(e_psi, 2), vs_iso=int(iso))
            else:
                if self.tid is not None:
                    self._event(t, "vs_track_lost", tid=self.tid)
                self.tid, self.t_align = None, None
                self.vs_phase = "BLIND"
                self.diag["vs_blind_ticks"] += 1
            lam = 0.0
            if self.vs_phase == "ALIGN":
                lam = vs.lam_max * min(1.0, (t - self.t_align) / max(vs.ramp_s, 1e-6))
                self.diag["vs_align_ticks"] += 1
                dxy = lam * vs.kxy * e_xy * dt
                cap = vs.vsat * dt
                nd = float(np.hypot(*dxy))
                if nd > cap:
                    dxy = dxy * (cap / nd)
                self.c[:2] += dxy
                nc = float(np.hypot(*self.c[:2]))
                if nc > vs.cmax:
                    self.c[:2] *= vs.cmax / nc
                if vs.use_yaw and not iso:
                    dpsi = float(np.clip(lam * vs.kyaw * e_psi * dt, -vs.wsat * dt, vs.wsat * dt))
                    self.c[2] = float(np.clip(self.c[2] + dpsi, -vs.cpsimax, vs.cpsimax))
            row["vs_lam"] = round(lam, 3)
            # ---- grasp authorization
            wants_close = g_cmd < vs.close_cmd_thr
            if vs.auth and wants_close:
                if self.want_close_t is None:
                    self.want_close_t = t
                if not have:
                    ok = True
                else:
                    ok = float(np.hypot(*e_xy)) <= vs.eps_xy and (iso or (not vs.use_yaw) or abs(e_psi) <= vs.eps_yaw)
                self.n_ok = self.n_ok + 1 if ok else 0
                if not self.authorised:
                    if self.n_ok >= vs.n_hold:
                        self.authorised = True
                        self._event(t, "vs_auth", waited=round(t - self.want_close_t, 3), n_ok=self.n_ok)
                    elif t - self.want_close_t >= vs.t_hold_max:
                        self.authorised = True
                        self.diag["vs_auth_timeout"] += 1
                        self._event(t, "vs_auth_timeout", waited=round(t - self.want_close_t, 3))
                if not self.authorised:
                    g_out = max(g_cmd, self.g_open)
                    self.diag["vs_wait_ticks"] += 1
            elif not wants_close:
                self.want_close_t, self.n_ok, self.authorised = None, 0, False
        # ---- apply the offset to the policy reference
        tgt_c[0] += self.c[0]
        tgt_c[1] += self.c[1]
        if self.c[2] != 0.0:
            psi = 0.5 * math.atan2(tgt[4], tgt[3]) + math.radians(self.c[2])
            tgt_c[3], tgt_c[4] = math.cos(2.0 * psi), math.sin(2.0 * psi)
        row.update(vs_cx=round(float(self.c[0]), 2), vs_cy=round(float(self.c[1]), 2), vs_cpsi=round(float(self.c[2]), 2), vs_gcmd=round(g_cmd, 1), vs_gout=round(g_out, 1),
                   vs_auth=int(self.authorised), vs_phase=self.vs_phase)
        return tgt_c, g_out, row

    # ------------------------------------------------------------------------------------------------------ IK with a fall-back to the uncorrected target
    def _try_ik(self, p, yaw):
        p = np.array([p[0], p[1], max(p[2], self.z_min)])
        r = self.kin.ik(p, yaw, q0_deg=self.q_last, tilt_deg=self.tilt, max_seeds=1, max_iter=15)
        if not (r.ok and self.kin.within_margin(r.q_deg, self.margin)):
            r = self.kin.ik(p, yaw, q0_deg=self.q_last, tilt_deg=self.tilt, max_seeds=4, max_iter=25)
        return np.asarray(r.q_deg, float) if (r.ok and self.kin.within_margin(r.q_deg, self.margin)) else None

    # ------------------------------------------------------------------------------------------------------ control tick
    def step(self, t, frame, belt, state) -> Command:
        if t - self.t0 >= self.duration_s:
            self.finished, self.outcome = True, "dpvs_timeout"
            self.events.append(TrialEvent(t, "phase:DONE", {}))
            return Command(None, None, "DONE")
        dt, self.t_prev = max(t - self.t_prev, 1e-3), t
        x = np.r_[np.asarray(state.q_deg, float), float(state.gripper)]
        if self.q_last is None:
            self.q_last = x[:5].copy()
        self.hist_t.append(float(t)); self.hist_x.append(x)
        if frame is not None:
            t_img = float(frame.t_capture)
            xs = self._state_at(t_img)
            s_img = belt.s_at(t_img)
            vec = to_vec(self.kin, xs[:5], xs[5], s_img, self.u)
            b = self._observe(frame.img, vec)
            self.frames_since += 1
            if self.chunk is None or self.frames_since >= self.replan:
                self.chunk, self.t_img, self.frames_since = self._sample(b), t_img, 0
                self.c[:] = 0.0                        # the chunk is anchored at the measured pose of its newest observation
                self.diag["plans"] += 1
                self.log.append({"t": round(float(t), 4), "t_img": round(t_img, 4), "s_img": round(float(s_img), 2),
                                 **{f"st{i}": round(float(v), 3) for i, v in enumerate(vec)},
                                 **{f"a0_{i}": round(float(v), 3) for i, v in enumerate(self.chunk[0])}})
            if not self.vs.off:
                p_w, _, _, _, _ = self.kin.tool_axes(x[:5])
                self._perceive(t, frame, belt, np.asarray(p_w, float))
        if self.chunk is None:
            return self.cmd
        k = min(max((t - self.t_img) * self.fps, 0.0), len(self.chunk) - 1.0)
        i = int(k); w = k - i
        tgt = self.chunk[i] if i + 1 >= len(self.chunk) else (1 - w) * self.chunk[i] + w * self.chunk[i + 1]
        s_now = belt.s_at(t)
        tgt_c, g_out, row = self._correct(t, np.asarray(tgt, float), x, s_now, dt)
        self.log.append(row)
        p0, yaw0, _ = to_world(tgt, s_now, self.u)
        if np.any(self.c != 0.0):
            p1, yaw1, g = to_world(tgt_c, s_now, self.u)
            q = self._try_ik(p1, yaw1)
            if q is None:
                self.diag["vs_fallback"] += 1
                q = self._try_ik(p0, yaw0)
            if q is None:
                q_cmd = self._ik(t, p0, yaw0, dt)      # records the failure exactly as DP_I2 does
            else:
                lim = self.qdot * dt
                self.q_last = self.q_last + np.clip(q - self.q_last, -lim, lim)
                q_cmd = self.q_last.copy()
        else:
            _, _, g = to_world(tgt_c, s_now, self.u)
            q_cmd = self._ik(t, p0, yaw0, dt)
        self.cmd = Command(q_cmd, float(np.clip(g_out, 0.0, 100.0)), "DPVS")
        return self.cmd


def _resolve(path: str) -> str:
    if os.path.exists(path):
        return path
    alt = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), path)
    return alt if os.path.exists(alt) else path


def make_method(info):
    cfg_d, calib_d = info["cfg"], info["calib"]
    cfg = config_from_dict(cfg_d)
    rb = cfg_d["robot"]
    kin = SO101Kinematics(urdf=rb.get("urdf") or None, tcp_offset_mm=rb["tcp_offset_mm"], margin_deg=rb["joint_margin_deg"])
    calib = PlaneCalib.load(_resolve(info["calib_path"]))
    bg = BackgroundModel.load(_resolve(info["background_path"]))
    det = Detector(Rectifier(calib, window_of(bg)), bg, cfg.perception)
    dur = float(os.environ.get("DP_T_S", cfg_d["executor"]["trial_timeout_s"]))
    return DPVSMethod(os.environ["DP_CKPT"], dur, kin, float(calib_d["belt_dir_deg"]), float(calib_d["z_plane_mm"]), rb, cfg_d["executor"],
                      int(os.environ.get("DP_REPLAN", "0")), os.environ.get("DP_DEVICE", "cuda"), int(os.environ.get("DP_STEPS", "0")),
                      det, replace(cfg.track, lost_s=max(cfg.track.lost_s, 6.0)), float(cfg.executor.arm_exclusion_mm), VSParams.from_env())
