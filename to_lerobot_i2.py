"""Interface I2: relabel the raw arena demo episodes (arena/demos.py) into a LeRobotDataset in the belt frame (arena/i2.py).

    env -u PYTHONPATH ~/venvs/lerobot_data/bin/python to_lerobot_i2.py --episodes runs/e6_demos_real/episodes [more episode dirs ...] \
        --root runs/e6_demos_real/lerobot_i2 --repo-id local/arena_so101_oracle_i2
Each episode's trial_XXXX_gt.npz is looked up in the PARENT of its episodes dir (where run_arena --record-demos puts it), or in --gt-dir.
observation.state = I2 vector of the MEASURED joints at the frame's capture time; action = I2 vector of the expert's COMMANDED joints at that time.
s(t) = ground-truth belt travel of the trial (trial_XXXX_gt.npz column belt_s_gt, interpolated at the frame time; the belt is not seen by the expert's
labels otherwise).  Same images as to_lerobot.py.  Then stats are recomputed in relative space (RelativeActionsProcessorStep, chunk = --chunk), which is
what the normaliser sees in training (train_act_i2.py).
"""
import argparse, glob, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "cl0")]
ap = argparse.ArgumentParser()
ap.add_argument("--episodes", nargs="+", required=True); ap.add_argument("--gt-dir", default=""); ap.add_argument("--root", required=True)
ap.add_argument("--repo-id", default="local/arena_so101_oracle_i2"); ap.add_argument("--camera", default="front"); ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--config", default=os.path.join(HERE, "configs", "arena.toml")); ap.add_argument("--calib", default=os.path.join(HERE, "runs", "calib", "calib.json"))
ap.add_argument("--chunk", type=int, default=100, help="ACT chunk_size, for the relative action stats"); ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--task-vec", action="store_true", help="E18: add observation.environment_state = the episode's task code (meta task_vec, arena/tasks.py)")
a = ap.parse_args()
import cv2
from cl0.config import load_config
from cl0.kinematics import SO101Kinematics
from lerobot.datasets.dataset_tools import recompute_stats
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from arena.i2 import NAMES, RELATIVE_EXCLUDE, belt_unit, to_vec

cfg = load_config(a.config)
kin = SO101Kinematics(urdf=cfg.robot.urdf or None, tcp_offset_mm=cfg.robot.tcp_offset_mm, margin_deg=cfg.robot.joint_margin_deg)
u = belt_unit(json.load(open(a.calib))["belt_dir_deg"])
files = [f for d in a.episodes for f in sorted(glob.glob(os.path.join(d, "episode_*.npz")))][: a.limit or None]
if not files:
    sys.exit(f"no episode_*.npz in {a.episodes}")
gt_dir = lambda f: a.gt_dir or os.path.dirname(os.path.dirname(os.path.abspath(f)))
if os.path.exists(a.root):
    sys.exit(f"{a.root} exists: choose a new --root (datasets are not overwritten)")
first = np.load(files[0], allow_pickle=True)
h, w = cv2.imdecode(np.frombuffer(first["jpeg"][0], np.uint8), cv2.IMREAD_COLOR).shape[:2]
features = {
    "observation.state": {"dtype": "float32", "shape": (len(NAMES),), "names": NAMES},
    "action": {"dtype": "float32", "shape": (len(NAMES),), "names": NAMES},
    f"observation.images.{a.camera}": {"dtype": "video", "shape": (h, w, 3), "names": ["height", "width", "channels"]},
}
if a.task_vec:
    n_tv = len(json.loads(str(first["meta"]))["task_vec"])
    features["observation.environment_state"] = {"dtype": "float32", "shape": (n_tv,), "names": [f"task{i}" for i in range(n_tv)]}
ds = LeRobotDataset.create(a.repo_id, a.fps, features, root=a.root, robot_type="so101_follower", use_videos=True)
lengths, s_end = [], []
for f in files:
    e = np.load(f, allow_pickle=True)
    meta = json.loads(str(e["meta"]))
    g = np.load(os.path.join(gt_dir(f), f"trial_{meta['trial_id']:04d}_gt.npz"))
    cols = [str(c) for c in g["columns"]]
    s = np.interp(e["t"], g["gt"][:, cols.index("t")], g["gt"][:, cols.index("belt_s_gt")])
    for i in range(len(e["t"])):
        rgb = cv2.cvtColor(cv2.imdecode(np.frombuffer(e["jpeg"][i], np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        st, ac = e["state"][i], e["action"][i]
        fr = {"observation.state": to_vec(kin, st[:5], st[5], s[i], u).astype(np.float32),
              "action": to_vec(kin, ac[:5], ac[5], s[i], u).astype(np.float32),
              f"observation.images.{a.camera}": rgb, "task": meta["task"]}
        if a.task_vec:
            fr["observation.environment_state"] = np.asarray(meta["task_vec"], np.float32)
        ds.add_frame(fr)
    ds.save_episode()
    lengths.append(len(e["t"])); s_end.append(float(s[-1]))
    print(f"  {os.path.relpath(f)}: {len(e['t'])} frames, L={meta['L']}, s_end={s[-1]:.1f} mm", flush=True)
ds.finalize()
rd = LeRobotDataset(a.repo_id, root=a.root)
recompute_stats(rd, relative_action=True, relative_exclude_joints=RELATIVE_EXCLUDE, chunk_size=a.chunk)
st = json.load(open(os.path.join(a.root, "meta", "stats.json")))
summary = {"episodes": rd.num_episodes, "frames": rd.num_frames, "fps": rd.fps, "len_min": min(lengths), "len_mean": float(np.mean(lengths)),
           "len_max": max(lengths), "belt_s_end_mm_max": max(s_end), "names": NAMES, "relative": ["x_b.mm", "y_b.mm", "z.mm"], "chunk": a.chunk,
           "action_stats_relative": {k: st["action"][k] for k in ("mean", "std", "min", "max")},
           "state_stats": {k: st["observation.state"][k] for k in ("mean", "std", "min", "max")}}
print(json.dumps(summary, indent=1))
json.dump(summary, open(os.path.join(os.path.dirname(a.root.rstrip("/")), "dataset_i2_summary.json"), "w"), indent=1)
