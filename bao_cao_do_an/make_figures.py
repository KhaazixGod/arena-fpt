#!/usr/bin/env python3
"""Figures for the bachelor-thesis report on ACT (bao_cao_do_an/).  Every number is read from runs/*/trials.csv or the benchmark's trials.csv, or
copied from the decision logs named next to it; nothing is typed by hand except the labels.
    python3 bao_cao_do_an/make_figures.py   (from arena/)  -> bao_cao_do_an/figures/*.png
"""
import csv, os, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ARENA = os.path.dirname(HERE)
BENCH = os.path.join(ARENA, "..", "..", "Benmark_Capstone", "results", "raw")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

# validated categorical slots (dataviz reference palette, light mode): blue, orange, aqua, violet; neutral gray for the benchmark's paper ports
C = {"modular": "#2a78d6", "act": "#eb6834", "dp": "#1baf7a", "priv": "#6250d6", "paper": "#8a8984"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK, "axes.titleweight": "bold", "axes.titlesize": 11, "savefig.dpi": 200})


def wilson(s, n, z=1.959964):
    p = s / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return max(0, c - h), min(1, c + h)


def count(path, method=None, keys=None, cell=None, L=None):
    s = n = 0; seen = set()
    for r in csv.DictReader(open(path)):
        if r.get("valid") != "1" or (method and r["method"] != method) or (cell and r["cell"] != cell) or (L and r["L"] != L):
            continue
        k = (r["arrangement_id"], r["L"])
        if (keys is not None and k not in keys) or k in seen:
            continue
        seen.add(k); n += 1; s += r["success"] == "1"
    return s, n


