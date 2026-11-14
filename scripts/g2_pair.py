"""Decision rules of PREREGISTRATION_G2.md, evaluated mechanically (same style as e16_pair.py).

    cd arena && env -u PYTHONPATH ~/venvs/cl0/bin/python scripts/g2_pair.py g0|g2|h4|selftest

g0        CL0 alone: system check on seen_C0 (>= 80 %) and the decision cell test_C2 L0.5 (n = 30)       (runs/g0_*)
g2        claim C: ACT_I2 (seed 1000 primary, seed 2000 replication) vs CL0 on test_C2 L0.5, n = 60      (runs/g2_test_*)
h4        interface: ACT_I2 vs ACT_J0 on dev_C0 L1.0, n = 30, two seeds                                  (runs/h4_*)
selftest  re-derives a number already in ARENA_SETUP_REPORT.md (dev_C2 L0.5: ACT_I2 13, CL0 6, 10/3, p = 0.092) to check the code

McNemar: exact, two-sided, paired by arrangement_id.  Only valid=1 trials count.  An incomplete run is reported as INCOMPLETE and no decision is printed.
"""
import csv, math, os, sys
from math import comb

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
PERCEPTION = {'merge', 'seg_miss', 'grasp_point'}      # KE_HOACH_HUONG_1.md, "Quy tắc G0"


def load(run, method):
    """-> ({(cell, L, arrangement_id): row}, number of valid=0 rows) for one method of one run directory."""
    p = f'{run}/trials.csv'
    if not os.path.exists(p):
        return {}, 0
    out, bad = {}, 0
    for r in csv.DictReader(open(p)):
        if r['method'] != method:
            continue
        if r['valid'] != '1':
            bad += 1
            continue
        out[(r['cell'], round(float(r['L']), 3), r['arrangement_id'])] = dict(ok=r['success'] == '1', cause=r['fail_cause'], target=r.get('target', ''))
    return out, bad


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def sr(D, ks):
    k = sum(D[x]['ok'] for x in ks)
    return k, len(ks)


def fmt(D, ks):
    k, n = sr(D, ks); lo, hi = wilson(k, n)
    return f'{k}/{n} = {100 * k / n:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]' if n else '-'


def pair(X, Y, ks):
    b = sum(X[k]['ok'] and not Y[k]['ok'] for k in ks); c = sum(Y[k]['ok'] and not X[k]['ok'] for k in ks)
    kx, n = sr(X, ks); ky, _ = sr(Y, ks)
    return dict(n=n, srx=kx / n, sry=ky / n, gap=100 * (kx - ky) / n, b=b, c=c, p=mcnemar(b, c))


def get(run, method, cell, L, n):
    D, bad = load(run, method)
    D = {k: v for k, v in D.items() if k[0] == cell and k[1] == L}
    return D, bad, len(D) >= n


def need_complete(parts):
    miss = [f'{name}: {len(D)}/{n} valid' + (f', {bad} invalid' if bad else '') for name, (D, bad, ok, n) in parts.items() if not ok]
    if miss:
        print('INCOMPLETE, no decision printed:\n  ' + '\n  '.join(miss))
        sys.exit(1)


def g0():
    seen, b1, ok1 = get('runs/g0_seen_c0', 'CL0', 'seen_C0', 0.5, 20)
    test, b2, ok2 = get('runs/g0_test_c2', 'CL0', 'test_C2', 0.5, 30)
    need_complete({'seen_C0 L0.5 (n=20)': (seen, b1, ok1, 20), 'test_C2 L0.5 (n=30)': (test, b2, ok2, 30)})
    ks, kt = sorted(seen), sorted(test)
    k1, n1 = sr(seen, ks); k2, n2 = sr(test, kt)
    fails = [test[x]['cause'] or 'other' for x in kt if not test[x]['ok']]
    perc = sum(f in PERCEPTION for f in fails)
    print(f'system check CL0 seen_C0 L0.5: {fmt(seen, ks)}  (needs >= 80%)   invalid rows: {b1}')
    print(f'decision cell CL0 test_C2 L0.5: {fmt(test, kt)}   invalid rows: {b2}')
    from collections import Counter
    print('failure causes:', dict(Counter(fails)), f'| perception/grasp-point share {perc}/{len(fails)}' + (f' = {100 * perc / len(fails):.0f}%' if fails else ''))
    if k1 / n1 < 0.8:
        print('\nRESULT: SYSTEM CHECK FAILED (seen_C0 < 80%): technical/calibration fault, NOT a gap. Fix, then rerun G0.'); return
    if k2 >= 26:
        print('\nRESULT: PIVOT (>= 85%, >= 26/30) -> direction 4 (testbed).')
    elif k2 <= 21:
        if fails and perc / len(fails) >= 0.5:
            print('\nRESULT: GO (<= 70% and >= 50% of failures are perception/grasp-point).')
        else:
            print('\nRESULT: CONDITIONAL GO (<= 70% but < 50% perception failures): fix the root cause (calibration, timing, gripper) on DEV only, rerun G0 exactly once.')
    else:
        print('\nRESULT: AMBIGUOUS (22..25 / 30) -> CL-1 on the same cell; the baseline of claim C is the stronger of CL0 and CL-1. [Deadline 15/11: CL-1 will not fit; state CL0-only as a limitation.]')


