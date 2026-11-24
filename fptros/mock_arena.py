"""Transport test without Isaac or a GPU: a fake arena feeds recorded sim frames, joint states and belt samples to fptros.policy_node (dummy method) at 50 Hz, with a 30 Hz camera, and reports the round-trip latency."""
import argparse, sys, time
import numpy as np
import cv2
from types import SimpleNamespace as NS
from fptros.client import Ros2Method
from fptros import common as C


class FakeBelt:
    def __init__(self): self.t, self.s = [], []
    def add(self, t, s): self.t.append(t); self.s.append(s)
    def history(self): return self.t, self.s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--frame", required=True); ap.add_argument("--ticks", type=int, default=500); a = ap.parse_args()
    img = cv2.imread(a.frame)
    ctx = NS(cfg=None, image_size=img.shape[:2], control_hz=50.0, calib=NS(to_json=lambda: "{}"), calib_path="", background_path="")
    import dataclasses
    ctx.cfg = NS(); dataclasses.asdict = (lambda o: {})              # the dummy ignores the config
    m = Ros2Method(ctx)
    m.reset(0.0, NS(q_deg=np.zeros(5), gripper=40.0, t=0.0))
    belt = FakeBelt(); rt = []
    for k in range(a.ticks):
        t = 0.02 * k
        belt.add(t, 75.0 * t)
        fr = NS(img=img, t_capture=t) if k % 2 == 0 or k % 3 == 0 else None          # about 30 fps
        cmd = m.step(t, fr, belt, NS(q_deg=np.zeros(5), gripper=40.0, t=t))
        rt.append(m.log[-1]["rt_ms"])
    rt = np.array(rt[5:])
    print(f"ticks {a.ticks}  round trip (publish image+joints+belt, tick, command back): median {np.median(rt):.2f} ms  p95 {np.percentile(rt, 95):.2f}  p99 {np.percentile(rt, 99):.2f}  max {rt.max():.2f}   budget 20 ms")
    print("node compute ms median", np.median([r["remote_ms"] for r in m.log[5:]]), " events", [e.name for e in m.events])


if __name__ == "__main__":
    main()
