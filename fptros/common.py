"""Topic names and small helpers shared by the ROS 2 policy node and the arena client (thesis Chapter 3.2 / 6.5)."""
import math

T_IMAGE = "/camera/image_raw"        # sensor_msgs/Image, bgr8, header.stamp = capture time (virtual seconds)
T_JOINTS = "/joint_states"          # sensor_msgs/JointState: name = 5 joints + gripper, position = joint angles in rad, gripper 0-100 in the sixth entry, header.stamp = state time
T_BELT = "/belt/counter"            # std_msgs/Float64MultiArray: [t0, s0, t1, s1, ...] new pulse-counter samples (time s, travel mm)
T_TICK = "/fpt/tick"                # std_msgs/Float64MultiArray: [t, n_image, n_joints, n_belt]: control tick t; n_* = number of messages published so far (ordering across topics)
T_CMD = "/robot/command"            # sensor_msgs/JointState: position = 5 joint targets in rad and the gripper (0-100); empty position = no command; header.stamp = t
T_STATUS = "/fpt/status"            # std_msgs/String (JSON): finished, outcome, phase, new events, diag, compute time ms, t
T_CONFIG = "/fpt/config"            # std_msgs/String (JSON), transient-local: the method info (image size, control_hz, calib, cfg, paths)
T_RESET = "/fpt/reset"              # std_msgs/String (JSON): t0, state
T_READY = "/fpt/ready"              # std_msgs/String: the policy node has built its method / has reset

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def deg2rad(v):
    return [math.radians(float(x)) for x in v]


def rad2deg(v):
    return [math.degrees(float(x)) for x in v]


def stamp_of(t: float):
    sec = int(math.floor(t)); return sec, int(round((t - sec) * 1e9))


def t_of(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9
