#!/usr/bin/env python3
"""Result figures that exist only after the P6 TEST chain / the P7 benchmark-DEV chain have finished (bao_cao_do_an/).
    python3 bao_cao_do_an/make_result_figures.py      (from arena/; system python with matplotlib)
fig_p6_test.png  <- runs/p6_test_decision.json   (scripts/p6_decide.py; success counts of the 13 methods at L0.5, n = 60 each)
fig_p7_bench.png <- runs/p7_bench_compare.json   (scripts/p7_bench_compare.py; ours on this machine + the papers from the benchmark machine)
A missing input file is skipped.  Same style and validated palette as make_figures.py.  Override the inputs / output folder (for tests) with
REPORT_P6_JSON, REPORT_P7_JSON, REPORT_FIG_DIR; the P7 JSON is used only when the P7 chain log says it is done (or REPORT_P7_JSON is set).
"""
import glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ARENA = os.path.dirname(HERE)
OUT = os.environ.get("REPORT_FIG_DIR") or os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)
C = {"modular": "#2a78d6", "act": "#eb6834", "dp": "#1baf7a", "priv": "#6250d6", "paper": "#8a8984"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK, "axes.titleweight": "bold", "axes.titlesize": 11, "savefig.dpi": 200})


def wilson(s, n, z=1.959964):
    p = s / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return max(0, c - h), min(1, c + h)


def dotplot(rows, fname, xlabel="Tỉ lệ thành công (%) — chấm: điểm ước lượng, vạch: Wilson 95%", legend=None, width=7.2, row_h=0.42):
    """rows: list of (label, s, n, kind), drawn top to bottom; a row (label, None, None, None) is a group heading."""
    h = row_h * len(rows) + 1.3
    fig, ax = plt.subplots(figsize=(width, h))
    for i, (lab, s, n, kind) in enumerate(rows):   # percentages round half up, like pct() in fill.js
        y = len(rows) - 1 - i
        if s is None:
            continue
        lo, hi = wilson(s, n)
        ax.plot([100 * lo, 100 * hi], [y, y], color=C[kind], lw=2, solid_capstyle="round", zorder=2)
        ax.scatter([100 * s / n], [y], s=64, color=C[kind], edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(104, y, f"{s}/{n} ({int(100 * s / n + 0.5)}%)", va="center", ha="left", color=INK, fontsize=9)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
    for t, r in zip(ax.get_yticklabels(), rows[::-1]):
        if r[1] is None:
            t.set_fontweight("bold"); t.set_color(INK2)
    ax.set_xlim(0, 102); ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel(xlabel, fontsize=9)
    if legend:
        handles = [plt.Line2D([0], [0], marker="o", color=C[k], lw=2, markersize=7, markeredgecolor="white", label=t) for k, t in legend]
        ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=len(handles), frameon=False, fontsize=8.5,
                  handletextpad=0.4, columnspacing=1.2, borderaxespad=0.2)
    fig.subplots_adjust(left=0.34, right=0.84, top=1 - 0.45 / h, bottom=0.62 / h)
    fig.savefig(os.path.join(OUT, fname)); plt.close(fig)
    print("wrote", os.path.join(OUT, fname))


# ---------------------------------------------------------------- P6
p6_path = os.environ.get("REPORT_P6_JSON") or os.path.join(ARENA, "runs", "p6_test_decision.json")
if os.path.exists(p6_path):
    d = json.load(open(p6_path)); S, n = d["success"], d["n"]
    rows = [("CL0", "cl0", "modular"), ("CL0_W (W1)", "cl0_w", "modular"), ("ORACLE", "oracle", "priv"), ("ORACLE_W (W1)", "oracle_w", "priv"),
            ("ACT_old s1000", "act_old_s1000", "act"), ("ACT_old s2000", "act_old_s2000", "act"),
            ("ACT_W s1000", "act_w_s1000", "act"), ("ACT_W s2000", "act_w_s2000", "act"), ("ACT_W s3000", "act_w_s3000", "act"),
            ("ACT_W_slow s1000", "act_w_slow_s1000", "act"),
            ("DP_W s1000", "dp_w_s1000", "dp"), ("DP_W s2000", "dp_w_s2000", "dp"), ("DP_W s3000", "dp_w_s3000", "dp")]
    dotplot([(lab, S[k], n, kind) for lab, k, kind in rows], "fig_p6_test.png",
            legend=[("modular", "Mô-đun"), ("act", "ACT"), ("dp", "Diffusion Policy"), ("priv", "Đặc quyền")])
else:
    print("skip fig_p6_test.png:", p6_path, "does not exist yet")

# ---------------------------------------------------------------- P7
p7_path = os.environ.get("REPORT_P7_JSON") or os.path.join(ARENA, "runs", "p7_bench_compare.json")
chain_done = bool(os.environ.get("REPORT_P7_JSON")) or any("P7 benchmark-DEV chain done" in open(f).read()
                                                            for f in glob.glob(os.path.join(ARENA, "logs", "*_p7_bench_chain.log")))
