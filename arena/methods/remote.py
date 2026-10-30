"""REMOTE: a method served by arena/remote_server.py from ANOTHER Python environment (lockstep over a local socket).

    run_arena --methods REMOTE --method-arg remote=localhost:6001 [--method-arg remote_authkey=arena]
The name in trials.csv is "REMOTE:<name the server announces>".  The remote method gets exactly what an in-process method gets (frame, the belt's
pulse-counter samples -> identical s_at / speed_at, joint state) and nothing else: never ground truth.  Its compute time + the transfer (~2.7 MB per 1280x720 frame) is what ms/step reports.
"""
from __future__ import annotations

import json
from multiprocessing.connection import Client

import numpy as np

from cl0.types import Command, TrialEvent

from .base import MethodContext, register


def pack_array(a):
    if a is None:
        return None
    a = np.ascontiguousarray(a)
    return {"data": a.tobytes(), "dtype": str(a.dtype), "shape": list(a.shape)}


class RemoteMethod:
    def __init__(self, ctx: MethodContext, addr: str, authkey: str = "arena"):
        host, port = addr.rsplit(":", 1)
        self.conn = Client((host, int(port)), authkey=authkey.encode())
        cfg_d = json.loads(json.dumps(__import__("dataclasses").asdict(ctx.cfg), default=list))
        calib_d = json.loads(ctx.calib.to_json())
        self.conn.send({"image_size": list(ctx.image_size), "control_hz": ctx.control_hz, "calib": calib_d, "cfg": cfg_d,
                        "calib_path": ctx.calib_path, "background_path": ctx.background_path})
        hello = self.conn.recv()
        self.method_name = f"REMOTE:{hello.get('name', addr)}"
        self.finished, self.outcome, self.events, self.log, self.diag, self.phase = False, "", [], [], {}, ""

    def _new_hist(self, belt) -> list:
        """Counter samples received since the previous call (the server rebuilds the belt readout with cl0's own algorithm)."""
        if not hasattr(belt, "history"):
            return []
        th, sh = belt.history()
        if len(th) and (not len(self._sent_t) or th[0] != self._sent_t[0]):      # a new trial (new Belt object)
            self._n_sent = 0
        out = [[float(a), float(b)] for a, b in zip(th[self._n_sent:], sh[self._n_sent:])]
        self._n_sent = len(th)
        self._sent_t = th[:1]
        return out

    def reset(self, t0, state) -> None:
        self._n_sent, self._sent_t = 0, []
        self.conn.send({"op": "reset", "t0": t0, "state": None if state is None else {"q_deg": [float(x) for x in state.q_deg], "gripper": float(state.gripper), "t": float(state.t)}})
        self.conn.recv()
        self.finished, self.outcome, self.events, self.log, self.diag, self.phase = False, "", [], [], {}, ""

    def step(self, t, frame, belt, state) -> Command:
        fr = None
        if frame is not None:
            fr = {"img": pack_array(frame.img), "t_capture": float(frame.t_capture), "depth": pack_array(getattr(frame, "depth_mm", None))}
        self.conn.send({"op": "step", "t": t, "state": {"q_deg": [float(x) for x in state.q_deg], "gripper": float(state.gripper), "t": float(state.t)},
                        "frame": fr, "belt_hist": self._new_hist(belt)})
        r = self.conn.recv()
        self.finished, self.outcome, self.diag, self.phase = r["finished"], r["outcome"], r["diag"], r.get("phase_name", "")
        self.events += [TrialEvent(e["t"], e["name"], e["data"]) for e in r["events"]]
        self.log.append({"t": t, "remote_ms": r["ms"], "phase": r["phase"]})
        return Command(None if r["q_deg"] is None else np.asarray(r["q_deg"], float), r["gripper"], r["phase"], r.get("note", ""))

    def close(self) -> None:
        try:
            self.conn.send({"op": "close"}); self.conn.recv(); self.conn.close()
        except Exception:                                  # noqa: BLE001
            pass


@register("REMOTE", doc="a method served from another Python environment (arena/remote_server.py)")
def make_remote(ctx: MethodContext):
    if "remote" not in ctx.extra:
        raise SystemExit("REMOTE needs --method-arg remote=host:port")
    return RemoteMethod(ctx, ctx.extra["remote"], ctx.extra.get("remote_authkey", "arena"))
