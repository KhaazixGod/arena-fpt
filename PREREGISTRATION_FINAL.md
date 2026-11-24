# PREREGISTRATION_FINAL — M1, M3 and M4 v2 at three belt speeds on a new locked sheet, DRAFT

Status: **LOCKED once `lock_commit` below is filled (25/11/2026).** Written 25/11/2026 before any trial was run on `locked/final/test_C2.csv`.
Rule 5 (`CLAUDE.md`): the locked sheet is run only on the user's explicit order (`CONFIRM_TEST=yes`).

## 1. Questions

- **Q1 (primary).** Does M4 v2 (DP_W1 + the corrector of `m4/diffusion_vs.py` with the descent release of `m4v2/diffusion_vs2.py`) raise pick success over M3 (DP_W1 alone) at 75 mm/s?
- **Q2.** How do M3 and M4 v2 compare with a plain kinematic baseline, M1 = CV + IK in open loop (`m4v2/kin_cv_ik.py`)?
- **Q3.** How do the three methods behave at 37.5 mm/s and at 0 mm/s (belt stopped)?

## 2. What is known before the test

- M4 v1 was tested on `locked/m4/test_C2.csv` (seed 1120, PREREGISTRATION_M4.md): 95/180 against 82/180 for M3, +7.2 points, one-sided p = 0.11; the rule (>= +10 points and p <= 0.05) was NOT met.
- Diagnosis of that run (descriptive, 25/11/2026, `scripts/` notes in the thesis): the descent gate holds z at the pre-grasp height while the policy reference keeps going down, and releases it at once; the arm then drops
  at the joint-rate limit. Maximum descent speed in successful trials: median 148 mm/s (M3) against 726 mm/s (M4 v1); before the first object displaced > 10 mm in the collision failures: 18 against 486 mm/s;
  median maximum displacement of a pushed object 19.3 against 33.2 mm; collision failures 54 (M3) against 66 (M4 v1). The correction offsets at the closing time are small in every failure class (median 1.4-2.1 mm).
- M4 v2 changes ONE thing against M4 v1: after a hold, the commanded z falls at most `VS2_VDESC` mm/s until it reaches the policy z, and the gripper stays open meanwhile. Its DEV runs
  (`runs/m4v2_dev_*`, dev_C2 first 20 scenes, DP_W seed 1000, baselines 16/20 for M3 and 18/20 for M4 v1) are in section 3b. No parameter is changed after the lock.
- M3 on earlier sheets: seed 1611 (27/28/35 of 60), seed 1120 (28/28/26 of 60). M1 has not been run on any sheet.

## 3. Design

- Sheet: `locked/final/test_C2.csv`, `python -m arena.arrangements --set sim --cell test_C2 --n 120 --seed 1125 --out locked/final/test_C2.csv` (seed 1125 chosen before generation), 120 scenes, the same ten test objects as before.
- Speeds and scenes: L0.5 (75 mm/s) on scenes 1-120 (blocks a = 1-60 and b = 61-120); L0.25 (37.5 mm/s) and L0 (0 mm/s) on scenes 1-60 (block a). The same scenes for every method at a speed.
- Methods: **M1** one run per block (the arena is deterministic and M1 has no sampling); **M3** and **M4 v2** with DP_W1 seeds 1000, 2000, 3000 (`scripts/final_test.sh`).
- M1 = CV + IK, open loop: the CL-0 Detector and Tracker find the objects, CL-0's selection rule picks the most downstream object inside the reach, its belt-frame estimate is FROZEN at the moment of selection, then CL-0's belt-frame executor
  (IK with the belt counter) approaches, descends, closes and lifts. No wrist-branch planner W1, no update of the estimate, no learning, no simulator state. It is deliberately a plain pipeline.
- M4 v2 parameters: `m4/m4_vs.env` (the v1 values, frozen in PREREGISTRATION_M4.md) and `m4v2/m4v2.env` (`VS2_VDESC`, `VS2_HOLDOPEN`), fixed on the DEV sheet before the lock.
- Valid trials: as in PREREGISTRATION_PAPER.md section 5 (`valid=0` only for simulator faults; a method failure always counts; more than 10 % `valid=0` in a run stops the chain).
- Order (two lanes, two Isaac processes at once): lane A = L0.5 block a, then L0.25; lane B = L0.5 block b, then L0, then the optional M4 v1 runs. Inside a block: M1, then for each seed M3 and M4 v2. A late stop leaves paired runs and the primary speed first.
- Optional descriptive comparator: **M4 v1** (`m4/diffusion_vs.py` with `m4/m4_vs.env`, as in PREREGISTRATION_M4.md) on L0.5 scenes 1-60, seeds 1000, 2000, 3000, run last in lane B and skipped if not started by 27/11/2026 12:00. It has no decision rule: v1 minus M3, v2 minus v1 and v2 minus M3 on those 60 scenes (mean gain, two-sided sign-permutation p, bootstrap interval).
- Not part of the test: M2 (CV + visual servoing) and the closed-loop CL-0 pipeline, with or without W1. They were left out at the user's decision (M2 on 20/11/2026, CL-0 on 25/11/2026). For the record: on the old sheet (seed 1611) at 75 mm/s
  CL0 reached 31/60 and CL0_W 52/60 (`runs/p6_test_c2_l05_cl0`, `runs/p6_test_c2_l05_cl0_w`), so a stronger classical pipeline than M1 exists, and M1 must not be read as the best conventional method.

## 3b. DEV phase before the lock (25/11/2026, `scripts/m4v2_dev.sh`, `scripts/m4v2_dev_summary.py`)

dev_C2 first 20 scenes, L0.5, DP_W seed 1000, all DEV (rule 4). The selection rule was written in `ARENA_TUNING_LOG.md` at 00:59 on 25/11, before the `pause` run had results. Results:

