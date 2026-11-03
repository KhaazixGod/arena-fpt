#!/usr/bin/env python3
"""Tính mọi bảng thống kê / ngân sách cho KE_HOACH_HUONG_1.md (không gõ tay số).

Chạy:  python stats_tables.py        (cần numpy + scipy)
Ra:    res/md/*.md  (bảng markdown)  và  res/scalars.json  (số đơn lẻ)
Giả định đánh dấu [giả định] nằm ở khối PARAMS bên dưới: sửa rồi chạy lại là bảng đổi theo.
"""
import json, math, os
import numpy as np
from scipy import stats
from scipy.special import gammaln

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "res")
os.makedirs(os.path.join(OUT, "md"), exist_ok=True)

# ----------------------------------------------------------------- PARAMS
ALPHA, POWER = 0.05, 0.80
NS = [20, 30, 40, 60]               # số lượt mỗi ô
RHO = 0.3                           # [giả định] tương quan thành công giữa 2 phương pháp trên CÙNG sắp xếp
G0_GO, G0_PIVOT = 0.70, 0.85        # ngưỡng G0 (do mình chọn; bạn chỉnh được TRƯỚC khi chạy)
MIN_PER_TRIAL = 1.0                 # [giả định] phút/lượt = đặt vật + chạy + dọn
OVERHEAD = 1.3                      # [giả định] hao phí: hiệu chuẩn, lỗi phần cứng, chạy lại lượt không hợp lệ
SEC_PER_DEMO = 40                   # [giả định] 15 s tập + 25 s dọn/đặt lại
TRAIN_H_RANGE = (2, 8)              # [giả định rộng] giờ GPU/lần huấn luyện trên RTX 3070 Ti; ĐO ở G1a
# sim (chỉ để nói "không làm lúc này"): số đo trong sandbox 2 core
SIM = dict(eps=5000, t_ep=8.0, fps=15, phys_s_per_simsec=0.19, render_s_per_frame=0.022, cores=2)

