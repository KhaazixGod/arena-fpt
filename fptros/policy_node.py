"""ROS 2 policy node: serves ANY method of the arena (Diffusion Policy, M4 ...) through ROS 2 topics instead of the REMOTE socket (remote_server.py).

    source /opt/ros/jazzy/setup.bash
    DP_CKPT=runs/dp_w_s1000/checkpoints/last/pretrained_model env -u PYTHONPATH ~/venvs/lerobot_data/bin/python -m fptros.policy_node \
        --factory diffusion_vs2:make_method --path m4v2 --path m4 --path . --path ../cl0

Lockstep: it computes one step per /fpt/tick message, after the image, joint-state and belt messages announced by that tick have arrived (the sequence counters in the tick make the
order across topics deterministic).  The step time and the arrival-to-reply time are reported in /fpt/status.  It receives what a real controller receives (camera, joints, belt
counter) and nothing else.
"""
import argparse, importlib, json, os, sys, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Float64MultiArray, String

from fptros import common as C

QOS = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=200)
QOS_LATCH = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL, history=HistoryPolicy.KEEP_LAST, depth=1)


class PolicyNode(Node):
    def __init__(self, make_method):
        super().__init__("fpt_policy_node")
        self.make_method = make_method
        self.m = None
        self.n_img = self.n_joint = self.n_belt = 0
        self.frame = None            # (img, t_capture) not yet consumed
        self.state = None
        self.belt_new = []
        self.pending = None          # tick waiting for its messages
        self.t_tick_rx = None
        self.n_events = 0
        self.belt = None
        self.pub_cmd = self.create_publisher(JointState, C.T_CMD, QOS)
        self.pub_status = self.create_publisher(String, C.T_STATUS, QOS)
        self.pub_ready = self.create_publisher(String, C.T_READY, QOS)
        self.create_subscription(String, C.T_CONFIG, self.on_config, QOS_LATCH)
        self.create_subscription(String, C.T_RESET, self.on_reset, QOS)
        self.create_subscription(Image, C.T_IMAGE, self.on_image, QOS)
        self.create_subscription(JointState, C.T_JOINTS, self.on_joints, QOS)
        self.create_subscription(Float64MultiArray, C.T_BELT, self.on_belt, QOS)
        self.create_subscription(Float64MultiArray, C.T_TICK, self.on_tick, QOS)

    # ----------------------------------------------------------------------------------------- inputs
    def on_config(self, msg):
        info = json.loads(msg.data)
        self.m = self.make_method(info)
        self.pub_ready.publish(String(data="method"))
        self.get_logger().info("method built")

    def on_reset(self, msg):
        from remote_server import BeltView, RobotState
        d = json.loads(msg.data)
        st = d.get("state")
        self.belt = BeltView()
        self.frame = None
        self.n_events = 0
        self.m.reset(d["t0"], RobotState(np.asarray(st["q_deg"], float), float(st["gripper"]), float(st["t"])) if st else None)
        self.n_img = self.n_joint = self.n_belt = 0
        self.pub_ready.publish(String(data="reset"))

    def on_image(self, msg):
        self.n_img += 1
        img = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(msg.height, msg.width, 3)
        self.frame = (img, C.t_of(msg.header.stamp))
        self._try()

    def on_joints(self, msg):
        self.n_joint += 1
        p = list(msg.position)
        self.state = (np.asarray(C.rad2deg(p[:5]), float), float(p[5]), C.t_of(msg.header.stamp))
        self._try()

    def on_belt(self, msg):
        self.n_belt += 1
        d = list(msg.data)
        self.belt_new += [(d[i], d[i + 1]) for i in range(0, len(d), 2)]
        self._try()

    def on_tick(self, msg):
        self.pending = list(msg.data)
        self.t_tick_rx = time.perf_counter()
        self._try()

    # ----------------------------------------------------------------------------------------- one control tick
    def _try(self):
        if self.pending is None or self.m is None:
            return
        t, ni, nj, nb = self.pending
        if self.n_img < ni or self.n_joint < nj or self.n_belt < nb:
            return
        from remote_server import Frame, RobotState
        self.pending = None
        self.belt.add(self.belt_new); self.belt_new = []
        fr = None
        if self.frame is not None:
            fr = Frame(self.frame[0], self.frame[1]); self.frame = None
        q, g, ts = self.state
        a = time.perf_counter()
        cmd = self.m.step(t, fr, self.belt, RobotState(q, g, ts))
        ms = (time.perf_counter() - a) * 1e3
        out = JointState()
        out.header.stamp.sec, out.header.stamp.nanosec = C.stamp_of(t)
        out.name = C.JOINTS
        if cmd.q_deg is not None:
            out.position = C.deg2rad(cmd.q_deg) + [float(cmd.gripper if cmd.gripper is not None else float("nan"))]
        else:
            out.position = []
            out.effort = [float(cmd.gripper) if cmd.gripper is not None else float("nan")]
        evs = list(self.m.events); new = [{"t": float(e.t), "name": str(e.name), "data": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in dict(e.data).items()}} for e in evs[self.n_events:]]
        self.n_events = len(evs)
        st = {"t": float(t), "finished": bool(self.m.finished), "outcome": str(self.m.outcome or ""), "phase": str(cmd.phase), "phase_name": str(getattr(self.m, "phase", "")),
              "events": new, "diag": {k: (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v)) for k, v in dict(self.m.diag).items()},
              "ms": ms, "node_ms": (time.perf_counter() - self.t_tick_rx) * 1e3, "q_none": cmd.q_deg is None}
        self.pub_cmd.publish(out)
        self.pub_status.publish(String(data=json.dumps(st)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--factory", required=True)
    ap.add_argument("--path", action="append", default=[])
    a, ros_args = ap.parse_known_args(argv)
    for p in a.path:
        sys.path.insert(0, os.path.abspath(p))
    mod, fn = a.factory.split(":", 1)
    make = getattr(importlib.import_module(mod), fn)
    rclpy.init(args=ros_args)
    node = PolicyNode(make)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
