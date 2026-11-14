"""E16: why does ACT_I2 fail?  Failure modes from GROUND TRUTH only (the trial_XXXX_gt.npz of each trial), so it also works for ACT, which emits no phases
(its own `fail_cause_auto` is then meaningless: no CLOSE phase => `collision` = anything moved at any time).

    cd arena && env -u PYTHONPATH ~/venvs/cl0/bin/python scripts/e16_failure_modes.py [> logs/..._e16_failure_modes.txt]

Per trial: first close of the gripper = measured opening < 30 (open 40; on an object 10-25; on nothing ~0); then
    no_close      never closed
    empty_close   objects never lifted >= 5 mm, jaws fully closed (< 3) within 1.5 s: closed on nothing (miss)
    grip_no_lift  never lifted, jaws stalled on something
    partial_lift  some object lifted 5-25 mm at some time (ANY object, ANY attempt of the 20 s)
    lift_not_held lifted >= 25 mm but never held 2 s inside the jaws
and the TCP offset to the nearest object centre at that first close, in the belt frame (da along the belt, db across; belt dir 90 deg: a = y, b = -x).
"""
import collections, csv, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
CLOSE_LT = 30.0

SETS = {
    'I2(/100)': [('runs/e14_act_i2_dev', 'REMOTE:ACT_I2', None), ('runs/e14_act_i2_dev2', 'REMOTE:ACT_I2', None), ('runs/e15_i2_r100', 'REMOTE:ACT_I2', None)],
    'I2(/10)': [('runs/e15_i2_r10', 'REMOTE:ACT_I2_R10', None)],
    'I2F': [('runs/e15_i2f', 'REMOTE:ACT_I2F', None), ('runs/e15_i2f_c3', 'REMOTE:ACT_I2F', None)],
    'J0': [('runs/e11_act_dev', 'REMOTE:ACT_J0', None), ('runs/e14_act_j0_dev2', 'REMOTE:ACT_J0', None)],
    'CL0': [('runs/e8_real', 'CL0', None), ('runs/e9_clutter_real', 'CL0', '0'), ('runs/e10_base_L05', 'CL0', None), ('runs/e15_base_c3_l05', 'CL0', None)],
    'ORACLE': [('runs/e8_real', 'ORACLE', None), ('runs/e9_clutter_real', 'ORACLE', '0'), ('runs/e10_base_L05', 'ORACLE', None), ('runs/e15_base_c3_l05', 'ORACLE', None)],
}
for extra in sys.argv[1:]:                      # NAME=run_dir:method  (e.g. COMMIT=runs/e16_commit_c23:REMOTE:ACT_I2_COMMIT)
    name, spec = extra.split('=', 1); d, m = spec.split(':', 1)
    SETS.setdefault(name, []).append((d, m, None))
MODES = ['success', 'no_close', 'empty_close', 'grip_no_lift', 'partial_lift', 'lift_not_held']


def analyze(run, row):
    tid = int(row['trial_id'])
    p = f'{run}/trial_{tid:04d}_gt.npz'
    if not os.path.exists(p):
        return None
    g = np.load(p); cols = [str(c) for c in g['columns']]; G = g['gt']; C = {c: i for i, c in enumerate(cols)}
    t, grip, z = G[:, 0], G[:, C['grip_pos']], G[:, C['tcp_z']]
    tcp_a, tcp_b = G[:, C['tcp_y']], -G[:, C['tcp_x']]
    names = sorted({c[:-2] for c in cols if c.endswith('.a')})
    O = {n: dict(a=G[:, C[n + '.a']], b=G[:, C[n + '.b']], lift=G[:, C[n + '.z']] - G[0, C[n + '.z']], ab=G[:, C[n + '.a']] - G[:, C['belt_s_gt']]) for n in names}
    ml = max(float(O[n]['lift'].max()) for n in names)
    ok = row['success'] == '1'
    out = dict(trial=tid, ok=ok, cell=row['cell'], L=row['L'], arr=row['arrangement_id'], speed=float(row['speed_mm_s']))
    closed = grip < CLOSE_LT
    if not closed.any():
        out['mode'] = 'success' if ok else 'no_close'
        return out
    i = int(np.argmax(closed)); tc = float(t[i])
    near = min(names, key=lambda n: math.hypot(tcp_a[i] - O[n]['a'][i], tcp_b[i] - O[n]['b'][i]))
    da, db = float(tcp_a[i] - O[near]['a'][i]), float(tcp_b[i] - O[near]['b'][i])
    gmin = float(grip[(t >= tc) & (t <= tc + 1.5)].min())
    pushed = max(float(np.hypot(O[n]['ab'][t <= tc] - O[n]['ab'][0], O[n]['b'][t <= tc] - O[n]['b'][0]).max()) for n in names)
    up = np.nonzero((t > tc) & (z > z[i] + 15))[0]           # arm leaves the bottom
    out.update(t_close=tc, da=da, db=db, gmin=gmin, pushed=pushed, z_close=float(z[i]), n_close=int(((grip[1:] < 25) & (grip[:-1] >= 25)).sum()),
               dwell=float(t[up[0]] - tc) if len(up) else None, grip_lift=float(grip[up[0]]) if len(up) else None,
               ob=float(O[near]['b'][i]), oa=float(O[near]['a'][i]), oz=float(G[0, C[near + '.z']]))
    out['mode'] = 'success' if ok else ('lift_not_held' if ml >= 25 else 'partial_lift' if ml >= 5 else 'empty_close' if gmin < 3 else 'grip_no_lift')
    return out


