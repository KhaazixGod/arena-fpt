"""The remote bridge: a method in ANOTHER process gets frames / belt / state and its commands, events and outcome come back intact."""
import os
import socket
import subprocess
import sys
import time

import numpy as np
import pytest

from conftest import ARENA, ROOT


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close()
    return p


@pytest.mark.skipif(not os.path.exists(os.path.join(ARENA, "runs", "calib", "calib.json")), reason="needs runs/calib")
def test_remote_round_trip(arena_cfg):
    from arena.methods.base import MethodContext
    from arena.methods.remote import RemoteMethod
    from cl0.geometry import PlaneCalib
    from cl0.types import Frame, RobotState
    port = _free_port()
    env = dict(os.environ); env.pop("PYTHONPATH", None)
    srv = subprocess.Popen([sys.executable, os.path.join(ARENA, "remote_server.py"), "--factory", "remote_dummy:make_method", "--name", "DUMMY", "--port", str(port),
                            "--path", os.path.join(ARENA, "tests"), "--path", os.path.join(ROOT, "cl0")], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        calib = PlaneCalib.load(os.path.join(ARENA, "runs", "calib", "calib.json"))
        ctx = MethodContext(arena_cfg, None, calib, "", "", (1280, 720), 50.0)
        for _ in range(50):
            try:
                m = RemoteMethod(ctx, f"127.0.0.1:{port}")
                break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.1)
        assert m.method_name == "REMOTE:DUMMY"

        class Belt:                                         # like cl0.hw.belt.Belt: counter samples every 10 ms at 40 mm/s
            def history(self):
                th = np.arange(-0.2, 0.1, 0.01)
                return th, 40.0 * th

            def s_at(self, t):
                return 40.0 * t

            def speed_at(self, t):
                return 40.0
        st = RobotState(np.zeros(5), 40.0, 0.0)
        m.reset(0.0, st)
        img = np.full((720, 1280, 3), 7, np.uint8)
        cmds = []
        for k in range(5):
            t = 0.02 * k
            cmds.append(m.step(t, Frame(img, t - 0.1) if k == 1 else None, Belt(), st))
        assert m.finished and m.outcome == "dummy_done"
        assert np.allclose(cmds[0].q_deg, 1.0) and cmds[0].gripper is None and cmds[2].gripper == 0.0
        assert m.diag["px"] == 7 and abs(m.diag["s_img"] - 40.0 * (0.02 - 0.1)) < 1e-6 and abs(m.diag["s_now"] - 40.0 * 0.08) < 1e-6
        assert [e.name for e in m.events] == ["phase:DUMMY", "phase:DONE"] and m.events[0].data["w"] == 1280
        m.close()
    finally:
        srv.wait(timeout=10) if srv.poll() is None else None
        if srv.poll() is None:
            srv.kill()
