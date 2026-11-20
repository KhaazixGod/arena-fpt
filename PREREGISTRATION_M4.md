# PREREGISTRATION_M4 — Diffusion Policy with a visual-servoing correction (thesis M4), DRAFT

Status: **DRAFT until locked.** Written 20/11/2026 before any M4 trial was run. It becomes binding when section 7 is filled by `scripts/m4_lock.sh`, committed, and `lock_commit` is added in a second commit.
Rule 5 (`CLAUDE.md`): the locked sheet is run only on the user's explicit order (`CONFIRM_TEST=yes`).

## 1. Question

Does adding a visual-servoing correction (position and yaw, driven by CL-0's belt-frame tracker) to the Diffusion Policy DP_W raise its pick success on novel objects at 75 mm/s?
M3 = DP_W alone. M4 = DP_W + corrector (`m4/diffusion_vs.py`; same checkpoints, no retraining; kept outside `arena/` and `configs/` so that the frozen sets of earlier pre-registrations are untouched).

## 2. What is known before the test (so that it cannot be mistaken for a prediction)

- On the OLD test sheet `locked/paper/test_C2.csv` (seed 1611) the M3 results had been looked at in detail (failure causes, per-object results, closing offsets, yaw misalignment) before M4 was designed.
  For that reason M4 is NOT confirmed on that sheet. The sheet of this pre-registration is new.
- Findings on the old sheet that shaped M4 (descriptive): M3 closing offset to the nearest object centre is 5.3 mm in successful and 5.2 mm in failed runs (offset does not separate them);
  for the five elongated objects the yaw deviation from the perpendicular-to-long-axis rule is a median 16.9 deg in successful and 47.1 deg in failed runs (n = 29, 63); 52 of 90 failures are pushes, 38 are closings without a lift.
  Hence M4 corrects yaw as well as position, and has a grasp authorization.

## 3. Design

- Sheet: `locked/m4/test_C2.csv`, `python -m arena.arrangements --set sim --cell test_C2 --n 60 --seed 1120 --out locked/m4/test_C2.csv` (seed 1120 chosen before generation), 60 scenes, the same ten test objects as before.
- Speed L0.5 (75 mm/s) only.
- Runs (60 scenes each, same scenes for all six): M3 and M4 for DP_W seeds 1000, 2000, 3000 (`scripts/m4_test.sh`).
- M4 parameters: `m4/m4_vs.env`, fixed on the DEV sheet (dev_C2, first 20 scenes, DP_W seed 1000, `scripts/m4_dev.sh`) BEFORE the lock; DEV results are in `ARENA_TUNING_LOG.md`. No parameter is changed after the lock.
- Valid trials: as in PREREGISTRATION_PAPER.md section 5 (`valid=0` only for simulator faults; a method failure always counts; more than 10 % `valid=0` stops the chain).
- Not part of the test: M1 and ACT_W (kept on the old sheet), M2 (dropped by the user on 20/11/2026).

## 4. Hypotheses

- **H1 (primary).** M4 > M3: the mean over the three seeds of the per-scene success difference (M4 minus M3) is at least **+10 points** (about 6 of 60 scenes; the value was left to the assistant by the user on 20/11/2026: "theo m") and the one-sided
  sign-permutation test (100,000 draws, numpy seed 0) has p <= 0.05.
- Descriptive only (no decision rule): per-seed exact McNemar; failure causes; closing offset and yaw deviation of successful and failed runs (as in thesis Section 8.3); corrector diagnostics (ALIGN / BLIND ticks, authorization waits and time-outs, IK fall-backs).
- If H1 is not supported the thesis reports M4 as not better; nothing is re-tuned on this sheet.

## 5. Analysis

`scripts/m4_decide.py` (frozen) writes `runs/m4_test_decision.json`. It prints no decision while any run has fewer than 60 valid rows.

## 6. Risks acknowledged

- Seed-to-seed spread of M3 alone is 8 scenes of 60 (27 to 35): a +10 point mean gain is about 6 scenes, so H1 can fail for a real but small effect.
- The simulator is deterministic but the policy samples noise; M3 is re-run on the new sheet, not borrowed from the old one.
- The corrector uses CL-0's detector and tracker, which miss low-contrast objects (blind: the method then behaves as M3 there); the 60 scenes include box32 and cyl33.
- Lockstep: the detector time (about 36 ms per frame) is not injected as delay.

## 7. Lock (to be filled by `scripts/m4_lock.sh`)

```
locked/m4/test_C2.csv: 766ea34ddc290910d6fca9510d49c8d67468f2344cc915914240ac6dd79185dd
m4/m4_vs.env: FILL AT LOCK (after DEV)
dp_w_s1000: 737d09ccd963a151b6be4ca4a1161f27c74372602a834389582e3b22153d0d3e
dp_w_s1000/pretrained_model: FILL AT LOCK
dp_w_s2000: 88b47f6aea835c4f9077f45dbbc58a1b2c7f16388c5c8567b76ddd948fed997a
dp_w_s2000/pretrained_model: FILL AT LOCK
dp_w_s3000: 0ad63bf645a4f4548a0115958166861e3ff7615a9150ed7a2c130e60a0f59ef9
dp_w_s3000/pretrained_model: FILL AT LOCK
lock_commit: FILL AT LOCK
```

Frozen files: `m4 arena/methods/diffusion_i2.py arena/methods/act_i2.py arena/i2.py arena/dp_i2.py remote_server.py locked/m4/test_C2.csv scripts/lib_chain.sh scripts/m4_wait.sh scripts/m4_test.sh scripts/m4_decide.py`.
