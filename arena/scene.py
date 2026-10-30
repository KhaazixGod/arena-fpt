"""Isaac Sim scene for the arena: SO-101 (USD converted from the official URDF), table, belt, fixed camera.

Everything here runs INSIDE Isaac's Python after ``SimulationApp(...)`` exists. Units: the TOML is mm/deg (CL-0's), USD is metres/deg.
The world frame is CL-0's W (the arm's base_link), z up. Belt: u = (cos phi, sin phi), v = (-sin phi, cos phi) (left of travel).
"""
from __future__ import annotations

import math
import os
import tomllib
from dataclasses import dataclass

ARENA_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM_JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")
ALL_JOINTS = ARM_JOINTS + ("gripper",)


def load_scene_cfg(path: str | None = None) -> dict:
    with open(path or os.path.join(ARENA_ROOT, "configs", "scene.toml"), "rb") as f:
        return tomllib.load(f)


def mm(x: float) -> float:
    return x * 1e-3


@dataclass
class ScenePaths:
    robot_root: str
    articulation_root: str
    belt: str
    camera: str
    table: str
    joints: dict          # joint name -> USD joint prim path


def _box(stage, path, size_m, center_m, yaw_deg=0.0, color=(0.5, 0.5, 0.5)):
    from pxr import Gf, UsdGeom
    cube = UsdGeom.Cube.Define(stage, path)
    cube.GetSizeAttr().Set(1.0)
    cube.CreateDisplayColorAttr([tuple(color)])
    x = UsdGeom.XformCommonAPI(cube)
    x.SetScale(Gf.Vec3f(*size_m))
    x.SetTranslate(Gf.Vec3d(*center_m))
    x.SetRotate(Gf.Vec3f(0.0, 0.0, yaw_deg))
    return cube.GetPrim()


def _physics_material(stage, path, static_f, dynamic_f, restitution=0.0):
    from pxr import UsdPhysics, UsdShade
    mat = UsdShade.Material.Define(stage, path)
    m = UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
    m.CreateStaticFrictionAttr(static_f)
    m.CreateDynamicFrictionAttr(dynamic_f)
    m.CreateRestitutionAttr(restitution)
    return mat


def bind_physics_material(prim, mat):
    from pxr import UsdShade
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat, UsdShade.Tokens.weakerThanDescendants, "physics")


def make_dynamic(prim, mass_kg: float, static_f: float = 0.8, dynamic_f: float = 0.8, max_depen_m_s: float = 0.0, pos_iters: int = 0, vel_iters: int = 0):
    """Rigid body that never sleeps: a resting body on a stopped belt would otherwise fall asleep and ignore the belt when it starts (E1, 29/10)."""
    from pxr import PhysxSchema, UsdPhysics
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.CollisionAPI.Apply(prim)
    UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(mass_kg)
    rba = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
    rba.CreateSleepThresholdAttr(0.0)
    if max_depen_m_s > 0.0:
        rba.CreateMaxDepenetrationVelocityAttr(max_depen_m_s)       # caps the speed at which overlapping bodies are pushed apart (a jaw squeezing a light object would otherwise launch it)
    if pos_iters > 0:
        rba.CreateSolverPositionIterationCountAttr(int(pos_iters))  # more solver iterations = stiffer, less slipping grasp contacts
    if vel_iters > 0:
        rba.CreateSolverVelocityIterationCountAttr(int(vel_iters))


def set_torsional_patch(prim, radius_mm: float) -> None:
    """Torsional friction for a collider: PhysX models a contact patch of this radius (default 0 = point contact, free spin about the contact normal)."""
    from pxr import PhysxSchema
    api = PhysxSchema.PhysxCollisionAPI.Apply(prim)
    api.CreateTorsionalPatchRadiusAttr().Set(mm(radius_mm))
    api.CreateMinTorsionalPatchRadiusAttr().Set(mm(radius_mm))


def belt_axes(phi_deg: float):
    p = math.radians(phi_deg)
    return (math.cos(p), math.sin(p)), (-math.sin(p), math.cos(p))