# ----------------------------------------------------------------- helpers
def c(x, nd=1, sign=False):
    """Định dạng kiểu Việt: dấu phẩy, làm tròn nửa ra xa 0, dấu trừ thật."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    y = round(x + math.copysign(1e-9, x), nd)
    if y == 0:
        y = 0.0
    s = f"{abs(y):.{nd}f}".replace(".", ",")
    if y < 0:
        return "−" + s
    return ("+" + s) if (sign and y > 0) else s

def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, ctr - h), min(1.0, ctr + h)

def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out) + "\n"

SC = {}   # scalars

# ----------------------------------------------------------------- T1: Wilson
rows = []
for n in NS:
    r = [n]
    for p in (0.5, 0.7, 0.9):
        k = int(round(p * n))
        lo, hi = wilson(k, n)
        r.append(f"{c(100*lo,0)}–{c(100*hi,0)} (±{c(50*(hi-lo),0)})")
    rows.append(r)
T1 = md_table(["Số lượt / ô", "quan sát 50%", "quan sát 70%", "quan sát 90%"], rows)
SC["hw30_70"] = 50 * (wilson(21, 30)[1] - wilson(21, 30)[0])
SC["hw60_70"] = 50 * (wilson(42, 60)[1] - wilson(42, 60)[0])

# ----------------------------------------------------------------- power: independent (Fisher exact)
_fisher_cache = {}
def fisher_reject(n):
    """M[x1, x2] = True nếu Fisher hai phía p <= ALPHA (x1: baseline, x2: đối chứng; mỗi bên n lượt)."""
    if n in _fisher_cache:
        return _fisher_cache[n]
    M = np.zeros((n + 1, n + 1), bool)
    for s in range(0, 2 * n + 1):
        j = np.arange(max(0, s - n), min(n, s) + 1)          # x2
        pm = stats.hypergeom.pmf(j, 2 * n, s, n)              # P(X2 = j | tổng thành công = s)
        order = np.argsort(pm)
        srt = pm[order]
        cs = np.cumsum(srt)
        pos = np.searchsorted(srt, pm * (1 + 1e-7), side="right") - 1
        pval = cs[pos]                                        # tổng pmf của các bảng không khả dĩ hơn bảng quan sát
        M[s - j, j] = pval <= ALPHA
    _fisher_cache[n] = M
    return M

def power_indep(n, pC, pL):
    pm1 = stats.binom.pmf(np.arange(n + 1), n, pC)
    pm2 = stats.binom.pmf(np.arange(n + 1), n, pL)
    return float((np.outer(pm1, pm2) * fisher_reject(n)).sum())

# ----------------------------------------------------------------- power: paired (exact McNemar, trinomial)
_mc_cache = {}
def reject_mask(n, min_diff=0.0):
    """M[b, c]: b = số cặp đối chứng thắng, c = số cặp baseline thắng; McNemar chính xác hai phía p <= ALPHA và (b-c)/n >= min_diff."""
    key = (n, min_diff)
    if key in _mc_cache:
        return _mc_cache[key]
    b = np.arange(n + 1)[:, None]
    cc = np.arange(n + 1)[None, :]
    m = b + cc
    mn = np.minimum(b, cc)
    p = np.minimum(1.0, 2 * stats.binom.cdf(mn, np.maximum(m, 1), 0.5))
    p = np.where(m == 0, 1.0, p)
    M = (m <= n) & (p <= ALPHA) & ((b - cc) / n >= min_diff - 1e-12)
    _mc_cache[key] = M
    return M

def joint(pC, pL, rho):
    p11 = pL * pC + rho * math.sqrt(pL * (1 - pL) * pC * (1 - pC))
    p10, p01 = pL - p11, pC - p11
    if p10 < -1e-12 or p01 < -1e-12 or 1 - p11 - p10 - p01 < -1e-12:
        return None
    return max(p10, 0.0), max(p01, 0.0)

def power_paired(n, pC, pL, rho=RHO, min_diff=0.0):
    pj = joint(pC, pL, rho)
    if pj is None:
        return float("nan")
    p10, p01 = pj
    p00 = max(1 - p10 - p01, 0.0)
    b = np.arange(n + 1)[:, None]
    cc = np.arange(n + 1)[None, :]
    r = n - b - cc
    ok = r >= 0
    rr = np.where(ok, r, 0)
    with np.errstate(all="ignore"):
        lp = gammaln(n + 1) - gammaln(b + 1) - gammaln(cc + 1) - gammaln(rr + 1)
        lp = lp + np.where(b > 0, b * np.log(p10), 0.0) + np.where(cc > 0, cc * np.log(p01), 0.0) \
                + np.where(rr > 0, rr * np.log(p00), 0.0)
        P = np.where(ok, np.exp(lp), 0.0)
    return float((P * reject_mask(n, min_diff)).sum())

def mdd(pC, n, fn):
    for k in range(1, 101):
        pL = round(pC + k / 100, 2)
        if pL > 1.0:
            return None
        if fn(n, pC, pL) >= POWER:
            return pL - pC
    return None

def n_needed(pC, pL, fn, nmax=400):
    for n in range(10, nmax + 1):
        if fn(n, pC, pL) >= POWER:
            return n
    return None

# ----------------------------------------------------------------- T2: min detectable difference
rows = []
for n in NS:
    r = [n]
    for pC in (0.5, 0.7):
        d_i = mdd(pC, n, power_indep)
        d_p = mdd(pC, n, power_paired)
        r.append(f"{c(100*d_i,0,True) if d_i is not None else '—'}" + " / " + f"{c(100*d_p,0,True) if d_p is not None else '—'}")
    rows.append(r)
T2 = md_table(["Số lượt / ô", "baseline thật 50%: độc lập / ghép cặp", "baseline thật 70%: độc lập / ghép cặp"], rows)
for n in NS:
    SC[f"mdd_ind_{n}_50"] = 100 * (mdd(0.5, n, power_indep) or float("nan"))
    SC[f"mdd_pair_{n}_50"] = 100 * (mdd(0.5, n, power_paired) or float("nan"))
    SC[f"mdd_ind_{n}_70"] = 100 * (mdd(0.7, n, power_indep) or float("nan"))
    SC[f"mdd_pair_{n}_70"] = 100 * (mdd(0.7, n, power_paired) or float("nan"))

# số lượt cần để phát hiện đúng +15 / +20 điểm
rows = []
for pC in (0.5, 0.6, 0.7):
    r = [f"{c(100*pC,0)}%"]
    for gap in (0.15, 0.20):
        pL = round(pC + gap, 2)
        ni = n_needed(pC, pL, power_indep, 300)
        npd = n_needed(pC, pL, power_paired, 300)
        r.append(f"{ni if ni else '>300'} / {npd if npd else '>300'}")
    rows.append(r)
T2B = md_table(["baseline thật", "cần để thấy +15 điểm (độc lập / ghép cặp)", "cần để thấy +20 điểm (độc lập / ghép cặp)"], rows)
SC["need_15_60"] = n_needed(0.6, 0.75, power_paired, 300)
SC["need_15_60_ind"] = n_needed(0.6, 0.75, power_indep, 300)

# ----------------------------------------------------------------- T3: P(GO ở G2) theo hiệu thật (n = 60 cặp, quy tắc đúng như tiêu chí: hiệu quan sát ≥ +15 và McNemar p ≤ 0,05)
N_PRIMARY = 60
rows = []
for gap in (0.0, 0.10, 0.15, 0.20, 0.25, 0.30):
    r = [c(100 * gap, 0, True)]
    for pC in (0.5, 0.6, 0.7):
        pL = round(pC + gap, 2)
        if gap == 0.0:
            # độ lớn I (dương tính giả): hiệu thật 0, cùng biên
            val = power_paired(N_PRIMARY, pC, pC, RHO, 0.15)
        else:
            val = power_paired(N_PRIMARY, pC, pL, RHO, 0.15)
        r.append("n/a" if (val != val) else f"{c(100*val,0)}%")
    rows.append(r)
T3 = md_table(["hiệu thật (điểm)", "baseline thật 50%", "baseline thật 60%", "baseline thật 70%"], rows)
SC["pgo_20_60"] = 100 * power_paired(N_PRIMARY, 0.6, 0.8, RHO, 0.15)
SC["pgo_15_60"] = 100 * power_paired(N_PRIMARY, 0.6, 0.75, RHO, 0.15)
SC["pgo_0_60"] = 100 * power_paired(N_PRIMARY, 0.6, 0.6, RHO, 0.15)

# ----------------------------------------------------------------- T4: đặc tính vận hành của G0 (chỉ phần quy tắc theo tỉ lệ thành công)
rows = []
for p in (0.5, 0.6, 0.7, 0.8, 0.9):
    r = [f"{c(100*p,0)}%"]
    for n in (20, 30):
        kgo = math.floor(G0_GO * n + 1e-9)
        kpv = math.ceil(G0_PIVOT * n - 1e-9)
        p_go = stats.binom.cdf(kgo, n, p)
        p_pv = 1 - stats.binom.cdf(kpv - 1, n, p)
        p_am = 1 - p_go - p_pv
        r.append(f"{c(100*p_go,0)} / {c(100*p_am,0)} / {c(100*p_pv,0)}")
    rows.append(r)
T4 = md_table(["baseline thật ở ô chính", "n = 20: GO / mơ hồ / PIVOT (%)", "n = 30: GO / mơ hồ / PIVOT (%)"], rows)
for n in (20, 30):
    SC[f"g0_kgo_{n}"] = math.floor(G0_GO * n + 1e-9)
    SC[f"g0_kpv_{n}"] = math.ceil(G0_PIVOT * n - 1e-9)
SC["g0_false_go_80_30"] = 100 * stats.binom.cdf(SC["g0_kgo_30"], 30, 0.8)
SC["g0_go_60_30"] = 100 * stats.binom.cdf(SC["g0_kgo_30"], 30, 0.6)
SC["g0_pivot_90_30"] = 100 * (1 - stats.binom.cdf(SC["g0_kpv_30"] - 1, 30, 0.9))

# ----------------------------------------------------------------- T5: tỉ số dẫn trước L = v*tau/w
rows = []
for w in (30, 50):
    for tau in (0.3, 0.5):
        r = [f"{w} mm", f"{c(tau,1)} s"]
        for L in (0.25, 0.5, 1.0):
            r.append(f"{c(L*w/tau,0)}")
        rows.append(r)
T5 = md_table(["độ mở kẹp hữu dụng w", "trễ vòng τ", "v cho L = 0,25 (mm/s)", "L = 0,5", "L = 1,0"], rows)

# ----------------------------------------------------------------- T6: ngân sách robot thật
def hours(trials):
    return trials * MIN_PER_TRIAL * OVERHEAD / 60.0

g0 = dict(easy_C0=20, hard_C0=20, hard_C2=30, hard_C3=20)
G0_TR = sum(g0.values())
G1A_TR = 30
G1B_TR = 2 * 30
n_p, n_o = 60, 30
# gói tối thiểu
G2_MIN = 2 * (n_p + 3 * n_o)                  # ô chính + 3 ô phụ (seen_C0, novel_C0, novel_C3), 2 phương pháp
G3_MIN = 3 * 3 * 30 + 3 * 30 + 3 * 30         # giao diện(3) x tốc độ(3), lớp chính sách(3), co giãn dữ liệu(3)
MIN_TR = G0_TR + G1A_TR + G1B_TR + G2_MIN + G3_MIN
# gói đầy đủ
G2_FULL = 2 * (n_p + 7 * n_o)                 # 8 ô, 2 phương pháp
G2_FULL_CL1 = 3 * (n_p + 7 * n_o)             # thêm CL-1
G3_FULL = G3_MIN + 2 * 3 * 30                 # thêm hạt giống thứ 2 cho 3 lớp chính sách, thêm biến thể demo tĩnh
FULL_TR = G0_TR + G1A_TR + G1B_TR + G2_FULL_CL1 + G3_FULL
rows = [
    ["G0 – baseline cổ điển (4 ô)", G0_TR, c(hours(G0_TR), 1)],
    ["G1a – học được việc cơ bản", G1A_TR, c(hours(G1A_TR), 1)],
    ["G1b – giao diện hệ quy chiếu băng, ô dễ", G1B_TR, c(hours(G1B_TR), 1)],
    ["G2 – so chính (gói tối thiểu: ô chính n=60 + 3 ô phụ n=30; 2 phương pháp)", G2_MIN, c(hours(G2_MIN), 1)],
    ["G3 – bỏ từng thành phần (giao diện×tốc độ, lớp chính sách, co giãn dữ liệu)", G3_MIN, c(hours(G3_MIN), 1)],
    ["**Tổng gói tối thiểu**", MIN_TR, "**" + c(hours(MIN_TR), 0) + "**"],
    ["Tổng gói đầy đủ (G2 đủ 8 ô + CL-1; G3 thêm hạt giống và demo tĩnh)", FULL_TR, c(hours(FULL_TR), 0)],
]
T6 = md_table(["Hạng mục", "Số lượt", "Giờ robot"], rows)
SC.update(MIN_TR=MIN_TR, FULL_TR=FULL_TR, G0_TR=G0_TR, MIN_H=hours(MIN_TR), FULL_H=hours(FULL_TR), G0_H=hours(G0_TR),
          G2_MIN_TR=G2_MIN, G3_MIN_TR=G3_MIN, EXT_TR=2 * n_p, EXT_H=hours(2 * n_p),
          MIN_PER_TRIAL=MIN_PER_TRIAL, OVERHEAD=OVERHEAD, RHO=RHO, TRAIN_LO=TRAIN_H_RANGE[0], TRAIN_HI=TRAIN_H_RANGE[1],
          G0_PIVOT_PCT=100 * G0_PIVOT, G0_GO_PCT=100 * G0_GO)

# demo + huấn luyện
DEMOS = dict(static=250, moving=150)
n_demo = sum(DEMOS.values())
demo_h = n_demo * SEC_PER_DEMO / 3600.0 * OVERHEAD
# G1a (ACT-I0, ~100 demo) + G1b (ACT-I2, ~100 demo) + 6 lần dữ liệu đầy đủ (ACT/DP/MIP x 2 hạt giống, giao diện mặc định I2;
# ACT-I2 chính là chính sách của hồ sơ ở G2) + 2 (giao diện I0, I1 với ACT) + 2 (ACT-I2 chỉ demo tĩnh, chỉ demo chạy) + 2 (co giãn 25%, 50%)
n_train = 1 + 1 + 6 + 2 + 2 + 2
rows = [
    ["Demo tĩnh (băng dừng) + lặp lại sắp xếp để đo đa mode", DEMOS["static"], c(DEMOS["static"] * SEC_PER_DEMO / 3600 * OVERHEAD, 1)],
    ["Demo băng chạy", DEMOS["moving"], c(DEMOS["moving"] * SEC_PER_DEMO / 3600 * OVERHEAD, 1)],
    ["**Tổng demo**", n_demo, "**" + c(demo_h, 1) + "**"],
]
T7 = md_table(["Thu demo", "Số demo", "Giờ (gồm hao phí)"], rows)
SC.update(N_DEMO=n_demo, DEMO_H=demo_h, N_TRAIN=n_train,
          TRAIN_H_LO=n_train * TRAIN_H_RANGE[0], TRAIN_H_HI=n_train * TRAIN_H_RANGE[1])

s = SIM
per_ep = s["t_ep"] * s["phys_s_per_simsec"] + s["t_ep"] * s["fps"] * s["render_s_per_frame"]
SC["SIM_EP_S"] = per_ep
SC["SIM_CORE_H"] = per_ep * s["eps"] / 3600
SC["SIM_WALL_H"] = per_ep * s["eps"] / 3600 / s["cores"]

# ----------------------------------------------------------------- viết ra
for name, tbl in dict(t1=T1, t2=T2, t2b=T2B, t3=T3, t4=T4, t5=T5, t6=T6, t7=T7).items():
    open(os.path.join(OUT, "md", f"{name}.md"), "w", encoding="utf-8").write(tbl)
SC = {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in SC.items()}
json.dump(SC, open(os.path.join(OUT, "scalars.json"), "w"), indent=1, ensure_ascii=False)
json.dump(dict(ALPHA=ALPHA, POWER=POWER, RHO=RHO, G0_GO=G0_GO, G0_PIVOT=G0_PIVOT, MIN_PER_TRIAL=MIN_PER_TRIAL,
               OVERHEAD=OVERHEAD, SEC_PER_DEMO=SEC_PER_DEMO, TRAIN_H_RANGE=TRAIN_H_RANGE, SIM=SIM, N_PRIMARY=N_PRIMARY),
          open(os.path.join(OUT, "params.json"), "w"), indent=1)
for name in ("t1", "t2", "t2b", "t3", "t4", "t5", "t6", "t7"):
    print(f"--- {name}"); print(open(os.path.join(OUT, "md", f"{name}.md"), encoding="utf-8").read())
print(json.dumps(SC, indent=1, ensure_ascii=False))
