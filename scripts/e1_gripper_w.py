"""E1: gripper gap from the arena USD meshes (fixed jaw vs moving jaw), measured along the closing axis x of gripper_frame_link, by depth z.

Mesh vertices (visual meshes) in the TCP frame: slab |y| < 6 mm, depth bins along z (approach axis).  This is an ESTIMATE from geometry [uoc luong];
contact-level width (pad shape, compliance) is checked by ORACLE grasps in E4.  gripper.pos 0..100 maps linearly to the joint -10..100 deg (scene.toml).
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 320, "height": 240})
import omni.usd, omni.timeline
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface
from pxr import Usd, UsdGeom
from arena import scene as S
ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg)
for _ in range(5): app.update()
omni.timeline.get_timeline_interface().play()
for _ in range(10): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root); links = list(art.shared_metatype.link_names); i_tcp = links.index("gripper_frame_link")
phx = get_physx_interface(); idx0 = np.array([0], np.int32)
r = cfg["robot"]
gl = [p for p in Usd.PrimRange(stage.GetPrimAtPath(paths.robot_root)) if p.GetName() == "gripper_link"][0]


def world_pts(prim):
    m = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())).T      # row-vector -> column convention
    pts = np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get(), float)
    return (m[:3, :3] @ pts.T).T + m[:3, 3]


def quat_to_R(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


out = {"engine": "isaac", "note": "estimate from visual meshes; closing axis x of gripper_frame_link; z = approach axis (negative = back from the frame origin)", "rows": []}
depths = [10, 0, -5, -10, -15, -20, -30, -40]
print("gripper.pos  joint_deg | gap [mm] at depth z (mm) in the TCP frame:  " + "  ".join(f"{d:5d}" for d in depths))
for g in (0, 10, 20, 25, 30, 35, 40, 45, 50, 55, 60):
    jdeg = r["gripper_deg_at_0"] + (r["gripper_deg_at_100"] - r["gripper_deg_at_0"]) * g / 100.0
    q = np.radians(np.array([[0, 0, 0, 0, 0, jdeg]], np.float32))
    art.set_dof_positions(q, idx0); art.set_dof_position_targets(q, idx0); sim.update_articulations_kinematic()
    phx.update_transformations(False, True, False); app.update()
    tf = art.get_link_transforms()[0, i_tcp]; Rt, pt = quat_to_R(tf[3:7]), tf[:3].astype(float)
    fixed = world_pts(stage.GetPrimAtPath(f"{gl.GetPath()}/wrist_roll_follower_so101_v1"))
    moving = world_pts(stage.GetPrimAtPath(f"{gl.GetPath()}/moving_jaw_so101_v1_link/moving_jaw_so101_v1"))
    f, m = (fixed - pt) @ Rt * 1000.0, (moving - pt) @ Rt * 1000.0            # TCP frame, mm
    if False: print(f'  g={g}: fixed x[{f[:,0].min():.0f},{f[:,0].max():.0f}] y[{f[:,1].min():.0f},{f[:,1].max():.0f}] z[{f[:,2].min():.0f},{f[:,2].max():.0f}] | moving x[{m[:,0].min():.0f},{m[:,0].max():.0f}] y[{m[:,1].min():.0f},{m[:,1].max():.0f}] z[{m[:,2].min():.0f},{m[:,2].max():.0f}]', flush=True)
    s = 1.0 if m[:, 0].mean() > f[:, 0].mean() else -1.0
    gaps = []
    for d in depths:
        sf = f[(np.abs(f[:, 1]) < 6) & (np.abs(f[:, 2] - d) < 2.5)]; sm = m[(np.abs(m[:, 1]) < 6) & (np.abs(m[:, 2] - d) < 2.5)]
        gaps.append(None if len(sf) < 5 or len(sm) < 5 else round(float(np.min(s * sm[:, 0]) - np.max(s * sf[:, 0])), 1))   # moving jaw on side s; gap > 0 = open
    out["rows"].append({"gripper_pos": g, "joint_deg": round(jdeg, 1), "closing_sign": s, "depths_mm": depths, "gap_mm": gaps})
    print(f"{g:6d}      {jdeg:6.1f}   | " + "  ".join(f"{x:5.1f}" if x is not None else "   --" for x in gaps), flush=True)
json.dump(out, open(os.path.join(HERE, "runs", "e1", "e1_gripper_gap.json"), "w"), indent=1)
app.close()