def load(run, method, rep=None):
    res = []
    for r in csv.DictReader(open(f'{run}/trials.csv')):
        if r['method'] == method and r['valid'] == '1' and (rep is None or r.get('rep', '0') == rep):
            a = analyze(run, r)
            if a is not None:
                res.append(a)
    return res


DATA = {k: sum((load(*a) for a in v), []) for k, v in SETS.items()}
METHODS = [m for m in ['I2(/100)', 'I2(/10)', 'I2F', 'J0', 'CL0', 'ORACLE'] if DATA.get(m)] + [m for m in DATA if m not in ('I2(/100)', 'I2(/10)', 'I2F', 'J0', 'CL0', 'ORACLE')]
GROUPS = [('C0+C1  L0', {'dev_C0', 'dev_C1'}, {'0'}), ('C0+C1  L0.25', {'dev_C0', 'dev_C1'}, {'0.25'}), ('C2  L0.25', {'dev_C2'}, {'0.25'}), ('C2  L0.5', {'dev_C2'}, {'0.5'}),
          ('C3  L0.25', {'dev_C3'}, {'0.25'}), ('C3  L0.5', {'dev_C3'}, {'0.5'})]
med = lambda xs: float(np.median(xs)) if len(xs) else float('nan')

print('== 1. failure modes (GT only).  pushed = failures that closed after moving an object > 10 mm; |da|,|db| = median TCP offset to the nearest object at the first close (failures that closed)')
print(f'{"method":9s} {"cells":14s} {"n":>3s} ' + ' '.join(f'{m[:8]:>8s}' for m in MODES) + '   pushed   |da| |db|')
for gname, cs, Ls in GROUPS:
    for meth in METHODS:
        rs = [r for r in DATA[meth] if r['cell'] in cs and r['L'] in Ls]
        if not rs: continue
        c = collections.Counter(r['mode'] for r in rs)
        fc = [r for r in rs if not r['ok'] and r['mode'] != 'no_close']
        print(f'{meth:9s} {gname:14s} {len(rs):3d} ' + ' '.join(f'{c[m]:8d}' for m in MODES) + f'   {sum(r["pushed"] > 10 for r in fc):2d}/{len(fc):<3d}  {med([abs(r["da"]) for r in fc]):4.1f} {med([abs(r["db"]) for r in fc]):4.1f}')

print('\n== 2. signed offset at the first close (da along the belt, db across; + = TCP downstream / larger b), successes vs failures, all dev cells pooled')
for meth in METHODS:
    cl = [r for r in DATA[meth] if 'da' in r]
    if not cl: continue
    s, f = [r for r in cl if r['ok']], [r for r in cl if not r['ok']]
    X = np.c_[np.ones(len(cl)), [r['ob'] for r in cl], [r['oz'] for r in cl]]
    X[:, 1:] -= X[:, 1:].mean(0)
    beta = np.linalg.lstsq(X, np.array([r['db'] for r in cl]), rcond=None)[0]
    print(f'{meth:9s} n={len(cl):3d}  db median {med([r["db"] for r in cl]):6.1f} (ok {med([r["db"] for r in s]):6.1f} | fail {med([r["db"] for r in f]):6.1f})  sd {np.std([r["db"] for r in cl]):5.1f}   '
          f'da median {med([r["da"] for r in cl]):6.1f} (ok {med([r["da"] for r in s]):5.1f} | fail {med([r["da"] for r in f]):5.1f})  | db slope vs object b {beta[1]:6.3f}, vs object height {beta[2]:6.3f}')

print('\n== 3. close -> lift-off (TCP 15 mm above its height at the close): dwell and gripper opening at lift-off')
for meth in METHODS:
    for ok in (True, False):
        xs = [r for r in DATA[meth] if r.get('dwell') is not None and r['ok'] == ok]
        if not xs: continue
        ga = np.array([r['grip_lift'] for r in xs])
        print(f'{meth:9s} {"ok  " if ok else "fail"} n={len(xs):3d}  dwell median {med([r["dwell"] for r in xs]):.2f} s  p10 {np.percentile([r["dwell"] for r in xs], 10):.2f}  p90 {np.percentile([r["dwell"] for r in xs], 90):.2f}   '
              f'opening at lift-off median {np.median(ga):5.1f}  share < 5 (empty jaws): {np.mean(ga < 5):.2f}')