def objects_hard():
    h = {}
    with open('configs/objects_sim.csv', newline='') as f:
        for r in csv.DictReader(l for l in f if l.strip() and not l.startswith('#')):
            h[r['name'].strip()] = r['hard_type'].strip() or 'ordinary'
    return h


def g2():
    cell, L = 'test_C2', 0.5
    spec = {'I2_s1000': ('runs/g2_test_c2_i2s1000', 'REMOTE:ACT_I2_S1000'), 'I2_s2000': ('runs/g2_test_c2_i2s2000', 'REMOTE:ACT_I2_S2000'),
            'CL0': ('runs/g2_test_c2_cl0', 'CL0'), 'ORACLE': ('runs/g2_test_c2_oracle', 'ORACLE')}
    M, parts = {}, {}
    for name, (run, m) in spec.items():
        D, bad, ok = get(run, m, cell, L, 60); M[name] = D; parts[name] = (D, bad, ok, 60)
    need_complete(parts)
    ks = sorted(set(M['I2_s1000']) & set(M['I2_s2000']) & set(M['CL0']) & set(M['ORACLE']))
    print(f'test_C2 L0.5, {len(ks)} arrangements valid for all four methods (pre-registered n = 60)')
    for name in M:
        print(f'  {name:9s} {fmt(M[name], ks)}')
    res = {}
    for s in ('1000', '2000'):
        r = pair(M[f'I2_s{s}'], M['CL0'], ks); res[s] = r
        print(f'  seed {s}: ACT_I2 {100 * r["srx"]:.0f}% vs CL0 {100 * r["sry"]:.0f}%  gap {r["gap"]:+.1f} pts  I2-only/CL0-only {r["b"]}/{r["c"]}  McNemar p = {r["p"]:.4f}')
    a = res['1000']['gap'] >= 15 and res['1000']['p'] <= 0.05 and res['1000']['srx'] >= 0.60
    b = res['2000']['gap'] >= 15 and res['2000']['srx'] >= 0.60
    print(f'\n(a) seed 1000: gap >= +15, p <= 0.05, SR >= 60%      -> {"PASS" if a else "FAIL"}')
    print(f'(b) seed 2000: gap >= +15, SR >= 60% (point estimate) -> {"PASS" if b else "FAIL"}')
    print('RESULT: ' + ('GO (claim C supported in simulation, novel objects x C2, L0.5)' if a and b else 'NO-GO -> report as is and move to direction 4; do not change thresholds, policy or seed'))
    ko = sr(M['ORACLE'], ks)[0] / len(ks)
    if ko < 0.70:
        print(f'note: ORACLE only {100 * ko:.0f}% (< 70%): the cell is limited by geometry; rule still applied as written')
    hard = objects_hard()
    print('\nBy hard type of the target object (descriptive):')
    groups = {}
    for x in ks:
        for name in ('I2_s1000', 'CL0'):
            t = M[name][x]['target']
            groups.setdefault((hard.get(t, 'no target') if t else 'no target', name), []).append(M[name][x]['ok'])
    for t in sorted({g[0] for g in groups}):
        print(f'  {t:9s} ' + '  '.join(f'{n}: {sum(groups.get((t, n), []))}/{len(groups.get((t, n), []))}' for n in ('I2_s1000', 'CL0')))
    print('\nDescriptive cells (n = 30, L0.5):')
    for c in ('test_C0', 'test_C3'):
        row = []
        for name, tag, m in (('I2_s1000', 'i2s1000', 'REMOTE:ACT_I2_S1000'), ('CL0', 'cl0', 'CL0'), ('ORACLE', 'oracle', 'ORACLE')):
            D, bad, ok = get(f'runs/g2_{c.lower()}_{tag}', m, c, L, 30)
            row.append(f'{name} {fmt(D, sorted(D)) if D else "not run"}')
        print(f'  {c}: ' + ' | '.join(row))