def build_scene(stage, cfg: dict) -> ScenePaths:
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdLux, UsdPhysics

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- physics scene
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(9.81)
    px = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    px.CreateTimeStepsPerSecondAttr(float(cfg["physics"]["hz"]))
    px.CreateSolverTypeAttr("TGS")

    # --- light (E0: DomeLight is what lights the scene)
    UsdLux.DomeLight.Define(stage, "/World/Dome").CreateIntensityAttr(float(cfg["light"]["dome_intensity"]))

    # --- table the arm stands on (static)
    t = cfg["table"]
    tx = 0.5 * (t["x_min_mm"] + t["x_max_mm"])
    table = _box(stage, "/World/Table",
                 (mm(t["x_max_mm"] - t["x_min_mm"]), mm(2 * t["half_width_mm"]), mm(t["thickness_mm"])),
                 (mm(tx), 0.0, mm(t["top_z_mm"] - t["thickness_mm"] / 2)), color=(0.55, 0.5, 0.42))
    UsdPhysics.CollisionAPI.Apply(table)
    tmat = _physics_material(stage, "/World/Looks/TablePhys", 0.8, 0.8)
    bind_physics_material(table, tmat)

    # --- belt: kinematic box with a PhysX surface velocity (set at runtime by arena.belt)
    b = cfg["belt"]
    u, v = belt_axes(b["dir_deg"])
    cx = b["center_a_mm"] * u[0] + b["center_b_mm"] * v[0]
    cy = b["center_a_mm"] * u[1] + b["center_b_mm"] * v[1]
    belt = _box(stage, "/World/Belt", (mm(b["length_mm"]), mm(b["width_mm"]), mm(b["thickness_mm"])),
                (mm(cx), mm(cy), mm(b["z_mm"] - b["thickness_mm"] / 2)), yaw_deg=b["dir_deg"], color=b["color"])
    UsdPhysics.CollisionAPI.Apply(belt)
    rb = UsdPhysics.RigidBodyAPI.Apply(belt)
    rb.CreateKinematicEnabledAttr(True)
    sv = PhysxSchema.PhysxSurfaceVelocityAPI.Apply(belt)
    sv.CreateSurfaceVelocityEnabledAttr(True)
    # WORLD-space velocity: the belt box is a unit cube with a non-uniform scale, and a LOCAL-space velocity is multiplied by that scale
    # (E1 debug 29/10: 50 mm/s commanded along a 0.6-scaled axis gave 30 mm/s). arena.belt.set_speed writes the world vector u * v.
    sv.CreateSurfaceVelocityLocalSpaceAttr(False)
    sv.CreateSurfaceVelocityAttr(Gf.Vec3f(0, 0, 0))
    bmat = _physics_material(stage, "/World/Looks/BeltPhys", b["friction"], b["friction"])
    bind_physics_material(belt, bmat)

    # --- robot (reference to the converted USD; base_link at the world origin, root joint fixes it to the world)
    r = cfg["robot"]
    robot = stage.DefinePrim(r["prim"], "Xform")
    usd = r["usd"] if os.path.isabs(r["usd"]) else os.path.join(ARENA_ROOT, r["usd"])
    robot.GetReferences().AddReference(usd)
    root = stage.GetPrimAtPath(r["articulation_root"])
    if not root or not root.HasAPI(UsdPhysics.ArticulationRootAPI):
        raise RuntimeError(f"articulation root not found at {r['articulation_root']}")
    # self-collision off: the converter's output explodes to NaN otherwise (user's note in so101_table_scene.py, 13/10/2026)
    art_api = PhysxSchema.PhysxArticulationAPI.Apply(root)
    art_api.CreateEnabledSelfCollisionsAttr().Set(False)
    if int(r.get("solver_pos_iters", 0)) > 0:
        art_api.CreateSolverPositionIterationCountAttr().Set(int(r["solver_pos_iters"]))
    if int(r.get("solver_vel_iters", 0)) > 0:
        art_api.CreateSolverVelocityIterationCountAttr().Set(int(r["solver_vel_iters"]))
    ga = r.get("gripper_collision", "")
    if ga:
        # The converted USD gives every link ONE convex hull.  For the jaws that fills the gap in a funnel: e2_jaw_hull.json shows the free gap shrinking from 60 mm at the tip
        # to 46 mm 15 mm up and 30 mm at 30 mm, so a 30 mm tall object is wedged and ejected when the jaw closes.  Decompose the gripper meshes into several convex pieces instead.
        from pxr import PhysxSchema as _PS, Usd as _Usd, UsdGeom as _UG
        gl = next(p for p in _Usd.PrimRange(robot) if p.GetName() == "gripper_link")
        for p in _Usd.PrimRange(gl):
            if p.HasAPI(UsdPhysics.CollisionAPI) and p.IsA(_UG.Mesh):
                UsdPhysics.MeshCollisionAPI.Apply(p).CreateApproximationAttr().Set(ga)
                if ga == "convexDecomposition":
                    d = _PS.PhysxConvexDecompositionCollisionAPI.Apply(p)
                    d.CreateMaxConvexHullsAttr().Set(int(r.get("decomp_max_hulls", 32)))
                    d.CreateHullVertexLimitAttr().Set(64)
                    d.CreateVoxelResolutionAttr().Set(int(r.get("decomp_voxel_resolution", 500000)))
                    d.CreateErrorPercentageAttr().Set(float(r.get("decomp_error_pct", 1.0)))
                    d.CreateMinThicknessAttr().Set(0.001)
    pf = float(r.get("pad_friction", 0.0))
    if pf > 0.0:        # [assumption, E8 must check] rubbery gripper pads: one friction material on every robot collision shape
        from pxr import Usd
        pmat = _physics_material(stage, "/World/Looks/RobotPhys", pf, pf)
        for p in Usd.PrimRange(robot):
            if p.HasAPI(UsdPhysics.CollisionAPI):
                bind_physics_material(p, pmat)
    tpr = float(r.get("torsional_patch_radius_mm", 0.0))
    if tpr > 0.0:       # pads have an AREA: PhysX point contacts have no torsional friction otherwise, and a 2-point grasp pivots freely (E4)
        from pxr import Usd
        for p in Usd.PrimRange(robot):
            if p.HasAPI(UsdPhysics.CollisionAPI):
                set_torsional_patch(p, tpr)
    joints = {}
    for name in ALL_JOINTS:
        jp = stage.GetPrimAtPath(f"{r['prim']}/Physics/{name}")
        if not jp:
            raise RuntimeError(f"joint prim missing: {r['prim']}/Physics/{name}")
        d = UsdPhysics.DriveAPI.Apply(jp, "angular")
        d.CreateTypeAttr("force")
        d.CreateStiffnessAttr(float(r["stiffness_nm_per_deg"]))
        d.CreateDampingAttr(float(r["damping_nms_per_deg"]))
        gmax = r.get("gripper_max_force_nm")
        d.CreateMaxForceAttr(float(gmax) if (name == "gripper" and gmax) else float(r["max_force_nm"]))
        gvel = r.get("gripper_max_vel_deg_s")
        if name == "gripper" and gvel:
            PhysxSchema.PhysxJointAPI.Apply(jp).CreateMaxJointVelocityAttr(float(gvel))      # a real servo does not close at the speed of an ideal torque source
        joints[name] = f"{r['prim']}/Physics/{name}"

    # --- camera: above the belt, looking straight down, image right = u (Rz(phi): X_cam = u, Y_cam = v)
    c = cfg["camera"]
    cam = UsdGeom.Camera.Define(stage, "/World/Camera")
    hap = 20.955
    cam.GetHorizontalApertureAttr().Set(hap)
    cam.GetVerticalApertureAttr().Set(hap * c["height"] / c["width"])
    cam.GetFocalLengthAttr().Set(hap / (2.0 * math.tan(math.radians(c["hfov_deg"]) / 2.0)))
    cam.GetClippingRangeAttr().Set(Gf.Vec2f(c["near_m"], c["far_m"]))   # E0: the USD default near plane is 1 m here and clips the belt away
    xf = UsdGeom.XformCommonAPI(cam)
    xf.SetTranslate(Gf.Vec3d(*[mm(x) for x in c["xyz_mm"]]))
    xf.SetRotate(Gf.Vec3f(0.0, 0.0, b["dir_deg"]))

    return ScenePaths(r["prim"], r["articulation_root"], "/World/Belt", "/World/Camera", "/World/Table", joints)


def camera_intrinsics(cfg: dict):
    c = cfg["camera"]
    f_px = (c["width"] / 2.0) / math.tan(math.radians(c["hfov_deg"]) / 2.0)
    return {"fx": f_px, "fy": f_px, "cx": c["width"] / 2.0, "cy": c["height"] / 2.0, "width": c["width"], "height": c["height"]}
