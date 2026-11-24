"""Arena side of the ROS 2 transport: a method of the arena (contract of arena/methods/base.py) whose step() publishes the camera image, the joint states and the belt counter as ROS 2
messages, ticks the policy node (fptros.policy_node) and waits for its /robot/command.  Lockstep: the simulation waits, so success is comparable to REMOTE; the wall time of each
round trip is logged (remote_ms = compute in the node, rt_ms = publish-to-reply as seen by the arena) so that the real-time budget can be read from the logs.

    source /opt/ros/jazzy/setup.bash; ~/env_isaac/bin/python -m arena.run_arena --methods fptros.client:make_method [--method-arg ros2_delay_ticks=3] ...

--method-arg ros2_delay_ticks=N : every command is applied N control ticks (20 ms each) late.  The delay is in virtual time and therefore exact; it models a measured loop latency.
"""
import collections, json, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Float64MultiArray, String

from cl0.types import Command, TrialEvent
from fptros import common as C

QOS = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=200)
QOS_LATCH = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL, history=HistoryPolicy.KEEP_LAST, depth=1)
_NODE = {}


def _node():
    if "n" not in _NODE:
        if not rclpy.ok():
            rclpy.init(args=[])
        _NODE["n"] = Node("fpt_arena_bridge")
    return _NODE["n"]


class Ros2Method:
    def __init__(self, ctx, delay_ticks: int = 0, timeout_s: float = 120.0):
        import dataclasses
        self.node = n = _node()
        self.delay, self.timeout = int(delay_ticks), timeout_s
        self.pub_cfg = n.create_publisher(String, C.T_CONFIG, QOS_LATCH)
        self.pub_reset = n.create_publisher(String, C.T_RESET, QOS)
        self.pub_img = n.create_publisher(Image, C.T_IMAGE, QOS)
        self.pub_joint = n.create_publisher(JointState, C.T_JOINTS, QOS)
        self.pub_belt = n.create_publisher(Float64MultiArray, C.T_BELT, QOS)
        self.pub_tick = n.create_publisher(Float64MultiArray, C.T_TICK, QOS)
        self.cmd = self.status = self.ready = None
        n.create_subscription(JointState, C.T_CMD, lambda m: setattr(self, "cmd", m), QOS)
        n.create_subscription(String, C.T_STATUS, lambda m: setattr(self, "status", json.loads(m.data)), QOS)
        n.create_subscription(String, C.T_READY, lambda m: setattr(self, "ready", m.data), QOS)
        cfg_d = json.loads(json.dumps(dataclasses.asdict(ctx.cfg), default=list))
        self.pub_cfg.publish(String(data=json.dumps({"image_size": list(ctx.image_size), "control_hz": ctx.control_hz, "calib": json.loads(ctx.calib.to_json()), "cfg": cfg_d,
                                                      "calib_path": ctx.calib_path, "background_path": ctx.background_path})))
        self._wait(lambda: self.ready == "method", "policy node (method built)")
        self.method_name = "ROS2:fpt_policy_node"
        self.finished, self.outcome, self.events, self.log, self.diag, self.phase = False, "", [], [], {}, ""
        self.n_img = self.n_joint = self.n_belt = 0
        self._n_sent, self._sent_t = 0, []
        self.queue = collections.deque()

    def _wait(self, cond, what, t_max=None):
        t0 = time.perf_counter()
        while not cond():
            rclpy.spin_once(self.node, timeout_sec=0.0005)
            if time.perf_counter() - t0 > (t_max or self.timeout):
                raise TimeoutError(f"ROS 2: no {what} after {time.perf_counter() - t0:.0f} s (is fptros.policy_node running?)")

    def _new_hist(self, belt):
        if not hasattr(belt, "history"):
            return []
        th, sh = belt.history()
        if len(th) and (not len(self._sent_t) or th[0] != self._sent_t[0]):
            self._n_sent = 0
        out = [[float(a), float(b)] for a, b in zip(th[self._n_sent:], sh[self._n_sent:])]
        self._n_sent = len(th); self._sent_t = th[:1]
        return out

    def reset(self, t0, state) -> None:
        self.ready = None
        self._n_sent, self._sent_t = 0, []
        self.n_img = self.n_joint = self.n_belt = 0
        self.queue.clear()
        self.pub_reset.publish(String(data=json.dumps({"t0": t0, "state": None if state is None else {"q_deg": [float(x) for x in state.q_deg], "gripper": float(state.gripper), "t": float(state.t)}})))
        self._wait(lambda: self.ready == "reset", "reset acknowledgement")
        self.finished, self.outcome, self.events, self.log, self.diag, self.phase = False, "", [], [], {}, ""

    def step(self, t, frame, belt, state) -> Command:
        t_a = time.perf_counter()
        if frame is not None:
            m = Image(); m.header.stamp.sec, m.header.stamp.nanosec = C.stamp_of(float(frame.t_capture)); m.header.frame_id = "camera"
            h, w = frame.img.shape[:2]; m.height, m.width, m.encoding, m.is_bigendian, m.step = h, w, "bgr8", 0, w * 3
            m.data = np.ascontiguousarray(frame.img).tobytes()
            self.pub_img.publish(m); self.n_img += 1
        j = JointState(); j.header.stamp.sec, j.header.stamp.nanosec = C.stamp_of(float(state.t)); j.name = C.JOINTS
        j.position = C.deg2rad(state.q_deg) + [float(state.gripper)]
        self.pub_joint.publish(j); self.n_joint += 1
        hist = self._new_hist(belt)
        self.pub_belt.publish(Float64MultiArray(data=[float(v) for p in hist for v in p])); self.n_belt += 1
        self.cmd = self.status = None
        self.pub_tick.publish(Float64MultiArray(data=[float(t), float(self.n_img), float(self.n_joint), float(self.n_belt)]))
        self._wait(lambda: self.cmd is not None and self.status is not None and abs(self.status["t"] - t) < 1e-9, "command")
        rt_ms = (time.perf_counter() - t_a) * 1e3
        r, c = self.status, self.cmd
        self.finished, self.outcome, self.diag, self.phase = r["finished"], r["outcome"], r["diag"], r.get("phase_name", "")
        self.events += [TrialEvent(e["t"], e["name"], e["data"]) for e in r["events"]]
        self.log.append({"t": t, "remote_ms": r["ms"], "rt_ms": rt_ms, "node_ms": r["node_ms"], "phase": r["phase"]})
        if r["q_none"]:
            g = float(c.effort[0]) if len(c.effort) and c.effort[0] == c.effort[0] else None
            out = Command(None, g, r["phase"])
        else:
            p = list(c.position); out = Command(np.asarray(C.rad2deg(p[:5]), float), p[5] if p[5] == p[5] else None, r["phase"])
        self.queue.append(out)
        if self.delay <= 0:
            return out
        return self.queue.popleft() if len(self.queue) > self.delay else Command(None, None, "DELAY")

    def close(self) -> None:
        pass


def make_method(ctx):
    """ROS 2 transport to fptros.policy_node (lockstep)"""
    return Ros2Method(ctx, delay_ticks=int(ctx.extra.get("ros2_delay_ticks", 0)))
