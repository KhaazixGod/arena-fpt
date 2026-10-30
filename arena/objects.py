"""Pick-able objects of the arena: a POOL of rigid bodies created once, parked on a shelf, and moved onto the belt per trial.

Why a pool: PhysX tensor views are bound to the prims that exist when the view is created; creating/deleting bodies per trial would need new views and a
physics re-parse.  Parked bodies sit on a static shelf outside the camera view.

E2 uses the INTERIM primitives below (boxes, cylinders; bright colours that contrast with the dark belt).  They are a stand-in so CL-0 can run end to end;
the diverse object set (meshes, hard types, DEV/TEST split) is E5 and needs the user's go-ahead before any download.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import scene as S


@dataclass(frozen=True)
class Part:
    """One collider of a compound object: "box" (x, y, z mm) or "cyl" (diameter, height mm), centred at pos_mm in the object frame, yawed by yaw_deg."""
    shape: str
    dims_mm: Tuple[float, ...]
    pos_mm: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw_deg: float = 0.0

    @property
    def half_h(self) -> float:
        return 0.5 * (self.dims_mm[2] if self.shape == "box" else self.dims_mm[1])

    def corners_xy(self) -> List[Tuple[float, float]]:
        if self.shape == "cyl":
            r = self.dims_mm[0] / 2.0
            return [(self.pos_mm[0] + r * math.cos(k * math.pi / 8), self.pos_mm[1] + r * math.sin(k * math.pi / 8)) for k in range(16)]
        c, s = math.cos(math.radians(self.yaw_deg)), math.sin(math.radians(self.yaw_deg))
        hx, hy = self.dims_mm[0] / 2.0, self.dims_mm[1] / 2.0
        return [(self.pos_mm[0] + c * x - s * y, self.pos_mm[1] + s * x + c * y) for x, y in ((hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy))]

    def volume_cm3(self) -> float:
        if self.shape == "cyl":
            return math.pi * (self.dims_mm[0] / 2.0) ** 2 * self.dims_mm[1] / 1000.0
        return self.dims_mm[0] * self.dims_mm[1] * self.dims_mm[2] / 1000.0


@dataclass(frozen=True)
class ObjSpec:
    name: str
    shape: str                       # "box" (x, y, z in mm; long axis = x) | "cyl" (diameter, height) | "compound" (parts)
    dims_mm: Tuple[float, ...]
    color: Tuple[float, float, float]
    mass_g: float
    mu: float = 0.8                  # [default, not measured] static = dynamic friction against the belt/jaws (PhysX averages the pair)
    parts: Tuple[Part, ...] = ()     # compound only; the object frame origin = centre of its bounding box
    grasp: Tuple[float, ...] = ()    # compound only: (gx, gy, closing_axis_deg, width_mm) of a good top-down grasp in the object frame (used by ORACLE)
    category: str = ""
    hard_type: str = ""              # "" | "concave" (handle / hollow / L-U shapes) | "thin" | "lowcon" (low contrast with the belt)
    split: str = ""

    @property
    def height_mm(self) -> float:
        if self.shape == "compound":
            return max(p.pos_mm[2] + p.half_h for p in self.parts) - min(p.pos_mm[2] - p.half_h for p in self.parts)
        return self.dims_mm[2] if self.shape == "box" else self.dims_mm[1]

    @property
    def footprint_radius_mm(self) -> float:
        if self.shape == "compound":
            return max(math.hypot(x, y) for p in self.parts for x, y in p.corners_xy())
        if self.shape == "box":
            return 0.5 * math.hypot(self.dims_mm[0], self.dims_mm[1])
        return 0.5 * self.dims_mm[0]

    @property
    def min_width_mm(self) -> float:
        if self.shape == "compound":
            return self.grasp[3]
        return min(self.dims_mm[0], self.dims_mm[1]) if self.shape == "box" else self.dims_mm[0]


INTERIM_SPECS: List[ObjSpec] = [
    ObjSpec("cube35", "box", (35.0, 35.0, 25.0), (0.85, 0.12, 0.10), 30.0),
    ObjSpec("cyl35", "cyl", (35.0, 30.0), (0.10, 0.25, 0.85), 35.0),
    ObjSpec("bar50x25", "box", (50.0, 25.0, 22.0), (0.95, 0.85, 0.10), 30.0),
    ObjSpec("cyl28", "cyl", (28.0, 40.0), (0.12, 0.65, 0.20), 30.0),
    ObjSpec("flat45x30", "box", (45.0, 30.0, 14.0), (0.95, 0.50, 0.05), 20.0),
    ObjSpec("disc45", "cyl", (45.0, 16.0), (0.92, 0.92, 0.92), 20.0),
]
CALIB_PLATE = ObjSpec("calib_plate", "box", (30.0, 30.0, 1.5), (0.85, 0.12, 0.10), 3.0, 1.0)   # thin flat marker for calib_from_scene (never an arrangement object)

POOL_ROOT = "/World/Objects"


def parking_xy_mm(i: int, cfg: dict) -> Tuple[float, float]:
    """Slot i of an 8 x 8 grid (100 mm pitch) on the parking shelf."""
    pk = cfg["parking"]
    col, row = divmod(i, 8)
    x = pk["x_max_mm"] - 60.0 - 100.0 * col
    y = -pk["half_width_mm"] + 60.0 + 100.0 * row
    if x < pk["x_min_mm"] + 40.0:
        raise ValueError(f"parking shelf full at object {i}")
    return x, y


def build_pool(stage, specs: List[ObjSpec], cfg: dict) -> Dict[str, str]:
    """Create the parking shelf and one dynamic body per spec; returns {name: prim path}.  Positions are set at runtime through the tensor view."""
    from pxr import Gf, UsdGeom, UsdPhysics

    pk = cfg["parking"]
    S._box(stage, "/World/ParkingShelf",
           (S.mm(pk["x_max_mm"] - pk["x_min_mm"]), S.mm(2 * pk["half_width_mm"]), S.mm(40.0)),
           (S.mm(0.5 * (pk["x_min_mm"] + pk["x_max_mm"])), 0.0, S.mm(cfg["table"]["top_z_mm"] - 20.0)), color=(0.4, 0.4, 0.4))
    UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath("/World/ParkingShelf"))
    UsdGeom.Xform.Define(stage, POOL_ROOT)
    paths: Dict[str, str] = {}
    oc = cfg.get("objects", {})
    depen = float(oc.get("max_depenetration_m_s", 0.0))
    iters = (int(oc.get("solver_pos_iters", 0)), int(oc.get("solver_vel_iters", 0)))
    tpr = float(oc.get("torsional_patch_radius_mm", 0.0))
    for i, sp in enumerate(specs):
        path = f"{POOL_ROOT}/{sp.name}"
        if sp.shape == "compound":
            _build_compound(stage, path, sp, depen, iters, tpr)
            paths[sp.name] = path
            continue
        if sp.shape == "box":
            prim = S._box(stage, path, tuple(S.mm(d) for d in sp.dims_mm), (0.0, 0.0, 0.0), color=sp.color)
        elif sp.shape == "cyl":
            cyl = UsdGeom.Cylinder.Define(stage, path)
            cyl.GetRadiusAttr().Set(S.mm(sp.dims_mm[0] / 2.0))
            cyl.GetHeightAttr().Set(S.mm(sp.dims_mm[1]))
            cyl.GetAxisAttr().Set(UsdGeom.Tokens.z)
            cyl.CreateDisplayColorAttr([tuple(sp.color)])
            prim = cyl.GetPrim()
        else:
            raise ValueError(sp.shape)
        S.make_dynamic(prim, sp.mass_g * 1e-3, max_depen_m_s=depen, pos_iters=iters[0], vel_iters=iters[1])
        S.bind_physics_material(prim, S._physics_material(stage, f"/World/Looks/Phys_{sp.name}", sp.mu, sp.mu))
        if tpr > 0.0:
            S.set_torsional_patch(prim, tpr)
        paths[sp.name] = path
    return paths


def _build_compound(stage, path: str, sp: ObjSpec, max_depen_m_s: float, iters=(0, 0), tpr: float = 0.0) -> None:
    """One rigid body (an Xform) whose children are primitive colliders: exact PhysX shapes, no convex decomposition needed for concave objects."""
    from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
    root = UsdGeom.Xform.Define(stage, path).GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(root)
    UsdPhysics.MassAPI.Apply(root).CreateMassAttr(sp.mass_g * 1e-3)
    rba = PhysxSchema.PhysxRigidBodyAPI.Apply(root)
    rba.CreateSleepThresholdAttr(0.0)
    if max_depen_m_s > 0.0:
        rba.CreateMaxDepenetrationVelocityAttr(max_depen_m_s)
    if iters[0] > 0:
        rba.CreateSolverPositionIterationCountAttr(int(iters[0]))
    if iters[1] > 0:
        rba.CreateSolverVelocityIterationCountAttr(int(iters[1]))
    mat = S._physics_material(stage, f"/World/Looks/Phys_{sp.name}", sp.mu, sp.mu)
    for j, p in enumerate(sp.parts):
        cp = f"{path}/p{j}"
        if p.shape == "box":
            g = UsdGeom.Cube.Define(stage, cp)
            g.GetSizeAttr().Set(1.0)
            x = UsdGeom.XformCommonAPI(g)
            x.SetScale(Gf.Vec3f(*[S.mm(d) for d in p.dims_mm]))
        else:
            g = UsdGeom.Cylinder.Define(stage, cp)
            g.GetRadiusAttr().Set(S.mm(p.dims_mm[0] / 2.0))
            g.GetHeightAttr().Set(S.mm(p.dims_mm[1]))
            g.GetAxisAttr().Set(UsdGeom.Tokens.z)
            x = UsdGeom.XformCommonAPI(g)
        x.SetTranslate(Gf.Vec3d(*[S.mm(c) for c in p.pos_mm]))
        x.SetRotate(Gf.Vec3f(0.0, 0.0, p.yaw_deg))
        g.CreateDisplayColorAttr([tuple(sp.color)])
        UsdPhysics.CollisionAPI.Apply(g.GetPrim())
        S.bind_physics_material(g.GetPrim(), mat)
        if tpr > 0.0:
            S.set_torsional_patch(g.GetPrim(), tpr)