if os.path.exists(p7_path) and chain_done:
    S = json.load(open(p7_path))["summary"]
    ours = [("CL0", "modular"), ("CL0_W (W1)", "modular"), ("ORACLE", "priv"), ("ORACLE_W (W1)", "priv"),
            ("ACT_old s1000", "act"), ("ACT_old s2000", "act"), ("ACT_W s1000", "act"), ("ACT_W s2000", "act"), ("ACT_W s3000", "act"),
            ("ACT_W_slow s1000", "act"), ("DP_W s1000", "dp"), ("DP_W s2000", "dp"), ("DP_W s3000", "dp")]
    ports = sorted(k for k in S if k.endswith("(here)"))
    papers = [("P17 ODIL stage1", "P17 ODIL (thành phần)"), ("P19 ACT", "P19 ACT (port gốc)"), ("P05 CNS frontend", "P05 CNS (thành phần)"),
              ("P07 ViT-VS", "P07 ViT-VS (thành phần)")]
    ok = lambda k: k in S and S[k]["n"] > 0
    rows = [("Đồ án, máy này (P7)", None, None, None)]
    rows += [(k.replace(" (W1)", ""), S[k]["s"], S[k]["n"], kind) for k, kind in ours if ok(k)]
    rows += [(k.replace(" (here)", " (port, máy này)"), S[k]["s"], S[k]["n"], "paper") for k in ports if ok(k)]
    rows += [("Máy benchmark", None, None, None)]
    rows += [(lab, S[k]["s"], S[k]["n"], "paper") for k, lab in papers if ok(k)]
    rows += [(lab, S[k]["s"], S[k]["n"], kind) for k, lab, kind in (("bench CL0", "CL0 (benchmark)", "modular"), ("bench ORACLE", "ORACLE (benchmark)", "priv")) if ok(k)]
    dotplot(rows, "fig_p7_bench.png",
            legend=[("modular", "Mô-đun"), ("act", "ACT"), ("dp", "DP"), ("paper", "Bài báo tái lập"), ("priv", "Đặc quyền")])
    # compact version for the 5-page summary: seeds of one method summed (descriptive; the interval treats the pooled trials as independent)
    fams = [("CL0_W", ["CL0_W (W1)"], "modular"), ("ORACLE_W", ["ORACLE_W (W1)"], "priv"),
            ("ACT_old (2 hạt giống)", ["ACT_old s1000", "ACT_old s2000"], "act"), ("ACT_W (3 hạt giống)", ["ACT_W s1000", "ACT_W s2000", "ACT_W s3000"], "act"),
            ("DP_W (3 hạt giống)", ["DP_W s1000", "DP_W s2000", "DP_W s3000"], "dp")]
    short = [("Đồ án, máy này (P7)", None, None, None)]
    short += [(lab, sum(S[k]["s"] for k in ks), sum(S[k]["n"] for k in ks), kind) for lab, ks, kind in fams if all(ok(k) for k in ks)]
    short += [("Máy benchmark", None, None, None)]
    short += [(lab, S[k]["s"], S[k]["n"], kind) for k, lab, kind in (("bench CL0", "CL0 (benchmark)", "modular"),) if ok(k)]
    short += [(lab, S[k]["s"], S[k]["n"], "paper") for k, lab in papers if ok(k)]
    dotplot(short, "fig_p7_bench_gon.png",
            legend=[("modular", "Mô-đun"), ("act", "ACT"), ("dp", "DP"), ("paper", "Bài báo"), ("priv", "Đặc quyền")], width=6.0, row_h=0.3)
else:
    print("skip fig_p7_bench.png:", p7_path, "missing or the P7 chain is not done")

# ---------------------------------------------------------------- P8
p8_path = os.environ.get("REPORT_P8_JSON") or os.path.join(ARENA, "runs", "p8_test_decision.json")
if os.path.exists(p8_path):
    S8 = json.load(open(p8_path))["success"]
    def r8(sp, lab, names, kind):
        if not all(f"{sp}/{n}" in S8 for n in names):
            return None
        return (lab, sum(S8[f"{sp}/{n}"] for n in names), 60 * len(names), kind)
    rows = []
    for sp, head in (("l05", "TEST, 75 mm/s (L0,5)"), ("l025", "TEST, 37,5 mm/s (L0,25)")):
        rows.append((head, None, None, None))
        rows += [x for x in (r8(sp, "CL0_W", ["cl0_w"], "modular"), r8(sp, "ACT_W (3 hạt giống)", ["act_w_s1000", "act_w_s2000", "act_w_s3000"], "act"),
                             r8(sp, "P07 ViT-VS + W1", ["p07_vitvs_w"], "paper"), r8(sp, "P17 ODIL + W1", ["p17_odil_w"], "paper"),
                             r8(sp, "P05 CNS + W1", ["p05_cns_w"], "paper"), r8(sp, "P19 ACT gốc (3 hạt giống)", ["p19_s1000", "p19_s2000", "p19_s3000"], "paper"))
                 if x]
    dotplot(rows, "fig_p8_test.png", legend=[("modular", "Mô-đun"), ("act", "ACT (đồ án)"), ("paper", "Bài báo dựng lại")], width=6.4, row_h=0.34)
else:
    print("skip fig_p8_test.png:", p8_path, "does not exist yet")
