#!/usr/bin/env python3
"""Ghép plan1_template.md + res/md/*.md + res/scalars.json -> ../KE_HOACH_HUONG_1.md
Chạy sau stats_tables.py.  Dùng: python build_plan1.py
"""
import json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import g0_analyze as g

SC = json.load(open(os.path.join(HERE, "res", "scalars.json")))
PR = json.load(open(os.path.join(HERE, "res", "params.json")))

# --- hai script phải dùng cùng một bộ ngưỡng (một nguồn sự thật)
assert abs(g.GO_MAX - PR["G0_GO"]) < 1e-12 and abs(g.PIVOT_MIN - PR["G0_PIVOT"]) < 1e-12, "ngưỡng G0 lệch giữa g0_analyze.py và stats_tables.py"
assert abs(g.G2_MIN_DIFF - 0.15) < 1e-12 and g.G2_MIN_PAIRS == PR["N_PRIMARY"], "ngưỡng/ số cặp G2 lệch"
assert abs(g.ALPHA - PR["ALPHA"]) < 1e-12

# --- tiên nghiệm CHỦ QUAN của mình (phần trăm); sửa ở đây rồi build lại
PRIORS = dict(P_H1=55, P_H2=75, P_H3=30, P_H4=60, P_H4B=40, P_H5=25)
SC.update(PRIORS)
SC["P_CHAIN"] = PRIORS["P_H1"] * PRIORS["P_H2"] * PRIORS["P_H3"] / 10000.0
SC["G0_SANITY_PCT"] = 100 * g.SANITY_MIN


def c(x, nd=1, sign=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        raise ValueError("NaN trong số cần in")
    y = round(x + math.copysign(1e-9, x), nd)
    if y == 0:
        y = 0.0
    s = f"{abs(y):.{nd}f}".replace(".", ",")
    return ("−" + s) if y < 0 else (("+" + s) if (sign and y > 0) else s)


txt = open(os.path.join(HERE, "plan1_template.md"), encoding="utf-8").read()


def sub_scalar(m):
    key, nd = m.group(1), int(m.group(2))
    if key not in SC:
        raise KeyError(f"thiếu scalar: {key}")
    return c(float(SC[key]), nd)


txt = re.sub(r"\{\{([A-Za-z0-9_]+)\|(\d+)\}\}", sub_scalar, txt)


def sub_table(m):
    return open(os.path.join(HERE, "res", "md", m.group(1) + ".md"), encoding="utf-8").read().rstrip("\n")


txt = re.sub(r"<!--T:([a-z0-9]+)-->", sub_table, txt)
left = re.findall(r"\{\{[^}]*\}\}|<!--T:[^>]*-->", txt)
if left:
    sys.exit(f"CÒN placeholder chưa thay: {left}")
out = os.path.join(HERE, "..", "KE_HOACH_HUONG_1.md")
open(out, "w", encoding="utf-8").write(txt)
print("ghi", os.path.abspath(out), len(txt.splitlines()), "dòng")
