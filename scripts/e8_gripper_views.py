"""E8 prep: what gripper does the SIM have?  Side / front / bottom views of the two jaws of the official SO-101 gripper (so101_new_calib.urdf) in the TCP
frame (gripper_frame_link: x = closing axis, z = approach axis), at gripper.pos 0 / 40 / 80.  Pure numpy + OpenCV (no Isaac).  For the user to compare with
the REAL gripper.   env -u PYTHONPATH ~/venvs/cl0/bin/python arena/scripts/e8_gripper_views.py
"""
import math, os, struct
import cv2
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(HERE, "assets", "so101_src", "assets")


def stl(p):
    d = open(p, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return a["v"].reshape(-1, 3).astype(float)


def T(xyz, rpy):
    r, p, y = rpy
    Rx = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
    Ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    Rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    M = np.eye(4); M[:3, :3] = Rz @ Ry @ Rx; M[:3, 3] = xyz
    return M


def tf(M, P):
    return (M[:3, :3] @ P.T).T + M[:3, 3]


fixed_mesh = tf(T((8.32667e-17, -0.000218214, 0.000949706), (-3.14159, 0, 0)), stl(os.path.join(A, "wrist_roll_follower_so101_v1.stl")))
moving_mesh = stl(os.path.join(A, "moving_jaw_so101_v1.stl"))
T_tool = T((-0.0079, -0.000218121, -0.0981274), (0, 3.14159, 0))           # gripper_link -> gripper_frame_link
Ti = np.linalg.inv(T_tool)
g0, g100 = -10.0, 100.0
S, W, H = 2400.0, 360, 420                                                      # px per metre, panel size
panels = []
for pos in (0, 40, 80):
    q = math.radians(g0 + (g100 - g0) * pos / 100.0)
    Mj = T((0.0202, 0.0188, -0.0234), (1.5708, 0, 0)) @ T((0, 0, 0), (0, 0, q)) @ T((0, 0, 0.0189), (0, 0, 0))
    F = tf(Ti, fixed_mesh) * 1000.0; Mv = tf(Ti, tf(Mj, moving_mesh)) * 1000.0      # mm, tool frame
    row = []
    for name, (i, j), flip in (("side: x (closing) vs z (approach)", (0, 2), True), ("front: y vs z", (1, 2), True), ("bottom: x vs y", (0, 1), False)):
        img = np.full((H, W, 3), 255, np.uint8)
        cx, cy = W // 2, (H - 70) if flip else H // 2           # side/front: TCP near the bottom, the jaws extend upward (towards the wrist)
        for P, col in ((F, (90, 90, 90)), (Mv, (30, 120, 230))):
            u = (cx + P[:, i] * S / 1000.0).astype(int); v = (cy + P[:, j] * S / 1000.0).astype(int) if flip else (cy - P[:, j] * S / 1000.0).astype(int)
            for du, dv in ((0, 0), (1, 0), (0, 1)):
                okk = (u + du >= 0) & (u + du < W) & (v + dv >= 0) & (v + dv < H)
                img[v[okk] + dv, u[okk] + du] = col
            ok = (u >= 0) & (u < W) & (v >= 0) & (v < H)
            img[v[ok], u[ok]] = col
        for k in range(-20, 21):
            cv2.line(img, (cx + int(k * 10 * S / 1000), 0), (cx + int(k * 10 * S / 1000), H), (235, 235, 235), 1)
            cv2.line(img, (0, cy + int(k * 10 * S / 1000)), (W, cy + int(k * 10 * S / 1000)), (235, 235, 235), 1)
        cv2.drawMarker(img, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 14, 2)
        cv2.putText(img, f"gripper.pos {pos}: {name}", (6, H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
        row.append(img)
    panels.append(np.hstack(row))
out = np.vstack(panels)
cv2.putText(out, "grey = fixed jaw + body, ORANGE = moving jaw, red + = gripper_frame_link; side/front: approach axis points DOWN (towards the object), 10 mm grid", (6, 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
p = os.path.join(HERE, "runs", "e8_gripper", "sim_gripper_views.png")
cv2.imwrite(p, out); print(p)
