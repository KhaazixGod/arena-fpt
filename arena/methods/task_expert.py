"""TASK_EXPERT (E18, PRIVILEGED like ORACLE): a scripted expert for the 40 stopped-belt tasks of arena/tasks.py; it records the demos and is the ceiling.

It reads the ground-truth pose of the objects resting on the belt at the first frame (GTTap, as ORACLE), picks the object of the task's category, plans
Cartesian waypoints in W and follows them with IK at the fixed tilt (cfg.robot.tilt_deg, same as interface I2), the joint rate limit
cfg.robot.q_dot_max_deg_s and z >= belt + executor.min_z_above_belt_mm.  The first move (home -> above the target) is in joint space.
    pick    above -> down to z_grasp -> close -> lift to belt + 60 -> hold 2.5 s
    place   pick -> carry at belt + 60 -> above the zone -> down -> open -> up
    pull    above -> down to z_grasp + 2 -> close -> drag 50 mm at 50 mm/s -> open -> up
    topple  close in the air -> down beside the object (opposite side) at 0.75 h -> push through at 80 mm/s -> wait 1 s -> back off -> up
Grasp point / closing axis: the stored good grasp of the generated object (objects_gen.py, as ORACLE); round objects try other yaws if IK fails.
Topple pushes with the closed jaws, which sit at gripper_frame_link = TCP + 29 mm along the closing axis (cfg.robot.tcp_offset_mm), the axis along the push.
"""
from __future__ import annotations

import math
from typing import List, Optional

import numpy as np

from cl0.types import Command, TrialEvent

from ..tasks import A0, B0, PARAMS, PULL_MM, ZONE_DA
from .base import MethodContext, register

V_MM_S, V_SLOW_MM_S, V_PUSH_MM_S, V_YAW_DEG_S, Q_JOINT_DEG_S = 120.0, 50.0, 80.0, 180.0, 90.0
V_CARRY_MM_S = 70.0
import os as _os
# topple tuning, 11/11, on pilot_T topple scenes 01-02 only (runs/e18_tune_topple_*): a slow push SLIDES tall objects in PhysX (0-9/20 toppled);
# a fast push at the top topples them: dz -3 / 250 mm/s 15/20, dz +7 / 250 11/20, dz -12 / 250 13/20, dz +7 / 80 9/20
TOPPLE_DZ_MM = float(_os.environ.get("E18_TOPPLE_DZ", "-3"))       # TCP height during the push = object height + this
V_PUSH_MM_S = float(_os.environ.get("E18_TOPPLE_V", "250"))
TOPPLE_PAST_MM = 40.0                                                 # the jaws travel this far past the object centre                    # smoke test 11/11: wide discs (cyl09) swung out of the jaws at 120 mm/s
LIFT_ABOVE_MM, CARRY_ABOVE_MM = 60.0, 60.0
CLOSE_S, OPEN_S, HOLD_PICK_S, TOPPLE_WAIT_S = 0.7, 0.6, 2.5, 1.0


