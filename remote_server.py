"""Serve a method that lives in ANOTHER Python environment (its own torch / LeRobot / paper repo) to the Isaac arena.  Needs only numpy.

    # in the method's own venv:
    python /path/to/arena/remote_server.py --factory mypkg.mymodule:make_method --name MYMETHOD --port 6001 [--path /path/to/mypkg]
    # in the arena:
    ~/env_isaac/bin/python -m arena.run_arena --methods REMOTE --method-arg remote=localhost:6001 ...

``make_method(info) -> method`` with the arena's method contract (reset / step / finished / outcome / events / log / diag).  ``info`` is a dict sent by the
arena: image size, control_hz, calib (calib.json as a dict), cfg (arena.toml as a dict), paths.  ``step`` receives (t, frame or None, belt, state):
frame.img (BGR uint8), frame.t_capture, frame.depth_mm (or absent); belt.s_at(t) / belt.speed_at(t) are computed from the full stream of pulse-counter
samples with cl0's own algorithm (identical to in-process); state.q_deg (5), state.gripper, state.t.  Return Command(q_deg or None, gripper or None, phase).
Lockstep: the arena waits for every reply, so slow code does not change the simulation (its time is reported as ms/step).
"""
from __future__ import annotations

import argparse
import bisect
import importlib
import os
import sys
import time
from dataclasses import dataclass, field
from multiprocessing.connection import Listener
from typing import Optional

import numpy as np

try:                                       # the CL-0 types when cl0 is importable (same names and fields otherwise)
    from cl0.types import Command, Frame, RobotState, TrialEvent
except Exception:                          # noqa: BLE001
    @dataclass
    class Frame:                           # type: ignore[no-redef]
        img: np.ndarray
        t_capture: float

    @dataclass
    class RobotState:                      # type: ignore[no-redef]
        q_deg: np.ndarray
        gripper: float
        t: float

    @dataclass
    class Command:                         # type: ignore[no-redef]
        q_deg: Optional[np.ndarray]
        gripper: Optional[float]
        phase: str
        note: str = ""

    @dataclass
    class TrialEvent:                      # type: ignore[no-redef]
        t: float
        name: str
        data: dict = field(default_factory=dict)


def unpack_array(d):
    return None if d is None else np.frombuffer(d["data"], dtype=d["dtype"]).reshape(d["shape"])


class BeltView:
    """The belt as the method sees it in-process: the arena streams every pulse-counter sample (t, s mm) it has received, and s_at / speed_at are
    computed with the SAME algorithm as cl0.hw.belt._History (copied below, so cl0 need not be installed here)."""

    def __init__(self):
        self.t, self.s = [], []

    def add(self, samples):
        for t, s in samples:
            if not self.t or t > self.t[-1]:
                self.t.append(float(t)); self.s.append(float(s))

    def s_at(self, t, tail_s: float = 0.3):
        ts, ss = self.t, self.s
        if not ts:
            return 0.0
        if len(ts) == 1:
            return ss[0]
        if t >= ts[-1]:
            j = bisect.bisect_left(ts, ts[-1] - tail_s)
            j = min(j, len(ts) - 2)
            v = (ss[-1] - ss[j]) / max(ts[-1] - ts[j], 1e-6)
            return ss[-1] + v * (t - ts[-1])
        if t <= ts[0]:
            return ss[0]
        return float(np.interp(t, ts, ss))

    def speed_at(self, t, win_s: float = 0.25):
        ts, ss = self.t, self.s
        if len(ts) < 2:
            return 0.0
        t_hi = min(t, ts[-1])
        j1 = bisect.bisect_right(ts, t_hi) - 1
        j0 = bisect.bisect_left(ts, t_hi - win_s)
        j0 = min(j0, max(j1 - 1, 0))
        j1 = max(j1, j0 + 1) if j0 + 1 < len(ts) else j1
        if j1 <= j0:
            return 0.0
        return (ss[j1] - ss[j0]) / max(ts[j1] - ts[j0], 1e-6)


def _ev(e):
    return {"t": float(e.t), "name": str(e.name), "data": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in dict(e.data).items()}}


def serve(make_method, port: int, name: str, authkey: bytes = b"arena") -> None:
    with Listener(("127.0.0.1", port), authkey=authkey) as lst:
        print(f"[remote_server] {name} waiting on 127.0.0.1:{port}", flush=True)
        with lst.accept() as conn:
            info = conn.recv()
            m = make_method(info)
            conn.send({"ok": True, "name": name})
            n_ev = 0
            belt = BeltView()
            while True:
                msg = conn.recv()
                op = msg["op"]
                if op == "reset":
                    st = msg["state"]
                    m.reset(msg["t0"], RobotState(np.asarray(st["q_deg"], float), float(st["gripper"]), float(st["t"])) if st else None)
                    n_ev = 0
                    belt = BeltView()
                    belt.add(msg.get("belt_hist", []))
                    conn.send({"ok": True})
                elif op == "step":
                    st = msg["state"]
                    state = RobotState(np.asarray(st["q_deg"], float), float(st["gripper"]), float(st["t"]))
                    fr = None
                    if msg["frame"] is not None:
                        f = msg["frame"]
                        fr = Frame(unpack_array(f["img"]), float(f["t_capture"]))
                        if f.get("depth") is not None:
                            fr.depth_mm = unpack_array(f["depth"])
                    belt.add(msg["belt_hist"])
                    a = time.perf_counter()
                    cmd = m.step(msg["t"], fr, belt, state)
                    ms = (time.perf_counter() - a) * 1e3
                    evs = list(m.events)
                    new = [_ev(e) for e in evs[n_ev:]]
                    n_ev = len(evs)
                    conn.send({"q_deg": None if cmd.q_deg is None else [float(x) for x in cmd.q_deg], "gripper": None if cmd.gripper is None else float(cmd.gripper),
                               "phase": str(cmd.phase), "note": str(getattr(cmd, "note", "")), "finished": bool(m.finished), "outcome": str(m.outcome or ""),
                               "events": new, "diag": {k: (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v)) for k, v in dict(m.diag).items()},
                               "phase_name": str(getattr(m, "phase", "")), "ms": ms})
                elif op == "close":
                    if hasattr(m, "close"):
                        m.close()
                    conn.send({"ok": True})
                    return


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--factory", required=True, help="module.path:make_method")
    ap.add_argument("--name", required=True, help="method name written in trials.csv (prefixed REMOTE:)")
    ap.add_argument("--port", type=int, default=6001)
    ap.add_argument("--path", action="append", default=[], help="extra sys.path entries (your repo, ../cl0 ...)")
    ap.add_argument("--authkey", default="arena")
    ap.add_argument("--repeat", action="store_true", help="serve again after the arena disconnects")
    a = ap.parse_args(argv)
    for p in a.path:
        sys.path.insert(0, os.path.abspath(p))
    mod, fn = a.factory.split(":", 1)
    make = getattr(importlib.import_module(mod), fn)
    while True:
        serve(make, a.port, a.name, a.authkey.encode())
        if not a.repeat:
            return 0


if __name__ == "__main__":
    sys.exit(main())
