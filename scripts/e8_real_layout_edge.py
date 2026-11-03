"""Layout check: footprint of the SO-101 base around the pan axis (from the official URDF + STL) and the farthest belt row the gripper can reach, kinematics only."""
import math, os, struct, sys, xml.etree.ElementTree as ET
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "cl0"))
from cl0.config import load_config
from cl0.kinematics import SO101Kinematics
U = os.path.join(HERE, "assets", "so101_src")
root = ET.parse(os.path.join(U, "so101_new_calib.urdf")).getroot()
def T(xyz, rpy):
    r, p, y = rpy
    Rx = np.array([[1,0,0],[0,math.cos(r),-math.sin(r)],[0,math.sin(r),math.cos(r)]]); Ry = np.array([[math.cos(p),0,math.sin(p)],[0,1,0],[-math.sin(p),0,math.cos(p)]]); Rz = np.array([[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]])
    M = np.eye(4); M[:3,:3] = Rz@Ry@Rx; M[:3,3] = xyz; return M
pts = []
for v in root.find("link[@name='base_link']").findall("visual"):
    o = v.find("origin"); fn = v.find("geometry/mesh").get("filename")
    d = open(os.path.join(U, fn), "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    P = np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n","<f4",3),("v","<f4",(3,3)),("a","<u2")]))["v"].reshape(-1,3).astype(float)
    M = T([float(x) for x in o.get("xyz").split()], [float(x) for x in o.get("rpy").split()])
    Q = (M[:3,:3]@P.T).T + M[:3,3]; pts.append(Q); print(os.path.basename(fn), "x", np.round(Q[:,0].min()*1e3,1), np.round(Q[:,0].max()*1e3,1), "y", np.round(Q[:,1].min()*1e3,1), np.round(Q[:,1].max()*1e3,1))
A = np.vstack(pts)*1e3; PAN = 38.8
print(f"base footprint in W: x {A[:,0].min():.1f}..{A[:,0].max():.1f}, y {A[:,1].min():.1f}..{A[:,1].max():.1f}; pan axis x = {PAN}: {PAN-A[:,0].min():.1f} mm behind, {A[:,0].max()-PAN:.1f} mm in front")
cfg = load_config(os.path.join(HERE, "configs", "arena.toml"))
for off in ((-29.0,0,0),):
    kin = SO101Kinematics(tcp_offset_mm=off, margin_deg=cfg.robot.joint_margin_deg)
    for zname, z in (("grasp only, TCP 10 mm above belt", 7.6), ("lift to 30 mm", 27.6), ("lift to 60 mm (CL-0 default)", 57.6)):
        far = {}
        for yaw_name, yaw in (("tangential", 90.0), ("radial", 0.0)):
            best = None
            for d in range(60, 340, 2):
                r = kin.ik([PAN + d, 0.0, z], yaw, tilt_deg=90.0)
                if r.ok and kin.within_margin(r.q_deg, cfg.robot.joint_margin_deg): best = d
            far[yaw_name] = best
        print(f"{zname}: farthest reachable distance from the pan axis, straight ahead: {far} mm")