def dotplot(rows, title, fname, xlabel="Tỉ lệ thành công (%) — chấm: điểm ước lượng, vạch: Wilson 95%", legend=None, height=None):
    """rows: list of (label, s, n, kind).  Drawn top to bottom in the given order."""
    h = height or 0.42 * len(rows) + 1.3
    fig, ax = plt.subplots(figsize=(7.2, h))
    for i, (lab, s, n, kind) in enumerate(rows):
        y = len(rows) - 1 - i
        lo, hi = wilson(s, n)
        ax.plot([100 * lo, 100 * hi], [y, y], color=C[kind], lw=2, solid_capstyle="round", zorder=2)
        ax.scatter([100 * s / n], [y], s=64, color=C[kind], edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(104, y, f"{s}/{n} ({100 * s / n:.0f}%)", va="center", ha="left", color=INK, fontsize=9)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
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
    fig.subplots_adjust(left=0.30, right=0.84, top=1 - 0.45 / h, bottom=0.62 / h)
    fig.savefig(os.path.join(OUT, fname)); plt.close(fig)
    print("wrote", fname)


def run(name):
    return os.path.join(ARENA, "runs", name, "trials.csv")


# ---- Fig 1: G2 TEST (thesis, frozen): logs/2026-11-10_210822_g2_decision.txt
g2 = [("ORACLE (đặc quyền)", 28, 60, "priv"), ("CL0 (mô-đun)", 22, 60, "modular"), ("ACT_I2 hạt giống 1000", 21, 60, "act"), ("ACT_I2 hạt giống 2000", 18, 60, "act")]
dotplot(g2, "TEST G2 của đồ án: test_C2, L0,5 (75 mm/s), 60 cảnh ghép cặp", "fig_g2_test.png",
        legend=[("modular", "Mô-đun"), ("act", "ACT"), ("priv", "Đặc quyền")])

# ---- Fig 2: ACT interface / inference variants, dev_C2 + dev_C3 x L0.25 + L0.5 (80 trials), ARENA_SETUP_REPORT E15/E16
# totals as recorded in ARENA_SETUP_REPORT.md E15/E16 (logs/2026-11-08_175431_e16_pair_final.txt): /80 on dev_C2, dev_C3 x L0.25, L0.5
v80 = [("ORACLE (đặc quyền)", 61, 80, "priv"), ("ACT_I2F: thêm 76 demo L0,5", 50, 80, "act"), ("ACT_I2, kế hoạch lại mỗi 100 khung", 48, 80, "act"),
       ("CL0 (mô-đun)", 43, 80, "modular"), ("ACT_I2 + COMMIT", 41, 80, "act"), ("ACT_I2, kế hoạch lại mỗi 10 khung", 39, 80, "act")]
dotplot(v80, "Các biến thể suy luận và dữ liệu của ACT_I2 trên DEV (dev_C2, dev_C3 × L0,25, L0,5)", "fig_act_variants.png",
        legend=[("modular", "Mô-đun"), ("act", "ACT"), ("priv", "Đặc quyền")])

# ---- Fig 3: J0 vs I2 at dev_C2 L0.5 (E14): runs/e14_act_j0_dev2, e14_act_i2_dev2, e10_base_L05
j0 = count(run("e14_act_j0_dev2"), cell="dev_C2", L="0.5")
i2 = count(run("e14_act_i2_dev2"), cell="dev_C2", L="0.5")
cl0 = count(run("e10_base_L05"), method="CL0", cell="dev_C2", L="0.5")
orc = count(run("e10_base_L05"), method="ORACLE", cell="dev_C2", L="0.5")
dotplot([("ORACLE (đặc quyền)", *orc, "priv"), ("ACT_I2 (hệ băng, tương đối)", *i2, "act"), ("CL0 (mô-đun)", *cl0, "modular"), ("ACT_J0 (góc khớp tuyệt đối)", *j0, "act")],
        "Giao diện hành động ở băng nhanh: dev_C2, L0,5, 20 cảnh", "fig_j0_vs_i2.png", legend=[("modular", "Mô-đun"), ("act", "ACT"), ("priv", "Đặc quyền")])

# ---- Fig 4: all methods on the 20 shared DEV scenes, dev_C2 L0.5 (paper-dev P2-P5)
dev = [("ORACLE_W (đặc quyền + W1)", "p5_woracle_dev_c2_l05", "priv"), ("CL0_W (mô-đun + W1)", "p2_cl0w_dev_c2_l05", "modular"),
       ("ORACLE (đặc quyền)", "p5_oracle_dev_c2_l05", "priv"), ("DP_W s1000", "p4_dev_dp_w_s1000_dev_c2_l05", "dp"), ("DP_W s3000", "p4_dev_dp_w_s3000_dev_c2_l05", "dp"),
       ("ACT_old s1000", "p4_dev_act_old_s1000_dev_c2_l05", "act"), ("ACT_W s1000", "p4_dev_act_w_s1000_dev_c2_l05", "act"), ("ACT_W s2000", "p4_dev_act_w_s2000_dev_c2_l05", "act"),
       ("ACT_W_slow s1000", "p4_dev_act_w_slow_s1000_dev_c2_l05", "act"), ("ACT_W s3000", "p4_dev_act_w_s3000_dev_c2_l05", "act"), ("DP_W s2000", "p4_dev_dp_w_s2000_dev_c2_l05", "dp"),
       ("CL0 (mô-đun)", "p2_cl0_dev_c2_l05", "modular")]
keys20 = {(f"dev_C2_{i:03d}", "0.5") for i in range(1, 21)}
rows = [(lab, *count(run(r), keys=keys20), k) for lab, r, k in dev]
rows.sort(key=lambda x: -x[1] / x[2])
dotplot(rows, "Mọi phương pháp trên 20 cảnh DEV chung: dev_C2, L0,5", "fig_dev_l05_all.png",
        legend=[("modular", "Mô-đun"), ("act", "ACT"), ("dp", "Diffusion Policy"), ("priv", "Đặc quyền")])

# ---- Fig 5: W1 effect (dumbbells), paired on the same scenes
w1 = [("ORACLE, train_C2 L0,5", "p1_oracle_train_c2_l05", "p2_oraclew2_train_c2_l05", None, "priv"),
      ("ORACLE, train_C3 L0,5", "p2_oracle_train_c3_l05", "p2_oraclew_train_c3_l05", None, "priv"),
      ("ORACLE, dev_C2 L0,5", "p5_oracle_dev_c2_l05", "p5_woracle_dev_c2_l05", None, "priv"),
      ("CL0, dev_C2 L0,5", "p2_cl0_dev_c2_l05", "p2_cl0w_dev_c2_l05", None, "modular"),
      ("ORACLE, dev_C2 L0,25", "p5_oracle_dev_c2_l025", "p5_woracle_dev_c2_l025", None, "priv"),
      ("CL0, dev_C2 L0,25", "p5_cl0_dev_c2_l025", "p5_wcl0_dev_c2_l025", None, "modular")]
fig, ax = plt.subplots(figsize=(7.2, 3.4))
for i, (lab, a, b, _, kind) in enumerate(w1):
    y = len(w1) - 1 - i
    sa, na = count(run(a)); sb, nb = count(run(b))
    xa, xb = 100 * sa / na, 100 * sb / nb
    ax.plot([xa, xb], [y, y], color=C[kind], lw=2, zorder=2)
    ax.scatter([xa], [y], s=60, facecolor="white", edgecolor=C[kind], linewidth=2, zorder=3)
    ax.scatter([xb], [y], s=64, color=C[kind], edgecolor="white", linewidth=1.5, zorder=3)
    ax.text(101.5, y, f"{sa}/{na} → {sb}/{nb}", va="center", fontsize=9, color=INK)
ax.set_yticks(range(len(w1))); ax.set_yticklabels([w[0] for w in w1][::-1])
ax.set_xlim(0, 100); ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_xlabel("Tỉ lệ thành công (%) — vòng rỗng: gốc, chấm đặc: có W1 (cùng cảnh)", fontsize=9)
fig.subplots_adjust(left=0.30, right=0.84, top=0.97, bottom=0.17)
fig.savefig(os.path.join(OUT, "fig_w1_effect.png")); plt.close(fig); print("wrote fig_w1_effect.png")

# ---- Fig 6: the 30-paper benchmark's DEV grid (40 pairs) with our ACT_old s1000 (E14 runs on the same pairs)
K40 = {(f"dev_C{c}_{i:03d}", L) for c in (0, 2) for i in range(1, 11) for L in ("0", "0.25")}
def bench(d, m=None):
    s = n = 0
    for dd in d:
        a, b = count(os.path.join(BENCH, dd, "trials.csv"), method=m, keys=K40); s += a; n += b
    return s, n
B2 = ["v2_baselines_dev_20261108", "v2_baselines_dev_cont_20261108"]
def ours(names):
    seen = {}
    for nm in names:
        for r in csv.DictReader(open(run(nm))):
            k = (r["arrangement_id"], r["L"])
            if r["valid"] == "1" and k in K40 and k not in seen:
                seen[k] = r["success"] == "1"
    return sum(seen.values()), len(seen)
bm = [("ORACLE (benchmark)", *bench(B2, "ORACLE"), "priv"), ("CL0 (benchmark)", *bench(B2, "CL0"), "modular"),
      ("ACT_old s1000 (đồ án này)", *ours(["e14_act_i2_dev", "e14_act_i2_dev2"]), "act"),
      ("P17 ODIL (thành phần)", *bench(["v2_p17_odil_stage1_dev"]), "paper"), ("P19 ACT (port gốc)", *bench(["v2_p19_act_dev"]), "paper"),
      ("P05 CNS (thành phần)", *bench(["v2_p05_cns_frontend_dev"]), "paper"), ("P07 ViT-VS (thành phần)", *bench(["v2_p07_vitvs_dev"]), "paper")]
dotplot(bm, "Benchmark 30 bài báo: 40 lượt DEV chung (dev_C0, dev_C2 × L0, L0,25)", "fig_benchmark_dev.png",
        legend=[("modular", "Mô-đun"), ("act", "ACT (đồ án)"), ("paper", "Bài báo tái lập"), ("priv", "Đặc quyền")])

# ---- Fig 7: system diagram of ACT_I2 (boxes)
fig, ax = plt.subplots(figsize=(7.2, 3.0)); ax.set_xlim(0, 100); ax.set_ylim(0, 44); ax.axis("off")
def box(x, y, w, h, title, sub, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc="white", ec=col, lw=1.6))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", fontsize=8.6, weight="bold", color=INK)
    ax.text(x + w / 2, y + h - 7.4, sub, ha="center", va="top", fontsize=7.4, color=INK2, linespacing=1.35)
