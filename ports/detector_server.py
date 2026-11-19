"""Serve one P8 paper front-end (ports/p05_cns.py, p07_vitvs.py, p17_odil.py) to the arena's P05_CNS / P07_VITVS / P17_ODIL methods (arena/methods/ports.py).

    env -u PYTHONPATH ~/venvs/ports/bin/python ports/detector_server.py --detector p05_cns --refs runs/p8_refs/train_dev --port 6305 --repeat
    (p07_vitvs needs torch: ~/venvs/lerobot_data/bin/python)

Protocol (multiprocessing.connection, authkey "arena"): the arena sends {calib, window, image_size} once, the server answers {name, refs, ...};
then for every detect call {img, depth} -> {grasps: [{u, v, angle_deg, width_mm, score}]} or {error}.  Lockstep: the arena waits for the answer, so
compute time does not change the simulation; it is reported (ms per call) when the arena disconnects.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
import time
import traceback
from multiprocessing.connection import Listener

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def unpack(d):
    if d is None:
        return None
    return np.frombuffer(d["data"], dtype=d["dtype"]).reshape(d["shape"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--detector", required=True, choices=["p05_cns", "p07_vitvs", "p17_odil"])
    ap.add_argument("--refs", required=True, help="reference view directory (ports/make_refs.sh)")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--authkey", default="arena")
    ap.add_argument("--repeat", action="store_true", help="serve again after the arena disconnects")
    ap.add_argument("--opt", action="append", default=[], help="key=value option of the detector (logged)")
    a = ap.parse_args(argv)
    mod = importlib.import_module(a.detector)
    opts = dict(kv.split("=", 1) for kv in a.opt)
    with Listener(("localhost", a.port), authkey=a.authkey.encode()) as lis:
        print(f"{time.strftime('%T')} {a.detector} listening on {a.port}, refs {a.refs}, opts {opts}", flush=True)
        while True:
            conn = lis.accept()
            info = conn.recv()
            det = mod.Detector(a.refs, info, **opts)
            conn.send({"name": det.NAME, "refs": [r.name for r in det.refs], "opts": opts, "version": getattr(mod, "VERSION", "")})
            ms, n = [], 0
            try:
                while True:
                    req = conn.recv()
                    t = time.perf_counter()
                    try:
                        gs = det(unpack(req["img"]), unpack(req.get("depth")))
                        conn.send({"grasps": [g.as_dict() for g in gs]})
                    except Exception as e:                 # noqa: BLE001  a detector error is the method's failure, reported to the arena
                        conn.send({"error": f"{type(e).__name__}: {e}"})
                        traceback.print_exc()
                    ms.append(1000.0 * (time.perf_counter() - t)); n += 1
            except EOFError:
                pass
            if ms:
                q = np.percentile(ms, [50, 95])
                print(f"{time.strftime('%T')} disconnected after {n} calls, ms/call p50 {q[0]:.1f} p95 {q[1]:.1f}", flush=True)
            if not a.repeat:
                return 0


if __name__ == "__main__":
    sys.exit(main())
