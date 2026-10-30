"""E2: what do the PhysX collision shapes (convex hulls, scene USD physics:approximation = convexHull) of the two jaws occupy, in the TCP frame at gripper.pos = 40?
Cross-section at y = 0: for depth z (approach axis; + = beyond the frame origin), the x-interval occupied by each jaw's hull.  Simulation only."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, HERE)
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 320, "height": 240})
import omni.usd, omni.timeline
from omni.physics.tensors import create_simulation_view
from omni.physx import get_physx_interface, get_physx_simulation_interface
from pxr import Usd, UsdGeom, UsdPhysics
from scipy.spatial import ConvexHull
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
# which collision prims belong to the gripper?
for p in Usd.PrimRange(gl):
    if p.HasAPI(UsdPhysics.CollisionAPI): print("collision prim:", p.GetPath(), p.GetTypeName(), flush=True)
def world_pts(prim):
    m = np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())).T
    pts = np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get(), float)
    return (m[:3, :3] @ pts.T).T + m[:3, 3]
def quat_to_R(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
g = 40; jdeg = r["gripper_deg_at_0"] + (r["gripper_deg_at_100"] - r["gripper_deg_at_0"]) * g / 100.0
q = np.radians(np.array([[0, 0, 0, 0, 0, jdeg]], np.float32))
art.set_dof_positions(q, idx0); art.set_dof_position_targets(q, idx0); sim.update_articulations_kinematic()
sim_i.simulate(1/300, 0.0); sim_i.fetch_results(); phx.update_transformations(False, True, False); app.update()
tf = art.get_link_transforms()[0, i_tcp]; Rt, pt = quat_to_R(tf[3:7]), tf[:3].astype(float)
jaws = {"fixed": f"{gl.GetPath()}/wrist_roll_follower_so101_v1", "moving": f"{gl.GetPath()}/moving_jaw_so101_v1_link/moving_jaw_so101_v1"}
res = {}
for name, path in jaws.items():
    P = (world_pts(stage.GetPrimAtPath(path)) - pt) @ Rt * 1000.0
    H = ConvexHull(P); A, b = H.equations[:, :3], H.equations[:, 3]
    rows = []
    for z in (6, 3, 0, -3, -6, -10, -15, -20, -30):
        xs = np.arange(-90, 60, 0.5)
        inside = np.array([np.all(A @ np.array([x, 0.0, z]) + b <= 1e-9) for x in xs])
        if inside.any():
            # contiguous intervals
            idx = np.nonzero(inside)[0]; cuts = np.nonzero(np.diff(idx) > 1)[0]
            segs = np.split(idx, cuts + 1); rows.append({"z": z, "x_intervals": [[float(xs[s[0]]), float(xs[s[-1]])] for s in segs]})
        else:
            rows.append({"z": z, "x_intervals": []})
    res[name] = rows
    print(name, "hull volume %.0f mm3, z range [%.1f, %.1f]" % (H.volume, P[:, 2].min(), P[:, 2].max()), flush=True)
    for rw in rows: print("   z=%4d  x occupied: %s" % (rw["z"], rw["x_intervals"]), flush=True)
json.dump({"engine": "isaac", "gripper_pos": g, "frame": "gripper_frame_link, x = closing axis, z = approach", "hull_cross_section_y0": res}, open(os.path.join(HERE, "runs", "e2", "jaw_hull.json"), "w"), indent=1)
app.close()
