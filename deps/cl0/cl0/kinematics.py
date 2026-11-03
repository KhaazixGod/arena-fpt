"""Động học SO-101: FK từ URDF chính thức (số liệu nhúng sẵn) + IK số cho kẹp có góc chúc cố định và yaw.

Đơn vị công khai: **mm và độ**. Bên trong dùng m/rad cho hệ số URDF.

Quy ước
-------
* Hệ thế giới W = khung ``base_link`` của URDF: gốc ở mặt gắn đế, z hướng lên, x ra phía trước khi pan = 0.
* Khung công cụ = ``gripper_frame_link``: trục z = hướng tiến vào vật (approach), trục x = trục khép của hai má kẹp,
  trục y = trục bản lề. Điểm TCP = gốc khung này cộng ``tcp_offset_mm`` (tính trong khung công cụ).
* Giá trị khớp giống LeRobot với ``use_degrees=True``: LeRobot đưa thẳng độ vào ``forward_kinematics`` của đúng URDF này,
  không cộng offset `[đã kiểm trong mã lerobot 0.6.1, robot_kinematic_processor.py]`.
  Điều đó chỉ đúng nếu bạn hiệu chuẩn tay theo đúng thủ tục của LeRobot (đưa về giữa tầm chuyển động);
  nếu khác, FK lệch vài độ và camera↔robot sẽ lệch theo => kiểm bằng ``python -m cl0.calibrate fk`` (so TCP in ra với thước).

Số liệu hình học lấy từ ``so101_new_calib.urdf`` (TheRobotStudio/SO-ARM100, nhánh main, tải ngày 26/10/2026):
sha256 = 3a65d2d35e68a8d2f0c2cc176d19b884506543c93ba72980145b80abe276022c.
Chỉ nhúng các con số động học (gốc khớp, trục, giới hạn), không nhúng lưới 3D.
Muốn dùng URDF khác (ví dụ mô hình từ CAD của bạn): ``SO101Kinematics(urdf="duong_dan.urdf")``, tên khớp phải trùng.

IK: giải 5 ẩn (5 khớp) với 5 ràng buộc = vị trí TCP (3) + góc chúc của trục tiến vào trong mặt phẳng tay (1) + yaw của trục khép (1).
Giải bằng Levenberg-Marquardt có chặn khớp, khởi tạo từ nghiệm trước (liên tục) rồi tới vài hạt giống cố định.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np

ARM_JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")

# (tên khớp, xyz [m], rpy [rad], trục, (min, max) [rad])
_OFFICIAL_CHAIN = [
    ("shoulder_pan", (0.0388353, -8.97657e-09, 0.0624), (3.14159, 4.18253e-17, -3.14159), (0.0, 0.0, 1.0), (-1.91986, 1.91986)),
    ("shoulder_lift", (-0.0303992, -0.0182778, -0.0542), (-1.5708, -1.5708, 0.0), (0.0, 0.0, 1.0), (-1.74533, 1.74533)),
    ("elbow_flex", (-0.11257, -0.028, 1.73763e-16), (-3.63608e-16, 8.74301e-16, 1.5708), (0.0, 0.0, 1.0), (-1.69, 1.69)),
    ("wrist_flex", (-0.1349, 0.0052, 3.62355e-17), (4.02456e-15, 8.67362e-16, -1.5708), (0.0, 0.0, 1.0), (-1.65806, 1.65806)),
    ("wrist_roll", (5.55112e-17, -0.0611, 0.0181), (1.5708, 0.0486795, 3.14159), (0.0, 0.0, 1.0), (-2.74385, 2.84121)),
]
_OFFICIAL_TOOL = ((-0.0079, -0.000218121, -0.0981274), (0.0, 3.14159, 0.0))  # gripper_frame_joint (cố định)


def _rpy_R(r: float, p: float, y: float) -> np.ndarray:
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def _T(xyz: Sequence[float], rpy: Sequence[float]) -> np.ndarray:
    M = np.eye(4)
    M[:3, :3] = _rpy_R(*rpy)
    M[:3, 3] = xyz
    return M


def _wrap_pi(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


def _wrap_half_pi(a: float) -> float:
    """Gói về (-pi/2, pi/2]: góc của một *trục* (đối xứng 180 độ)."""
    return (a + math.pi / 2) % math.pi - math.pi / 2


def _load_urdf(path: str):
    root = ET.parse(path).getroot()
    joints = {}
    for j in root.findall("joint"):
        o, ax, lim = j.find("origin"), j.find("axis"), j.find("limit")
        joints[j.get("name")] = dict(
            parent=j.find("parent").get("link"), child=j.find("child").get("link"),
            xyz=tuple(float(v) for v in (o.get("xyz", "0 0 0") if o is not None else "0 0 0").split()),
            rpy=tuple(float(v) for v in (o.get("rpy", "0 0 0") if o is not None else "0 0 0").split()),
            axis=tuple(float(v) for v in (ax.get("xyz", "0 0 1") if ax is not None else "0 0 1").split()),
            lim=(float(lim.get("lower")), float(lim.get("upper"))) if lim is not None and lim.get("lower") else None)
    child2j = {v["child"]: k for k, v in joints.items()}
    names, link = [], "gripper_frame_link"
    while link in child2j:
        names.append(child2j[link])
        link = joints[child2j[link]]["parent"]
    names = names[::-1]
    arm = [(n, joints[n]["xyz"], joints[n]["rpy"], joints[n]["axis"], joints[n]["lim"]) for n in names if n in ARM_JOINTS]
    if [a[0] for a in arm] != list(ARM_JOINTS):
        raise ValueError(f"URDF không có đúng chuỗi khớp {ARM_JOINTS}; thấy {names}")
    tool = joints["gripper_frame_joint"]
    return arm, (tool["xyz"], tool["rpy"])


@dataclass
class IKResult:
    q_deg: np.ndarray          # 5 khớp (độ); hợp lệ khi ok
    ok: bool
    pos_err_mm: float
    ang_err_deg: float         # lỗi lớn nhất giữa góc chúc và yaw
    reason: str = ""


class SO101Kinematics:
    """FK/IK cho SO-101 (5 khớp). Thread-safe không được đảm bảo (dùng một đối tượng cho mỗi luồng)."""

    # trọng số đổi rad -> mm cho phần góc của phần dư (chỉ ảnh hưởng khi vô nghiệm)
    K_ANG_MM_PER_RAD = 60.0

    def __init__(self, urdf: Optional[str] = None, tcp_offset_mm: Sequence[float] = (0.0, 0.0, 0.0),
                 margin_deg: float = 1.0):
        chain, tool = _load_urdf(urdf) if urdf else (_OFFICIAL_CHAIN, _OFFICIAL_TOOL)
        self._T0 = [_T(xyz, rpy) for (_, xyz, rpy, _, _) in chain]
        self._axes = [np.asarray(ax, float) / (np.linalg.norm(ax) or 1.0) for (_, _, _, ax, _) in chain]
        lim = np.array([l if l is not None else (-math.pi, math.pi) for (_, _, _, _, l) in chain], float)
        self.lo_rad, self.hi_rad = lim[:, 0].copy(), lim[:, 1].copy()
        self._T_tool = _T(*tool)
        self.tcp_offset_mm = np.asarray(tcp_offset_mm, float)
        T_off = np.eye(4)
        T_off[:3, 3] = self.tcp_offset_mm / 1000.0
        self._T_tcp = self._T_tool @ T_off
        self.margin_rad = math.radians(margin_deg)
        self._sigma, self._pan_xy = self._detect_pan_convention()
        self._init_seed_model()

    # ------------------------------------------------------------------ FK
    def _rot_about(self, axis: np.ndarray, th: np.ndarray) -> np.ndarray:
        """Ma trận 4x4 xoay quanh trục (batch theo th, shape (N,))."""
        N = th.shape[0]
        c, s = np.cos(th), np.sin(th)
        if np.allclose(axis, (0, 0, 1)):
            R = np.zeros((N, 4, 4))
            R[:, 0, 0] = c; R[:, 0, 1] = -s; R[:, 1, 0] = s; R[:, 1, 1] = c; R[:, 2, 2] = 1; R[:, 3, 3] = 1
            return R
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        R = np.zeros((N, 4, 4))
        R[:, :3, :3] = np.eye(3) + s[:, None, None] * K + (1 - c)[:, None, None] * (K @ K)
        R[:, 3, 3] = 1
        return R

    def _fk_batch(self, Q: np.ndarray) -> np.ndarray:
        """Q: (N,5) rad -> (N,4,4) khung TCP trong W (đơn vị m)."""
        N = Q.shape[0]
        M = np.broadcast_to(np.eye(4), (N, 4, 4)).copy()
        for i in range(5):
            M = M @ self._T0[i]
            M = M @ self._rot_about(self._axes[i], Q[:, i])
        return M @ self._T_tcp

    def fk(self, q_deg: Sequence[float]):
        """Trả về (p_mm (3,), R (3,3)) của TCP trong W. Lấy 5 giá trị đầu của q_deg."""
        q = np.radians(np.asarray(q_deg, float)[:5])
        M = self._fk_batch(q[None, :])[0]
        return M[:3, 3] * 1000.0, M[:3, :3].copy()

    def tool_axes(self, q_deg: Sequence[float]):
        """(p_mm, approach, closing, pitch_deg, yaw_deg). yaw = phương vị của trục khép chiếu lên mặt phẳng ngang, mod 180."""
        p, R = self.fk(q_deg)
        a, c = R[:, 2], R[:, 0]
        pitch = self._pitch(np.radians(q_deg[0]), a)
        yaw = math.atan2(c[1], c[0])
        return p, a, c, math.degrees(pitch), math.degrees(_wrap_half_pi(yaw))

    # -------------------------------------------------------- quy ước pan/góc chúc
    def _detect_pan_convention(self):
        """Hướng của mặt phẳng tay theo pan: u_h(pan) = (cos(sigma*pan), sin(sigma*pan)) quanh trục pan.
        Phát hiện từ FK: với tay duỗi, quay pan +0.1 rad thì TCP đi về phía y âm hay dương."""
        q0 = np.zeros((1, 5))
        q1 = q0.copy(); q1[0, 0] = 0.1
        p0, p1 = self._fk_batch(q0)[0][:3, 3], self._fk_batch(q1)[0][:3, 3]
        pan_xy = self._T0[0][:2, 3].copy()           # trục pan đi qua điểm này trong W (m)
        r0, r1 = p0[:2] - pan_xy, p1[:2] - pan_xy
        cross = r0[0] * r1[1] - r0[1] * r1[0]
        sigma = 1.0 if cross > 0 else -1.0
        # hướng mặt phẳng tay lúc pan = 0 (đơn vị): hướng nằm ngang từ trục pan tới TCP; kỳ vọng ~ +x
        ex = r0 / (np.linalg.norm(r0) or 1.0)
        self._ex = ex
        return sigma, pan_xy

    def _uh(self, pan_rad: float) -> np.ndarray:
        th = self._sigma * pan_rad
        c, s = math.cos(th), math.sin(th)
        return np.array([c * self._ex[0] - s * self._ex[1], s * self._ex[0] + c * self._ex[1]])

    def _pitch(self, pan_rad: float, a: np.ndarray) -> float:
        """Góc chúc (rad) của trục tiến vào: 90° = thẳng xuống; <90° = chếch ra xa đế; >90° = chếch vào phía đế."""
        uh = self._uh(pan_rad)
        return math.atan2(-a[2], float(a[0] * uh[0] + a[1] * uh[1]))

    # ------------------------------------------------------------------ IK
    def _residual_batch(self, Q: np.ndarray, p_t_m: np.ndarray, tilt_rad: float, yaw_rad: float) -> np.ndarray:
        M = self._fk_batch(Q)
        N = Q.shape[0]
        R = np.empty((N, 5))
        R[:, :3] = (M[:, :3, 3] - p_t_m) * 1000.0
        for k in range(N):
            a, c = M[k, :3, 2], M[k, :3, 0]
            R[k, 3] = self.K_ANG_MM_PER_RAD * _wrap_pi(self._pitch(Q[k, 0], a) - tilt_rad)
            R[k, 4] = self.K_ANG_MM_PER_RAD * _wrap_half_pi(math.atan2(c[1], c[0]) - yaw_rad)
        return R

    def _jac(self, q: np.ndarray, p_t_m, tilt_rad, yaw_rad, h=1e-5) -> np.ndarray:
        Qs = np.repeat(q[None, :], 10, axis=0)
        for i in range(5):
            Qs[2 * i, i] += h
            Qs[2 * i + 1, i] -= h
        R = self._residual_batch(Qs, p_t_m, tilt_rad, yaw_rad)
        # các phần dư góc đã gói về nửa khoảng; sai phân trung tâm vẫn ổn khi h nhỏ
        return ((R[0::2] - R[1::2]) / (2 * h)).T

    def _init_seed_model(self):
        """Với SO-101: góc chúc = lift + elbow + flex + c0 (ba trục song song) => hạt giống thoả ràng buộc chúc.
        Cũng đo hệ số yaw theo pan và roll để đoán roll. Nếu URDF khác cấu trúc, tắt chế độ này (dùng hạt giống cố định)."""
        rng = np.random.default_rng(7)
        lo, hi = np.degrees(self.lo_rad), np.degrees(self.hi_rad)
        q = np.zeros(5)
        self._pitch_c0 = self.tool_axes(q)[3]
        ok = True
        for _ in range(8):
            q = rng.uniform(lo, hi)
            d = self.tool_axes(q)[3] - (q[1] + q[2] + q[3] + self._pitch_c0)
            if abs((d + 180) % 360 - 180) > 0.2:
                ok = False
        self._pitch_linear = ok
        # hệ số yaw: dyaw/dpan, dyaw/droll tại tư thế chúc xuống tham chiếu
        qr = np.array([0.0, -10.0, 56.0, 90.0 - 46.0 - self._pitch_c0, 0.0])
        y0 = self.tool_axes(qr)[4]
        self._yaw0 = y0
        def dyaw(k, dv=5.0):
            q2 = qr.copy(); q2[k] += dv
            return ((self.tool_axes(q2)[4] - y0 + 90) % 180 - 90) / dv
        self._c_pan, self._c_roll = dyaw(0), dyaw(4)
        if abs(self._c_roll) < 0.5:
            self._c_roll = 1.0
        self._fallback_seeds = [np.radians(v) for v in
                                ([0, -10, 56, 45, 0], [0, -30, 48, 70, 0], [0, 10, 56, 25, 0], [0, 30, 30, 30, 0])]

    def _seed_candidates(self, p_t_m: np.ndarray, yaw_deg: float, tilt_deg: float, k: int = 6):
        """Danh sách hạt giống (rad) xếp theo sai số vị trí FK tăng dần."""
        az = math.atan2(p_t_m[1] - self._pan_xy[1], p_t_m[0] - self._pan_xy[0])
        ex_az = math.atan2(self._ex[1], self._ex[0])
        pan = float(np.clip(self._sigma * _wrap_pi(az - ex_az), self.lo_rad[0], self.hi_rad[0]))
        lo, hi = np.degrees(self.lo_rad), np.degrees(self.hi_rad)
        roll0 = ((yaw_deg - self._yaw0 - self._c_pan * math.degrees(pan)) / self._c_roll + 90) % 180 - 90
        rolls = [r for r in (roll0, roll0 + 180, roll0 - 180) if lo[4] <= r <= hi[4]] or [0.0]
        rolls.sort(key=abs)
        cands = []
        if self._pitch_linear:
            for ql in (-45, -30, -15, 0, 15, 30, 45):
                for qe in (15, 30, 45, 60, 75):
                    qf = tilt_deg - ql - qe - self._pitch_c0
                    if lo[3] <= qf <= hi[3]:
                        for r in rolls[:2]:
                            cands.append([math.degrees(pan), ql, qe, qf, r])
        else:
            for s in self._fallback_seeds:
                for r in rolls[:2]:
                    cands.append([math.degrees(pan), *np.degrees(s[1:4]), r])
        if not cands:
            return []
        Q = np.radians(np.asarray(cands, float))
        err = np.linalg.norm(self._fk_batch(Q)[:, :3, 3] - p_t_m, axis=1)
        order = np.argsort(err)[:k]
        return [Q[i] for i in order]

    def _lm(self, q_init, p_t_m, tilt_rad, yaw_rad, tol_mm=0.02, tol_ang=0.02, max_iter=60):
        lo, hi = self.lo_rad, self.hi_rad
        q = np.clip(q_init, lo, hi)
        r = self._residual_batch(q[None, :], p_t_m, tilt_rad, yaw_rad)[0]
        cost = float(r @ r)
        lam = 1e-2
        for _ in range(max_iter):
            if np.linalg.norm(r[:3]) < tol_mm and np.max(np.abs(r[3:])) / self.K_ANG_MM_PER_RAD < math.radians(tol_ang):
                break
            J = self._jac(q, p_t_m, tilt_rad, yaw_rad)
            g = J.T @ r
            A = J.T @ J
            improved = False
            for _try in range(8):
                try:
                    dq = -np.linalg.solve(A + lam * np.eye(5), g)
                except np.linalg.LinAlgError:
                    lam *= 10
                    continue
                dq = np.clip(dq, -0.6, 0.6)
                qn = np.clip(q + dq, lo, hi)
                rn = self._residual_batch(qn[None, :], p_t_m, tilt_rad, yaw_rad)[0]
                cn = float(rn @ rn)
                if cn < cost:
                    q, r, cost = qn, rn, cn
                    lam = max(lam * 0.3, 1e-9)
                    improved = True
                    break
                lam *= 10
            if not improved:
                break
        return q, r

    def ik(self, p_mm: Sequence[float], yaw_deg: float, q0_deg: Optional[Sequence[float]] = None,
           tilt_deg: float = 90.0, tol_mm: float = 0.05, tol_ang_deg: float = 0.1,
           max_seeds: Optional[int] = None, max_iter: int = 60) -> IKResult:
        """IK cho TCP tại p_mm (W), trục khép có phương vị yaw_deg (mod 180), góc chúc tilt_deg.
        ``q0_deg``: khởi tạo từ nghiệm trước để liên tục (``max_seeds=1`` => chỉ dùng nó: nhanh, dùng trong vòng điều khiển).
        ok = hội tụ và trong giới hạn khớp; biên an toàn kiểm riêng bằng ``within_margin``."""
        p_t = np.asarray(p_mm, float) / 1000.0
        tilt, yaw = math.radians(tilt_deg), math.radians(yaw_deg)
        seeds = []
        if q0_deg is not None:
            seeds.append(np.radians(np.asarray(q0_deg, float)[:5]))
        if max_seeds is None or len(seeds) < max_seeds:
            seeds.extend(self._seed_candidates(p_t, yaw_deg, tilt_deg))
        if max_seeds is not None:
            seeds = seeds[:max_seeds]
        best = None
        for s in seeds:
            q, r = self._lm(s, p_t, tilt, yaw, max_iter=max_iter)
            pe = float(np.linalg.norm(r[:3]))
            ae = float(np.max(np.abs(r[3:])) / self.K_ANG_MM_PER_RAD)
            in_lim = bool(np.all(q >= self.lo_rad + 0 * self.margin_rad - 1e-9) and np.all(q <= self.hi_rad + 1e-9))
            ok = pe <= tol_mm and math.degrees(ae) <= tol_ang_deg and in_lim
            # biên an toàn: vẫn ok nếu sát biên nhưng không vượt (margin dùng ở reachable())
            res = IKResult(np.degrees(q), ok, pe, math.degrees(ae), "" if ok else "không hội tụ / ngoài giới hạn khớp")
            if ok:
                return res
            if best is None or pe + 10 * ae < best.pos_err_mm + 10 * math.radians(best.ang_err_deg):
                best = res
        if best is None:
            best = IKResult(np.zeros(5), False, float("inf"), float("inf"), "không có hạt giống hợp lệ cho góc chúc này")
        return best

    def within_margin(self, q_deg: Sequence[float], margin_deg: Optional[float] = None) -> bool:
        m = self.margin_rad if margin_deg is None else math.radians(margin_deg)
        q = np.radians(np.asarray(q_deg, float)[:5])
        return bool(np.all(q >= self.lo_rad + m) and np.all(q <= self.hi_rad - m))

    def reachable(self, p_mm, yaw_deg, tilt_deg=90.0, margin_deg: Optional[float] = None, q0_deg=None) -> bool:
        r = self.ik(p_mm, yaw_deg, q0_deg=q0_deg, tilt_deg=tilt_deg)
        return bool(r.ok and self.within_margin(r.q_deg, margin_deg))

    @property
    def limits_deg(self):
        return np.degrees(self.lo_rad), np.degrees(self.hi_rad)

    def pan_axis_xy_mm(self) -> np.ndarray:
        return self._pan_xy * 1000.0
