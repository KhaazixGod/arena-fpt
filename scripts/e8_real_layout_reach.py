import sys, math
import numpy as np
sys.path.insert(0, "/home/pread/Projects/dir1_tools/cl0")
from cl0.config import load_config
from cl0.kinematics import SO101Kinematics
cfg = load_config("/home/pread/Projects/dir1_tools/arena/configs/arena.toml")
kin = SO101Kinematics(tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
PAN_X = 38.8
zb = -2.4
heights = [zb + cfg.executor.z_grasp_above_belt_mm, zb + cfg.executor.z_grasp_above_belt_mm + cfg.executor.pre_height_mm, zb + cfg.executor.lift_height_mm]
def ok(x, y, yaw):
    for z in heights:
        r = kin.ik([x, y, z], yaw, tilt_deg=90.0)
        if not (r.ok and kin.within_margin(r.q_deg, cfg.robot.joint_margin_deg)):
            return False
    return True
def tang(x, y):
    return math.degrees(math.atan2(y, x - PAN_X)) + 90.0
print("heights", [round(z, 1) for z in heights], "tcp_offset", cfg.robot.tcp_offset_mm)
print("dist from pan axis | tangential: longest pick segment along belt | yaws feasible at y=0 (of 0,30,..150)")
rows = {}
for d in range(60, 381, 20):
    x = PAN_X + d
    ys = np.arange(-300, 301, 10.0)
    f = [ok(x, float(y), tang(x, float(y))) for y in ys]
    best = cur = 0; 
    for v in f:
        cur = cur + 1 if v else 0; best = max(best, cur)
    seg = max(0, (best - 1) * 10)
    n = sum(ok(x, 0.0, float(a)) for a in range(0, 180, 30))
    rows[d] = seg
    print(f"{d:4d} mm  segment {seg:4d} mm  yaws ok {n}/6")
print("\nnear edge of a 200 mm belt at distance e from the pan axis: common segment across the width (tangential grasp, 20 mm rows)")
for e in (40, 60, 80, 100, 120, 140, 160, 180):
    v = [rows.get(e + k, 0) for k in range(0, 201, 20)]
    print(f" e={e:3d} mm: far edge {e + 200} mm; min segment over width {min(v)} mm; per row {v}")
# camera footprint on the belt plane, straight down
h = 500.0; hf = math.radians(69.4); ar = 720 / 1280
gw = 2 * h * math.tan(hf / 2); gh = gw * ar
print(f"\nD435 colour straight down at {h:.0f} mm: footprint {gw:.0f} x {gh:.0f} mm, {gw / 1280:.3f} mm/px at 1280 wide, {gw / 1920:.3f} at 1920")
