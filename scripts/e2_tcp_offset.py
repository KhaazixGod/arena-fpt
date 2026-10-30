"""E2: where are the two jaws relative to gripper_frame_link (the point CL-0 steers to the object centre)?  Prints, at gripper.pos = 40 (arena gripper_open):
inner face of the fixed jaw, inner face of the moving jaw (x = closing axis in the TCP frame), their midpoint = the offset CL-0's robot.tcp_offset_mm should carry,
plus y and z extents (jaw tip depth).  Visual meshes (estimate [uoc luong]).  Simulation only.   ~/env_isaac/bin/python arena/scripts/e2_tcp_offset.py
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 320, "height": 240})
import omni.usd, omni.timeline
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface, get_physx_simulation_interface
from pxr import Usd, UsdGeom
from arena import scene as S
ctx = omni.usd.get_context(); ctx.new_stage(); stage = ctx.get_stage()
cfg = S.load_scene_cfg(); paths = S.build_scene(stage, cfg)
for _ in range(5): app.update()
omni.timeline.get_timeline_interface().play()
for _ in range(10): app.update()
sim = create_simulation_view("numpy", stage_id=ctx.get_stage_id()); sim.set_subspace_roots("/")
art = sim.create_articulation_view(paths.articulation_root); links = list(art.shared_metatype.link_names); i_tcp = links.index("gripper_frame_link")
phx = get_physx_interface(); sim_i = get_physx_simulation_interface(); idx0 = np.array([0], np.int32); r = cfg["robot"]
gl = [p for p in Usd.PrimRange(stage.GetPrimAtPath(paths.robot_root)) if p.GetName() == "gripper_link"][0]
def world_pts(prim):
    m = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())).T
    pts = np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get(), float)
    return (m[:3, :3] @ pts.T).T + m[:3, 3]
def quat_to_R(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
out = []
for g in (0, 20, 40, 60):
    jdeg = r["gripper_deg_at_0"] + (r["gripper_deg_at_100"] - r["gripper_deg_at_0"]) * g / 100.0
    q = np.radians(np.array([[0, 0, 0, 0, 0, jdeg]], np.float32))
    art.set_dof_positions(q, idx0); art.set_dof_position_targets(q, idx0); sim.update_articulations_kinematic()
    sim_i.simulate(1/300, 0.0); sim_i.fetch_results(); phx.update_transformations(False, True, False); app.update()   # app.update only to refresh USD for the mesh read (no stepping needed here)
    tf = art.get_link_transforms()[0, i_tcp]; Rt, pt = quat_to_R(tf[3:7]), tf[:3].astype(float)
    f = (world_pts(stage.GetPrimAtPath(f"{gl.GetPath()}/wrist_roll_follower_so101_v1")) - pt) @ Rt * 1000.0
    m = (world_pts(stage.GetPrimAtPath(f"{gl.GetPath()}/moving_jaw_so101_v1_link/moving_jaw_so101_v1")) - pt) @ Rt * 1000.0
    s = 1.0 if m[:, 0].mean() > f[:, 0].mean() else -1.0
    row = {"gripper_pos": g, "moving_jaw_side": s}
    for d in (5, 0, -5, -10, -15):
        sf = f[(np.abs(f[:, 1]) < 6) & (np.abs(f[:, 2] - d) < 2.5)]; sm = m[(np.abs(m[:, 1]) < 6) & (np.abs(m[:, 2] - d) < 2.5)]
        if len(sf) >= 5 and len(sm) >= 5:
            fi, mi = float(np.max(s * sf[:, 0]) * s), float(np.min(s * sm[:, 0]) * s)      # inner faces (x in the TCP frame)
            row[f"z{d}"] = {"fixed_inner_x": round(fi, 1), "moving_inner_x": round(mi, 1), "gap": round(abs(mi - fi), 1), "mid_x": round((fi + mi) / 2, 1)}
    row["fixed_x_range"] = [round(float(f[:, 0].min()), 1), round(float(f[:, 0].max()), 1)]; row["moving_x_range"] = [round(float(m[:, 0].min()), 1), round(float(m[:, 0].max()), 1)]
    row["fixed_y_range"] = [round(float(f[:, 1].min()), 1), round(float(f[:, 1].max()), 1)]; row["fixed_z_range"] = [round(float(f[:, 2].min()), 1), round(float(f[:, 2].max()), 1)]
    row["moving_z_range"] = [round(float(m[:, 2].min()), 1), round(float(m[:, 2].max()), 1)]
    out.append(row); print(json.dumps(row), flush=True)
json.dump({"engine": "isaac", "rows": out}, open(os.path.join(HERE, "runs", "e2", "tcp_offset.json"), "w"), indent=1)
app.close()
