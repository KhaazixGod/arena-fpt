"""E16 paired comparison (McNemar exact, two-sided, paired by arrangement) and the PRE-REGISTERED adoption rule (written before the runs, see e16_commit.sh).

    cd arena && env -u PYTHONPATH ~/venvs/cl0/bin/python scripts/e16_pair.py
"""
import csv, os
from math import comb

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)


def idx(p, m, rep=None):
    if not os.path.exists(p):
        return {}
    return {(r['cell'], r['L'], r['arrangement_id']): r['success'] == '1' for r in csv.DictReader(open(p)) if r['method'] == m and r['valid'] == '1' and (rep is None or r.get('rep', '0') == rep)}


def mc(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def merged(srcs):
    d = {}
    for p, m, rep in srcs:
        d.update(idx(p, m, rep))
    return d


M = {
    'COMMIT': merged([('runs/e16_commit_c23/trials.csv', 'REMOTE:ACT_I2_COMMIT', None), ('runs/e16_commit_c01/trials.csv', 'REMOTE:ACT_I2_COMMIT', None)]),
    '/100': merged([('runs/e14_act_i2_dev/trials.csv', 'REMOTE:ACT_I2', None), ('runs/e14_act_i2_dev2/trials.csv', 'REMOTE:ACT_I2', None), ('runs/e15_i2_r100/trials.csv', 'REMOTE:ACT_I2', None)]),
    '/10': merged([('runs/e15_i2_r10/trials.csv', 'REMOTE:ACT_I2_R10', None)]),
    'J0': merged([('runs/e11_act_dev/trials.csv', 'REMOTE:ACT_J0', None), ('runs/e14_act_j0_dev2/trials.csv', 'REMOTE:ACT_J0', None)]),
    'CL0': merged([('runs/e8_real/trials.csv', 'CL0', None), ('runs/e9_clutter_real/trials.csv', 'CL0', '0'), ('runs/e10_base_L05/trials.csv', 'CL0', None), ('runs/e15_base_c3_l05/trials.csv', 'CL0', None)]),
    'ORACLE': merged([('runs/e8_real/trials.csv', 'ORACLE', None), ('runs/e9_clutter_real/trials.csv', 'ORACLE', '0'), ('runs/e10_base_L05/trials.csv', 'ORACLE', None), ('runs/e15_base_c3_l05/trials.csv', 'ORACLE', None)]),
}
REP = idx('runs/e16_repeat_r100/trials.csv', 'REMOTE:ACT_I2_REP')


def pr(X, Y, ks):
    ks = [k for k in ks if k in X and k in Y]
    b = sum(X[k] and not Y[k] for k in ks); c = sum(Y[k] and not X[k] for k in ks)
    return f'{b}/{c} p={mc(b, c):.3f}'


cells = sorted({k[:2] for k in M['COMMIT']})
print('cell            n  COMMIT  /100  /10   J0  CL0  ORACLE | COMMIT vs /100 | vs /10 | vs J0 | vs CL0   (hơn/kém, p)')
for cell in cells:
    ks = [k for k in M['COMMIT'] if k[:2] == cell]
    s = lambda D: (str(sum(D[k] for k in ks if k in D)) if any(k in D for k in ks) else '-')
    print(f'{cell[0]} L{cell[1]:<5s} {len(ks):3d}  ' + '  '.join(f'{s(M[m]):>5s}' for m in ['COMMIT', '/100', '/10', 'J0', 'CL0', 'ORACLE']) + ' | ' +
          ' | '.join(pr(M['COMMIT'], M[m], ks) if any(k in M[m] for k in ks) else '-' for m in ['/100', '/10', 'J0', 'CL0']))

pool = [k for k in M['COMMIT'] if k[0] in ('dev_C2', 'dev_C3') and k[1] in ('0.25', '0.5')]
tot = {m: sum(M[m][k] for k in pool if k in M[m]) for m in ['COMMIT', '/100', '/10', 'CL0', 'ORACLE']}
print(f'\npooled dev_C2+dev_C3 x L0.25,L0.5 (n={len(pool)}): ' + ', '.join(f'{m} {v}' for m, v in tot.items()) + f'   | COMMIT vs /100 {pr(M["COMMIT"], M["/100"], pool)}')
if len(pool) == 80:
    adopt = tot['COMMIT'] >= tot['/100'] + 5 and tot['COMMIT'] >= tot['/10']
    print(f'pre-registered rule: COMMIT >= /100 + 5 ({tot["/100"] + 5}) AND >= /10 ({tot["/10"]})  ->  {"ADOPT COMMIT as the default ACT-I2 inference mode" if adopt else "KEEP /100 as the default"}')
else:
    print('(pool incomplete: rule not evaluated)')
l0 = [k for k in M['COMMIT'] if k[1] == '0']
if l0:
    print(f'\nL0 (dev_C0+dev_C1, n={len(l0)}): ' + ', '.join(f'{m} {sum(M[m][k] for k in l0 if k in M[m])}' for m in ['COMMIT', '/100', 'J0', 'CL0', 'ORACLE']) + f'   | COMMIT vs J0 {pr(M["COMMIT"], M["J0"], l0)} | vs CL0 {pr(M["COMMIT"], M["CL0"], l0)}')
if REP:
    ks = [k for k in REP if k in M['/100']]
    flips = sum(REP[k] != M['/100'][k] for k in ks)
    print(f'\nnoise floor (same model, same /100 setting, fresh server process, dev_C2 L0.5, n={len(ks)}): first run {sum(M["/100"][k] for k in ks)}, repeat {sum(REP[k] for k in ks)}, trials whose outcome flipped: {flips}/{len(ks)}')
