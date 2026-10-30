"""E6: convert raw arena demo episodes (arena/demos.py) into a LeRobotDataset (LeRobot 0.6.1).  Run in the venv that HAS LeRobot (~/venvs/cl0), not Isaac's.

    env -u PYTHONPATH ~/venvs/cl0/bin/python arena/to_lerobot.py --episodes arena/runs/e6_demos/episodes --root arena/runs/e6_demos/lerobot --repo-id local/arena_so101_oracle
Features use the names of the real `lerobot-record` with an SO-101 follower: observation.state / action = [shoulder_pan.pos ... gripper.pos] (deg, gripper
0-100), observation.images.<camera> = video.  robot_type = so101_follower.  The dataset is then reloaded with LeRobotDataset and summarised.
"""
import argparse, glob, json, os, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--episodes", required=True); ap.add_argument("--root", required=True); ap.add_argument("--repo-id", default="local/arena_so101_oracle")
ap.add_argument("--camera", default="front", help="camera key (match the real recorder's camera name)"); ap.add_argument("--fps", type=int, default=30)
a = ap.parse_args()
import cv2
from lerobot.datasets.lerobot_dataset import LeRobotDataset

files = sorted(glob.glob(os.path.join(a.episodes, "episode_*.npz")))
if not files:
    sys.exit(f"no episode_*.npz in {a.episodes}")
first = np.load(files[0], allow_pickle=True)
names = [str(x) for x in first["names"]]
h, w = cv2.imdecode(np.frombuffer(first["jpeg"][0], np.uint8), cv2.IMREAD_COLOR).shape[:2]
features = {
    "observation.state": {"dtype": "float32", "shape": (len(names),), "names": names},
    "action": {"dtype": "float32", "shape": (len(names),), "names": names},
    f"observation.images.{a.camera}": {"dtype": "video", "shape": (h, w, 3), "names": ["height", "width", "channels"]},
}
if os.path.exists(a.root):
    sys.exit(f"{a.root} exists: choose a new --root (datasets are not overwritten)")
ds = LeRobotDataset.create(a.repo_id, a.fps, features, root=a.root, robot_type="so101_follower", use_videos=True)
lengths = []
for f in files:
    e = np.load(f, allow_pickle=True)
    meta = json.loads(str(e["meta"]))
    for i in range(len(e["t"])):
        rgb = cv2.cvtColor(cv2.imdecode(np.frombuffer(e["jpeg"][i], np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        ds.add_frame({"observation.state": e["state"][i].astype(np.float32), "action": e["action"][i].astype(np.float32),
                      f"observation.images.{a.camera}": rgb, "task": meta["task"]})
    ds.save_episode()
    lengths.append(len(e["t"]))
    print(f"  {os.path.basename(f)}: {len(e['t'])} frames, success={meta['success']}, objects={meta['objects']}", flush=True)
ds.finalize()
rd = LeRobotDataset(a.repo_id, root=a.root)
size_mb = sum(os.path.getsize(os.path.join(dp, x)) for dp, _, fs in os.walk(a.root) for x in fs) / 1e6
item = rd[0]
summary = {"episodes": rd.num_episodes, "frames": rd.num_frames, "fps": rd.fps, "len_min": min(lengths), "len_mean": float(np.mean(lengths)),
           "len_max": max(lengths), "size_MB": round(size_mb, 1), "features": list(rd.features), "image_shape": list(item[f"observation.images.{a.camera}"].shape)}
print(json.dumps(summary, indent=1))
json.dump(summary, open(os.path.join(os.path.dirname(a.root.rstrip("/")), "dataset_summary.json"), "w"), indent=1)
