# ports/ — paper front-ends re-implemented for P8

Why: the benchmark's adapters (Benmark_Capstone, Windows machine) are not on this machine; its numbers are DEV-only, cross-machine and on the old
executor.  P8 rebuilds the methods here and runs them on the thesis TEST (PREREGISTRATION_P8.md).  These are **re-implementations by this thesis**,
written from the papers (and, for CNS, from its MIT code, read not imported), not the benchmark's code.

| Port | Paper | What is implemented | Not exercised (as in the benchmark) | venv |
|---|---|---|---|---|
| `p05_cns.py` | CNS (Chen et al., arXiv 2309.09047) | classic front-end: SIFT, FLANN kd-tree, ratio 0.75, RANSAC 5 px; matches -> 2D similarity -> reference grasp moved | GNN servo | ~/venvs/ports |
| `p07_vitvs.py` | ViT-VS (Scherl et al., arXiv 2503.04545) | DINOv2 ViT-S/14 layer-11 tokens, best-buddy correspondences -> similarity -> grasp | IBVS loop | ~/venvs/lerobot_data (torch) |
| `p17_odil.py` | ODIL stage 1 | planar-depth foreground, DBSCAN, FPFH + FGR + point-to-plane ICP (Open3D 0.20 CPU) -> rigid transform -> grasp | GroundedSAM, wrist servo, replay, UKF | ~/venvs/ports |
| P19 | ACT (Zhao et al. 2023) | `arena/methods/act_lerobot.py` with `ACT_TE_COEFF=0.01` on the ACT_J0 checkpoints (benchmark's p19_act.yaml = LeRobot ACT defaults + temporal ensembling) | — | ~/venvs/lerobot_data |

Arena side: `arena/methods/ports.py` (P05_CNS, P07_VITVS, P17_ODIL and their `_W` = + W1), CL-0's tracker / selection / BeltExecutor shared.
Reference views: `REFCAP` (privileged, writes one object alone on the stopped belt + the object's stored good grasp) via `scripts/p8_dev.sh` step 0
-> `runs/p8_refs/train_dev` (main) and `runs/p8_refs/testobj` (labelled variant only).
Server: `ports/detector_server.py --detector p05_cns|p07_vitvs|p17_odil --refs DIR --port N`.  Parameters are fixed in each file's docstring before
any arena run; changes only on DEV, logged in PREREGISTRATION_P8.md section 8.