def _smooth(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def _wrap180(d: float) -> float:
    """yaw difference mod 180 into (-90, 90]"""
    d = (d + 90.0) % 180.0 - 90.0
    return 90.0 if d == -90.0 else d


class TaskExpert:
    phase = "EXPERT"

    def __init__(self, ctx: MethodContext):
        if ctx.gt is None:
            raise RuntimeError("TASK_EXPERT needs the ground-truth tap (privileged)")
        self.gt, self.kin, self.cfg = ctx.gt, ctx.kin, ctx.cfg
        rb, ex = ctx.cfg.robot, ctx.cfg.executor
        self.tilt, self.margin, self.qdot = float(rb.tilt_deg), float(rb.joint_margin_deg), float(rb.q_dot_max_deg_s)
        self.g_open, self.g_closed = float(rb.gripper_open), float(rb.gripper_closed)
        self.jaw_off = -float(rb.tcp_offset_mm[0])                      # link = TCP + jaw_off * closing axis
        self.zb = float(ctx.calib.z_plane_mm)
        self.z_min = self.zb + float(ex.min_z_above_belt_mm)
        self.z_grasp = self.zb + float(ex.z_grasp_above_belt_mm)
        phi = math.radians(ctx.calib.belt_dir_deg)
        self.u, self.v = np.array([math.cos(phi), math.sin(phi)]), np.array([-math.sin(phi), math.cos(phi)])
        self.task: Optional[dict] = None
        self.reset(0.0, None)

    # ---------------------------------------------------------------- contract
    def set_task(self, task: dict) -> None:
        self.task = dict(task)

    def reset(self, t0, state) -> None:
        self.t0, self.finished, self.outcome = t0, False, ""
        self.events: List[TrialEvent] = []
        self.log: list = []
        self.diag: dict = {"ik_fail_ticks": 0}
        self.segs = None
        self.q_last = None if state is None else np.asarray(state.q_deg, float).copy()
        self.t_prev = t0
        self.phase = "EXPERT"

    def _w(self, a: float, b: float) -> np.ndarray:
        return a * self.u + b * self.v

    # ---------------------------------------------------------------- planning
    def _ik(self, p, yaw, q0=None, seeds=4):
        r = self.kin.ik(np.asarray(p, float), yaw, q0_deg=q0, tilt_deg=self.tilt, max_seeds=seeds, max_iter=40)
        return r.q_deg if (r.ok and self.kin.within_margin(r.q_deg, self.margin)) else None

    def _feasible(self, poses, yaw) -> bool:
        q = self.q_last
        for p in poses:
            q = self._ik(p, yaw, q)
            if q is None:
                return False
        return True

    def _objects(self, snap):
        out = {}
        for n, o in snap.items():
            sp = self.gt.spec(n)
            if abs(o["pos_mm"][2] - (self.zb + sp.height_mm / 2.0)) <= 5.0 and o.get("tilt_deg", 0.0) <= 20.0 and -360.0 <= o["b_mm"] <= -140.0:
                out[n] = (o, sp)
        return out

    def _grasp(self, o, sp):
        """(grasp point xy in W, closing-axis yaw candidates)"""
        x, y = float(o["pos_mm"][0]), float(o["pos_mm"][1])
        yaw = float(o["yaw_deg"])
        if sp.grasp:
            c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            x, y = x + c * sp.grasp[0] - s * sp.grasp[1], y + s * sp.grasp[0] + c * sp.grasp[1]
            base = yaw + sp.grasp[2]
        else:
            base = yaw + 90.0
        round_ = sp.category in ("cyl", "ring")
        square_ = len(sp.parts) == 1 and sp.parts[0].shape == "box" and max(sp.parts[0].dims_mm[:2]) <= 50.0      # either side fits the jaws
        cands = [base] + ([base + d for d in (45.0, -45.0, 90.0, 30.0, -30.0, 60.0, -60.0)] if round_ else [base + 90.0] if square_ else [])
        return np.array([x, y]), [_wrap180(c) for c in cands]

    def _plan(self, snap) -> Optional[list]:
        t = self.task
        objs = self._objects(snap)
        tg = [n for n, (o, sp) in objs.items() if sp.category == t["cat"]]
        if len(tg) != 1:
            self.outcome = f"no_target:{len(tg)}"
            return None
        o, sp = objs[tg[0]]
        self.target = tg[0]
        h, zb = sp.height_mm, self.zb
        for pre_z in sorted({zb + min(max(40.0, h + dz), 70.0) for dz in (20.0, 12.0, 6.0)}, reverse=True):   # lower the approach height if out of reach
            S = self._plan_at(t, o, sp, pre_z)
            if S:
                return S
        return None

    def _plan_at(self, t, o, sp, pre_z) -> Optional[list]:
        h, zb = sp.height_mm, self.zb
        fam = t["family"]
        pa, pb = PARAMS[t["param"]] if t["param"] else (0, 0)
        G, Gc = self.g_open, self.g_closed
        if fam in ("pick", "place", "pull"):
            gxy, yaws = self._grasp(o, sp)
            zg = self.z_grasp + 2.0 if fam == "pull" else zb + min(max(0.5 * h, self.z_grasp - zb), 20.0)   # pick/place: mid-height, 10..20 mm (mugs slipped at 10)
            pre = np.r_[gxy, pre_z]
            down = np.r_[gxy, zg]
            if fam == "pick":
                key = [pre, down, np.r_[gxy, zb + LIFT_ABOVE_MM]]
            elif fam == "place":
                zone = self._w(A0 + ZONE_DA * pa, B0)
                zone_g = zone + (gxy - np.array(o["pos_mm"][:2], float))       # keep the grasp offset of L / T shapes
                key = [pre, down, np.r_[gxy, zb + CARRY_ABOVE_MM], np.r_[zone_g, zb + CARRY_ABOVE_MM], np.r_[zone_g, zg + 1.0], np.r_[zone_g, pre_z]]
            else:
                end = gxy + PULL_MM * self._w(pa, pb)
                key = [pre, down, np.r_[end, zg], np.r_[end, pre_z]]
            yaw = next((y for y in yaws if self._feasible(key, y)), None)
            if yaw is None:
                return None
            S = [("J", pre, yaw, G, None)]
            S.append(("C", down, yaw, G, V_MM_S))
            S.append(("W", down, yaw, Gc, CLOSE_S))
            if fam == "pick":
                S.append(("C", key[2], yaw, Gc, V_MM_S)); S.append(("W", key[2], yaw, Gc, HOLD_PICK_S))
            elif fam == "place":
                for p in key[2:5]:
                    S.append(("C", p, yaw, Gc, V_CARRY_MM_S))
                S.append(("W", key[4], yaw, G, OPEN_S)); S.append(("C", key[5], yaw, G, V_MM_S)); S.append(("W", key[5], yaw, G, 1.5))
            else:
                S.append(("C", key[2], yaw, Gc, V_SLOW_MM_S)); S.append(("W", key[2], yaw, G, OPEN_S)); S.append(("C", key[3], yaw, G, V_MM_S))
                S.append(("W", key[3], yaw, G, 1.5))
            return S
        # topple: push with the closed jaws (at the link) along d, closing axis along d
        d = self._w(pa, pb)
        c = np.array(o["pos_mm"][:2], float)
        r = sp.footprint_radius_mm
        zp = zb + h + TOPPLE_DZ_MM                     # TCP just below the top: the jaw tips (~10 mm below the TCP) hit the upper part (smoke video 11/11: at 0.75 h it slid)
        yaw = _wrap180(math.degrees(math.atan2(d[1], d[0])))
        for sign in (1.0, -1.0):                                         # which way the closing axis points depends on the IK branch; checked with FK
            link0, link1 = c - (r + 15.0) * d, c + TOPPLE_PAST_MM * d
            off = sign * self.jaw_off * d                                # link - TCP
            tcp0, tcp1 = link0 - off, link1 - off
            back = tcp1 - 25.0 * d
            key = [np.r_[tcp0, pre_z], np.r_[tcp0, zp], np.r_[tcp1, zp], np.r_[back, zp], np.r_[back, pre_z]]
            q0 = self._ik(key[0], yaw, self.q_last)
            q = None if q0 is None else self._ik(key[1], yaw, q0)
            if q is None:
                continue
            _, _, cax, _, _ = self.kin.tool_axes(q)
            if float(np.dot(cax[:2], d)) * sign <= 0 or not self._feasible(key, yaw):
                continue
            S = [("J", key[0], yaw, Gc, None), ("C", key[1], yaw, Gc, V_MM_S), ("C", key[2], yaw, Gc, V_PUSH_MM_S),
                 ("W", key[2], yaw, Gc, TOPPLE_WAIT_S), ("C", key[3], yaw, Gc, V_MM_S), ("C", key[4], yaw, Gc, V_MM_S), ("W", key[4], yaw, Gc, 1.5)]
            return S
        return None

    def _timeline(self, S, t0: float, q_start: np.ndarray, p_start) -> list:
        """-> list of (t_start, t_end, kind, data) segments"""
        out, t, p_prev, yaw_prev = [], t0, None, None
        for kind, p, yaw, g, par in S:
            if kind == "J":
                q1 = self._ik(p, yaw, q_start, seeds=4)          # same seed as _feasible / the topple FK check: same IK branch
                if q1 is None:
                    return []
                T = max(float(np.max(np.abs(q1 - q_start))) / Q_JOINT_DEG_S, 1.0)
                out.append((t, t + T, "J", (q_start.copy(), q1, g)))
            elif kind == "W":
                T = float(par)
                out.append((t, t + T, "W", (p, yaw, g)))
            else:
                dist = float(np.linalg.norm(np.asarray(p) - np.asarray(p_prev)))
                T = max(dist / float(par), abs(_wrap180(yaw - yaw_prev)) / V_YAW_DEG_S, 0.25)
                out.append((t, t + T, "C", (np.asarray(p_prev, float), np.asarray(p, float), yaw_prev, yaw, g)))
            t += T
            p_prev, yaw_prev = p, yaw
        return out

    # ---------------------------------------------------------------- control
    def step(self, t, frame, belt, state) -> Command:
        dt, self.t_prev = max(t - self.t_prev, 1e-3), t
        if self.q_last is None:
            self.q_last = np.asarray(state.q_deg, float).copy()
        if self.segs is None:
            if frame is None:
                return Command(None, None, "WAIT")
            if self.task is None:
                raise RuntimeError("TASK_EXPERT: no task (run_arena --tasks)")
            S = self._plan(self.gt.objects_at_capture(frame.img))
            self.segs = self._timeline(S, t, np.asarray(state.q_deg, float), None) if S else []
            if not self.segs:
                self.finished, self.outcome = True, self.outcome or "infeasible"
                self.events.append(TrialEvent(t, "plan_failed", {"reason": self.outcome}))
                return Command(None, self.g_open, "DONE")
            self.events.append(TrialEvent(t, "plan", {"task": self.task["id"], "target": self.target, "n_seg": len(self.segs)}))
        i = next((k for k, s in enumerate(self.segs) if t < s[1]), None)
        if i is None:
            self.finished, self.outcome = True, "done"
            last = self.segs[-1]
            return Command(None, last[3][-1], "DONE")
        t_a, t_b, kind, data = self.segs[i]
        self.phase = f"{self.task['family']}:{i}{kind}"
        x = _smooth((t - t_a) / max(t_b - t_a, 1e-6))
        if kind == "J":
            q0, q1, g = data
            q = q0 + x * (q1 - q0)
            lim = self.qdot * dt
            self.q_last = self.q_last + np.clip(q - self.q_last, -lim, lim)
            return Command(self.q_last.copy(), g, self.phase)
        if kind == "W":
            p, yaw, g = data
        else:
            p0, p1, y0, y1, g = data
            p, yaw = p0 + x * (p1 - p0), y0 + x * _wrap180(y1 - y0)
        p = np.array([p[0], p[1], max(p[2], self.z_min)])
        q = self._ik(p, yaw, self.q_last, seeds=1)
        if q is None:
            q = self._ik(p, yaw, self.q_last, seeds=4)
        if q is None:
            self.diag["ik_fail_ticks"] += 1
            return Command(self.q_last.copy(), g, self.phase)
        lim = self.qdot * dt
        self.q_last = self.q_last + np.clip(q - self.q_last, -lim, lim)
        return Command(self.q_last.copy(), g, self.phase)


@register("TASK_EXPERT", privileged=True, doc="E18 scripted expert for the 40 stopped-belt tasks (arena/tasks.py), ground-truth poses", uses_pixels=False)
def make_task_expert(ctx: MethodContext):
    return TaskExpert(ctx)
