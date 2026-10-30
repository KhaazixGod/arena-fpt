"""IsaacWorld: the arena's Isaac Sim scene, PhysX stepping, camera render and ground-truth access.  Create ``SimulationApp`` first.

Rules learned in E0-E2 (29/10) and kept here:
  * never call ``app.update()`` inside the loop: with the timeline playing it adds physics steps (GT travel 292 mm instead of 195 mm in e2_render_lag2);
  * physics advances ONLY through ``simulate(dt, t)`` + ``fetch_results()``; the renderer (Fabric) follows PhysX after such a step, NOT after a bare joint
    teleport -> every teleport is followed by one step before rendering;
  * ``update_transformations(False, True, False)`` + ``rep.orchestrator.step(rt_subframes=1, delta_time=0.0)`` gives an image of the CURRENT state
    (measured lag 0.0015 s, e2_render_lag2.json).
Ground truth (object poses, TCP, belt displacement) is read through methods named ``gt_*``; the Platform handed to CL-0 never exposes them.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np

from . import belt as B
from . import scene as S
from .objects import POOL_ROOT, ObjSpec, build_pool, parking_xy_mm


class SimFault(RuntimeError):
    """A fault of the SIMULATION (NaN, crash-like state, lost sync): the trial is valid=0 (arena/CLAUDE.md rule 7), never a method failure."""


def _yaw_from_quat(q) -> float:
    x, y, z, w = (float(c) for c in q)
    return math.degrees(math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)))


class IsaacWorld:
    def __init__(self, app, specs: List[ObjSpec], cfg: Optional[dict] = None, debug_cam: bool = False, depth: bool = False):
        import omni.replicator.core as rep
        import omni.timeline
        import omni.usd
        from omni.physx import get_physx_interface, get_physx_simulation_interface

        self.app = app
        self.cfg = cfg or S.load_scene_cfg()
        c = self.cfg
        ctx = omni.usd.get_context()
        ctx.new_stage()
        self.stage = ctx.get_stage()
        self.paths = S.build_scene(self.stage, c)
        self.specs = list(specs)
        self.pool = build_pool(self.stage, self.specs, c)
        self.spec_by_name = {s.name: s for s in self.specs}
        self.u, self.v = S.belt_axes(c["belt"]["dir_deg"])
        self.belt_top_mm = float(c["belt"]["z_mm"])
        self.hz = float(c["physics"]["hz"])
        self.dt = 1.0 / self.hz
        self.k = 0                                  # global physics step counter
        self._belt_v = None

        self._cam_wh = (int(c["camera"]["width"]), int(c["camera"]["height"]))
        self._rp = rep.create.render_product(self.paths.camera, self._cam_wh)
        self._rgb = rep.AnnotatorRegistry.get_annotator("rgb")
        self._rgb.attach([self._rp])
        self.depth_enabled = bool(depth)
        self._depth_ann, self._last_depth = None, None
        if depth:                                    # ideal depth along the optical axis (the D435i has depth; CL-0 does not use it, other methods may)
            self._depth_ann = rep.AnnotatorRegistry.get_annotator("distance_to_image_plane")
            self._depth_ann.attach([self._rp])
        self._dbg_rgb = None
        if debug_cam:
            self._dbg_rgb = self._make_debug_cam(rep)
        for _ in range(5):
            app.update()
        omni.timeline.get_timeline_interface().play()
        for _ in range(30):                         # shaders/textures stream in; the timeline is already playing, so these may step physics: reset_state() follows
            app.update()
        self._stage_id = ctx.get_stage_id()
        self._make_views()
        self._phx = get_physx_interface()
        self._sim_i = get_physx_simulation_interface()
        self._rep = rep
        self._idx0 = np.array([0], np.int32)
        self._idx_all = np.arange(len(self._obj_names), dtype=np.int32)
        r = c["robot"]
        self._g0, self._g100 = float(r["gripper_deg_at_0"]), float(r["gripper_deg_at_100"])

    def _make_views(self) -> None:
        from omni.physics.tensors import create_simulation_view
        sim = create_simulation_view("numpy", stage_id=self._stage_id)
        sim.set_subspace_roots("/")
        self._sim = sim
        self._art = sim.create_articulation_view(self.paths.articulation_root)
        names = list(self._art.shared_metatype.dof_names)
        if names != list(S.ALL_JOINTS):
            raise SimFault(f"unexpected dof order {names}")
        self._links = list(self._art.shared_metatype.link_names)
        self._tcp_i = self._links.index("gripper_frame_link")
        self._rb = sim.create_rigid_body_view(f"{POOL_ROOT}/*")
        self._obj_names = [p.rsplit("/", 1)[1] for p in self._rb.prim_paths]
        self._obj_i = {n: i for i, n in enumerate(self._obj_names)}

    def hard_reset(self, warm_updates: int = 3) -> None:
        """Stop and replay the timeline: PhysX rebuilds its scene from USD, so a trial no longer inherits solver/contact state from the previous one
        (E2: the same trial gave different results depending on the trial before it).  The views are recreated; the caller then teleports and places
        everything as usual.  The fixed number of app.update() calls keeps it deterministic [checked by the M8 runs, not assumed]."""
        import omni.timeline
        tl = omni.timeline.get_timeline_interface()
        tl.stop()
        self.app.update()
        tl.play()
        for _ in range(warm_updates):
            self.app.update()
        self._make_views()
        self._belt_v = None
        self.set_belt_speed(0.0)

    # ------------------------------------------------------------------ debug camera (oblique, only for videos humans watch)
    def _make_debug_cam(self, rep):
        from pxr import Gf, UsdGeom
        cam = UsdGeom.Camera.Define(self.stage, "/World/DebugCam")
        cam.GetFocalLengthAttr().Set(14.0)
        cam.GetHorizontalApertureAttr().Set(20.955)
        cam.GetVerticalApertureAttr().Set(20.955 * 720 / 1280)
        cam.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 20.0))
        pos = np.array([0.52, -0.30, 0.26]); tgt = np.array([0.19, 0.0, 0.02])
        f = tgt - pos; f /= np.linalg.norm(f)
        right = np.cross(f, [0, 0, 1.0]); right /= np.linalg.norm(right)
        up = np.cross(right, f)
        m = Gf.Matrix4d(right[0], right[1], right[2], 0, up[0], up[1], up[2], 0, -f[0], -f[1], -f[2], 0, pos[0], pos[1], pos[2], 1)
        UsdGeom.Xformable(cam).AddTransformOp().Set(m)
        rp = rep.create.render_product("/World/DebugCam", (1280, 720))
        ann = rep.AnnotatorRegistry.get_annotator("rgb")
        ann.attach([rp])
        return ann

    # ------------------------------------------------------------------ time
    @property
    def t(self) -> float:
        return self.k * self.dt

    def step(self) -> None:
        self._sim_i.simulate(self.dt, self.t)
        self._sim_i.fetch_results()
        self.k += 1

    def step_seconds(self, seconds: float) -> None:
        for _ in range(int(round(seconds * self.hz))):
            self.step()

    # ------------------------------------------------------------------ belt (physical surface velocity)
    def set_belt_speed(self, v_mm_s: float) -> None:
        if self._belt_v is not None and abs(v_mm_s - self._belt_v) < 1e-9:
            return
        B.set_speed(self.stage, self.paths.belt, self.cfg["belt"]["dir_deg"], v_mm_s)
        self._sim_i.flush_changes()
        self._belt_v = v_mm_s

    # ------------------------------------------------------------------ arm
    def grip_pos_to_deg(self, pos: float) -> float:
        return self._g0 + (self._g100 - self._g0) * float(pos) / 100.0

    def grip_deg_to_pos(self, deg: float) -> float:
        return 100.0 * (float(deg) - self._g0) / (self._g100 - self._g0)

    def joint_deg(self) -> np.ndarray:
        """(6,) measured joint angles in degrees (5 arm joints, then the URDF gripper joint)."""
        return np.degrees(self._art.get_dof_positions()[0].astype(float))

    def set_targets(self, q5_deg, grip_pos: Optional[float]) -> None:
        cur = self._art.get_dof_position_targets()[0].astype(float)
        if q5_deg is not None:
            cur[:5] = np.radians(np.asarray(q5_deg, float))
        if grip_pos is not None:
            cur[5] = math.radians(self.grip_pos_to_deg(grip_pos))
        self._art.set_dof_position_targets(cur.astype(np.float32)[None, :], self._idx0)

    def teleport_arm(self, q5_deg, grip_pos: float) -> None:
        q = np.radians(np.r_[np.asarray(q5_deg, float), self.grip_pos_to_deg(grip_pos)]).astype(np.float32)[None, :]
        self._art.set_dof_positions(q, self._idx0)
        self._art.set_dof_velocities(np.zeros((1, 6), np.float32), self._idx0)
        self._art.set_dof_position_targets(q, self._idx0)
        self._sim.update_articulations_kinematic()

    def gt_tcp_mm(self) -> np.ndarray:
        """Position (mm) of gripper_frame_link (the URDF frame, ON the fixed jaw; the grasp centre is this + R @ tcp_offset)."""
        return self._art.get_link_transforms()[0, self._tcp_i, :3].astype(float) * 1000.0

    def gt_tcp_pose(self):
        """(position mm, rotation 3x3) of gripper_frame_link; x = closing axis, z = approach axis."""
        tf = self._art.get_link_transforms()[0, self._tcp_i].astype(float)
        x, y, z, w = tf[3:7]
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        return tf[:3] * 1000.0, R

    # ------------------------------------------------------------------ objects
    def _pose_row(self, x_mm, y_mm, z_mm, yaw_deg):
        h = math.radians(yaw_deg) / 2.0
        return [x_mm * 1e-3, y_mm * 1e-3, z_mm * 1e-3, 0.0, 0.0, math.sin(h), math.cos(h)]

    def park_all(self) -> None:
        rows = np.zeros((len(self._obj_names), 7), np.float32)
        for i, n in enumerate(self._obj_names):
            x, y = parking_xy_mm(i, self.cfg)
            rows[i] = self._pose_row(x, y, self.cfg["table"]["top_z_mm"] + self.spec_by_name[n].height_mm / 2 + 0.5, 0.0)
        self._rb.set_transforms(rows, self._idx_all)
        self._rb.set_velocities(np.zeros((len(self._obj_names), 6), np.float32), self._idx_all)

    def place(self, placements: List[dict]) -> None:
        """placements: [{"name", "a_mm", "b_mm", "yaw_deg"}], a/b in the belt frame (W origin), yaw relative to the belt direction (CCW)."""
        phi = self.cfg["belt"]["dir_deg"]
        idx, rows = [], []
        for p in placements:
            sp = self.spec_by_name[p["name"]]
            x = p["a_mm"] * self.u[0] + p["b_mm"] * self.v[0]
            y = p["a_mm"] * self.u[1] + p["b_mm"] * self.v[1]
            idx.append(self._obj_i[p["name"]])
            rows.append(self._pose_row(x, y, self.belt_top_mm + sp.height_mm / 2.0 + 0.3, phi + p.get("yaw_deg", 0.0)))
        if idx:
            idx = np.array(idx, np.int32)
            full = self._rb.get_transforms().astype(np.float32)            # the tensor API wants the FULL (count, 7) array and the indices to write
            full[idx] = np.array(rows, np.float32)
            self._rb.set_transforms(full, idx)
            self._rb.set_velocities(np.zeros((len(self._obj_names), 6), np.float32), idx)

    def gt_objects(self) -> Dict[str, dict]:
        """Ground truth: {name: {"pos_mm": (3,), "yaw_deg": float, "a_mm", "b_mm"}} for every pool body (parked ones included)."""
        tf = self._rb.get_transforms().astype(float)
        out = {}
        for n, i in self._obj_i.items():
            p = tf[i, :3] * 1000.0
            out[n] = {"pos_mm": p, "yaw_deg": _yaw_from_quat(tf[i, 3:7]),
                      "a_mm": float(p[0] * self.u[0] + p[1] * self.u[1]), "b_mm": float(p[0] * self.v[0] + p[1] * self.v[1])}
        return out

    def finite(self) -> bool:
        return bool(np.all(np.isfinite(self._art.get_dof_positions())) and np.all(np.isfinite(self._art.get_dof_velocities()))
                    and np.all(np.isfinite(self._rb.get_transforms())))

    # ------------------------------------------------------------------ camera
    def _grab(self, ann) -> np.ndarray:
        self._phx.update_transformations(False, True, False)
        self._rep.orchestrator.step(rt_subframes=1, delta_time=0.0, pause_timeline=False)
        img = np.asarray(ann.get_data())
        if img.ndim != 3 or img.shape[0] != self._cam_wh[1] and ann is self._rgb:
            raise SimFault(f"empty/odd camera frame {img.shape}")
        return np.ascontiguousarray(img[..., :3][..., ::-1])               # RGB -> BGR (what CL-0 expects)

    def render_bgr(self) -> np.ndarray:
        img = self._grab(self._rgb)
        if self._depth_ann is not None:                  # same orchestrator step as the colour image
            d = np.asarray(self._depth_ann.get_data(), np.float32)
            self._last_depth = (d.reshape(d.shape[0], d.shape[1]) * 1000.0) if d.ndim >= 2 else None
        return img

    def last_depth_mm(self) -> Optional[np.ndarray]:
        return self._last_depth

    def render_debug_bgr(self) -> np.ndarray:
        return self._grab(self._dbg_rgb)