def h4():
    cell, L = 'dev_C0', 1.0
    spec = {'I2_s1000': ('runs/h4_i2s1000', 'REMOTE:ACT_I2_S1000'), 'I2_s2000': ('runs/h4_i2s2000', 'REMOTE:ACT_I2_S2000'),
            'J0_s1000': ('runs/h4_j0s1000', 'REMOTE:ACT_J0_S1000'), 'J0_s2000': ('runs/h4_j0s2000', 'REMOTE:ACT_J0_S2000'),
            'CL0': ('runs/h4_cl0', 'CL0'), 'ORACLE': ('runs/h4_oracle', 'ORACLE')}
    M, parts = {}, {}
    for name, (run, m) in spec.items():
        D, bad, ok = get(run, m, cell, L, 30); M[name] = D; parts[name] = (D, bad, ok, 30)
    need_complete(parts)
    ks = sorted(set.intersection(*[set(D) for D in M.values()]))
    print(f'dev_C0 L1.0 (150 mm/s), {len(ks)} arrangements valid for all methods (pre-registered n = 30)')
    for name in M:
        print(f'  {name:9s} {fmt(M[name], ks)}')
    res = {}
    for s in ('1000', '2000'):
        r = pair(M[f'I2_s{s}'], M[f'J0_s{s}'], ks); res[s] = r
        print(f'  seed {s}: ACT_I2 {100 * r["srx"]:.0f}% vs ACT_J0 {100 * r["sry"]:.0f}%  gap {r["gap"]:+.1f} pts  I2-only/J0-only {r["b"]}/{r["c"]}  McNemar p = {r["p"]:.4f}')
    sup = res['1000']['gap'] >= 15 and res['1000']['p'] <= 0.05 and res['2000']['gap'] >= 15
    print('\nRESULT: ' + ('H4 SUPPORTED (seed 1000: gap >= +15 and p <= 0.05; seed 2000: gap >= +15)' if sup else
                          'H4 NOT SUPPORTED under the pre-registered rule; report as descriptive (n = 30 only sees differences of about 26-32 points)'))
    print('caveat: J0 differs from I2 in interface AND action space (joint vs relative EE), so H4 is tested as a bundle.')


def selftest():
    I2, _ = load('runs/e14_act_i2_dev2', 'REMOTE:ACT_I2'); CL, _ = load('runs/e10_base_L05', 'CL0')
    I2 = {k: v for k, v in I2.items() if k[0] == 'dev_C2' and k[1] == 0.5}; ks = sorted(set(I2) & set(CL))
    r = pair(I2, CL, ks)
    print(f'dev_C2 L0.5: ACT_I2 {sr(I2, ks)[0]}/{len(ks)}, CL0 {sr(CL, ks)[0]}/{len(ks)}, I2-only/CL0-only {r["b"]}/{r["c"]}, p = {r["p"]:.3f}   (report: 13, 6, 10/3, 0.092)')
    assert (sr(I2, ks)[0], sr(CL, ks)[0], r['b'], r['c']) == (13, 6, 10, 3) and abs(r['p'] - 0.092) < 0.001
    assert abs(mcnemar(9, 1) - 0.0215) < 0.001 and abs(mcnemar(0, 0) - 1.0) < 1e-9
    lo, hi = wilson(35, 40)
    assert abs(lo - 0.739) < 0.002 and abs(hi - 0.945) < 0.002, (lo, hi)
    print('selftest OK')


if __name__ == '__main__':
    cmds = {'g0': g0, 'g2': g2, 'h4': h4, 'selftest': selftest}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]]()