| run | successes | collision failures | median max descent speed in successful runs |
|---|---|---|---|
| M3, DP_W alone (`runs/p4_dev_dp_w_s1000_dev_c2_l05`) | 16/20 | 3 | 154 mm/s |
| M4 v1, default (`runs/m4_dev_c1_default_dev_c2_l05`) | 18/20 | 1 | 740 mm/s |
| M4 v2 rate-limited release, 250 mm/s (`runs/m4v2_dev_v2b_vd250_dev_c2_l05`) | 16/20 | 4 | 308 mm/s |
| M4 v2 rate-limited release, 150 mm/s (stopped by hand after 11 trials) | 7/11 | 4 | 171 mm/s |
| M4 v2 `pause` (stopped after 13 trials, the rule could no longer be met) | 7/13 | 5 | 276 mm/s |
| M1, CV + IK open loop, first 10 scenes (`runs/kin_dev_dev_c2_l05`; no parameters, smoke test) | 4/10 | 1 | - |

By the rule, M4 v2 = the rate-limited release at 250 mm/s (`m4v2/m4v2.env`). On these 20 scenes neither v2 variant is better than M4 v1 (18/20) or than M3 (16/20); 20 scenes of one seed cannot separate them (binomial SD about 1.7 scenes).
The mechanism claim of Section 2 (the fast plunge causes the extra pushes) is therefore NOT supported by DEV; it rests on the descriptive diagnosis of the old TEST. v2 is locked as it is and tested here; M4 v1 is also run as a comparator (below).

## 4. Hypotheses

- **H1 (primary).** At L0.5, on the scenes for which all six DP runs are complete (120 when blocks a and b are complete; if only block a is complete, its 60 scenes, and the result is reported as UNDERPOWERED), the mean over the three seeds of the per-scene
  success difference (M4 v2 minus M3) is at least **+5 points** and the one-sided sign-permutation test (100,000 draws, numpy seed 0) has p <= 0.05. Reported besides: whether the mean gain reaches +10 points (the threshold of PREREGISTRATION_M4.md),
  and a bootstrap 95 % interval of the mean gain (20,000 resamples of scenes, seed 0).
  Why +5 and not +10: per-scene SD of the gain was 41.7 points on the old sheet, so 120 scenes resolve about 7 points (80 % power needs about 220 scenes for a true gain of 7 and 108 for 10);
  the threshold was fixed here, before any trial of this sheet, and is written next to the +10 reading so that nothing depends on the choice.
- Descriptive (no decision rule): per speed, M4 v2 minus M3 (mean gain, bootstrap interval, one-sided and two-sided sign-permutation p); M3 minus M1 and M4 v2 minus M1 (per-scene mean over seeds minus M1, two-sided sign-permutation p);
  pooled successes with Wilson intervals; failure causes; picks per object; median maximum descent speed in successful trials and median maximum displacement of pushed objects (the mechanism of Section 2).
- If H1 is not supported the thesis reports M4 v2 as not shown better; nothing is re-tuned on this sheet.

## 5. Analysis

`scripts/final_decide.py` (frozen) writes `runs/final_test_decision.json`. It reports incomplete runs as such and takes a decision on H1 only from complete blocks.

## 6. Risks acknowledged

- Power: see H1. At 37.5 and 0 mm/s only 60 scenes are run; differences there are descriptive.
- DP_W1 was trained on demonstrations at L0, L0.25 and L0.5, so the three speeds are inside its training range; the new sheet's objects are the same ten held-out objects of the earlier sheets (scenes differ).
- The corrector uses CL-0's detector and tracker, which miss low-contrast objects (the sheet contains box32 and cyl33); v2 does not change perception.
- Lockstep simulation: the detector time (about 36 ms per frame) is not injected as delay; the ROS 2 real-time check of the thesis addresses latency separately.
- The simulator is deterministic but the policy samples noise; M3 is re-run on this sheet, not borrowed.

## 7. Lock (to be filled by `scripts/final_lock.sh`)

```
locked/final/test_C2.csv: ce9d8e7aa511cd727e3b0e7bf60dd329b18a5afbf7127fcdf7fc1a70aa4e521b
m4/m4_vs.env: 698ec2248d59c4ef483ea3303edfbd981e47758e9b7517562d03f0d3e7c0ce3b
m4v2/m4v2.env: 8422e0e0c4a6285fdddfb9a80322fb141030b4154294e2be6b1b3972c4f55637
dp_w_s1000: 737d09ccd963a151b6be4ca4a1161f27c74372602a834389582e3b22153d0d3e
dp_w_s1000/pretrained_model: 5932755f5ac50b1783d93dc8c0960ad77a9813dd87f883965d7a09e83e79ce1d
dp_w_s2000: 88b47f6aea835c4f9077f45dbbc58a1b2c7f16388c5c8567b76ddd948fed997a
dp_w_s2000/pretrained_model: 094b26a7c60e55a4152bbbe10039edc69890f5e34f21a00583caf9c939ba9a37
dp_w_s3000: 0ad63bf645a4f4548a0115958166861e3ff7615a9150ed7a2c130e60a0f59ef9
dp_w_s3000/pretrained_model: 0f4bf3f4abad140795fb4c12239fae78049a77414787471aee56c669321f5dc5
lock_commit: f96b80d776349f4064f9fe4cf7fbf74d19746c7a
```

Frozen files: `m4 m4v2 arena/methods/diffusion_i2.py arena/i2.py arena/dp_i2.py remote_server.py locked/final/test_C2.csv scripts/lib_chain.sh scripts/final_test.sh scripts/final_decide.py`.