def arrow(x1, y1, x2, y2, lab=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    if lab:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.0, lab, ha="center", va="bottom", fontsize=7, color=INK2)
box(1, 28, 20, 15, "Camera RGB cố định", "640×360, 30 khung/s\nảnh tại t_chụp", C["modular"])
box(1, 9, 20, 15, "Trạng thái I2 của EE", "[x_b, y_b, z, cos2ψ,\nsin2ψ, kẹp] tại t_chụp", C["modular"])
box(28, 9, 22, 34, "ACT (LeRobot 0.6.1)", "ResNet-18 + Transformer\nCVAE, chunk 100\n\nđầu ra: 100 mục tiêu EE\ntương đối, trong hệ băng", C["act"])
box(57, 9, 22, 34, "Bộ thực thi I2", "cộng s(t) − s(t_chụp)\nđổi về hệ thế giới\n\nIK góc chúc cố định\ngiới hạn khớp, 50 Hz", C["priv"])
box(85, 18, 14, 16, "SO-101", "5 khớp + kẹp\n(Isaac Sim)", INK2)
arrow(21.4, 35, 27.6, 30); arrow(21.4, 16, 27.6, 21); arrow(50.4, 26, 56.6, 26, "chunk"); arrow(79.4, 26, 84.6, 26, "góc khớp")
ax.plot([92, 92, 11, 11], [17.6, 3, 3, 8.6], color=INK2, lw=1.0, ls=(0, (3, 2)))
ax.annotate("", xy=(11, 8.6), xytext=(11, 6), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.0))
ax.text(52, 3.6, "khớp đo được → FK → trạng thái I2 ở lần chụp sau (kế hoạch lại sau 100 khung)", ha="center", va="bottom", fontsize=7, color=INK2)
fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig.savefig(os.path.join(OUT, "fig_act_i2_pipeline.png")); plt.close(fig); print("wrote fig_act_i2_pipeline.png")

# ---- existing renders
shutil.copy(os.path.join(ARENA, "runs", "e5", "objects_sheet.png"), os.path.join(OUT, "fig_objects.png"))
shutil.copy(os.path.join(ARENA, "runs", "p1_video_001", "lift_sheet_2.43-3.30s.png"), os.path.join(OUT, "fig_failure_seq.png"))
print("copied renders")
