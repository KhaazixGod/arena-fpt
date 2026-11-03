#!/usr/bin/env python3
"""Phân tích CSV lượt thử cho các cổng G0 / G2 của KE_HOACH_HUONG_1.md.

Chỉ dùng thư viện chuẩn (Python >= 3.8). Ví dụ:
  python3 g0_analyze.py cells  trials.csv
  python3 g0_analyze.py g0     trials.csv --method CL0
  python3 g0_analyze.py g2     trials.csv --base CL0 --chal ACT_I2 --cell novel_C2
  python3 g0_analyze.py selftest

CSV (dòng bắt đầu bằng # bị bỏ qua):
  trial_id,method,cell,arrangement_id,success,valid,fail_cause,note
  success: 1/0.  valid: 1/0 (0 = lỗi phần cứng/ngắt khẩn cấp -> loại và CHẠY LẠI; mọi thứ khác phải tính).
  fail_cause (chỉ điền khi success=0): merge | seg_miss | grasp_point | timing | calib | slip | collision | other
Ngưỡng nằm ngay dưới đây: sửa TRƯỚC lượt thử đầu tiên rồi đóng băng (sha256sum) cùng file kế hoạch.
"""
import argparse, csv, math, random, sys
from collections import defaultdict, Counter

Z = 1.959964
GO_MAX = 0.70          # G0: GO nếu CL ở ô quyết định (novel_C2) thành công <= ngưỡng này ...
PIVOT_MIN = 0.85       # ... PIVOT nếu >= ngưỡng này; ở giữa = mơ hồ
SANITY_MIN = 0.80      # G0: ô kiểm hệ thống (seen_C0) phải >= ngưỡng này, nếu không là lỗi hệ thống, không phải "headroom"
ATTRIB_MIN = 0.50      # G0: tối thiểu phần thất bại do nhận thức / chọn điểm kẹp
ATTRIB = {"merge", "seg_miss", "grasp_point"}
CAUSES = {"", "none", "merge", "seg_miss", "grasp_point", "timing", "calib", "slip", "collision", "other"}
G0_MIN_N_PRIMARY, G0_MIN_N_EASY = 30, 20
G2_MIN_DIFF, G2_MIN_ABS, G2_MIN_PAIRS, ALPHA = 0.15, 0.60, 60, 0.05
BOOT, SEED = 10000, 12345


# ------------------------------------------------------------------ thống kê
def wilson(k, n, z=Z):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def binom_cdf(k, n, p=0.5):
    if k < 0:
        return 0.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, min(k, n) + 1))


def mcnemar_exact(b, c):
    """p hai phía chính xác (kiểm định nhị thức trên các cặp bất đồng). b: chỉ chal thắng; c: chỉ base thắng."""
    m = b + c
    if m == 0:
        return 1.0
    return min(1.0, 2 * binom_cdf(min(b, c), m, 0.5))


def boot_ci(diffs, reps=BOOT, seed=SEED):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


# ------------------------------------------------------------------ đọc dữ liệu
def read_trials(path):
    rows, warns = [], []
    with open(path, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    for i, r in enumerate(csv.DictReader(lines), start=2):
        try:
            s = int(r["success"])
            v = int(r.get("valid", "1") or 1)
        except Exception:
            warns.append(f"dòng {i}: success/valid không phải 0/1 -> bỏ")
            continue
        if s not in (0, 1) or v not in (0, 1):
            warns.append(f"dòng {i}: success/valid phải là 0/1 -> bỏ")
            continue
        fc = (r.get("fail_cause") or "").strip()
        if fc not in CAUSES:
            warns.append(f"dòng {i}: fail_cause '{fc}' không có trong danh sách -> tính là 'other'")
            fc = "other"
        if s == 0 and v == 1 and fc in ("", "none"):
            warns.append(f"dòng {i}: thất bại hợp lệ nhưng thiếu fail_cause -> tính là 'other'")
            fc = "other"
        rows.append(dict(trial=r.get("trial_id", str(i)), method=r["method"].strip(), cell=r["cell"].strip(),
                         arr=(r.get("arrangement_id") or "").strip(), s=s, valid=v, cause=fc))
    return rows, warns


def counts(rows, method, cell):
    sel = [r for r in rows if r["method"] == method and r["cell"] == cell and r["valid"] == 1]
    return len(sel), sum(r["s"] for r in sel), sel


# ------------------------------------------------------------------ lệnh
def cmd_cells(a):
    rows, warns = read_trials(a.file)
    for w in warns:
        print("CẢNH BÁO:", w)
    inval = Counter((r["method"], r["cell"]) for r in rows if r["valid"] == 0)
    keys = sorted({(r["method"], r["cell"]) for r in rows})
    print(f"{'phương pháp':<12}{'ô':<14}{'n':>4}{'k':>4}{'tỉ lệ':>8}   Wilson 95%      lượt không hợp lệ (đã loại, phải chạy lại)")
    for m, c in keys:
        n, k, _ = counts(rows, m, c)
        lo, hi = wilson(k, n) if n else (float("nan"),) * 2
        print(f"{m:<12}{c:<14}{n:>4}{k:>4}{(k / n if n else float('nan')):>8.1%}   [{lo:5.1%}, {hi:5.1%}]   {inval[(m, c)]}")


def cmd_g0(a):
    rows, warns = read_trials(a.file)
    for w in warns:
        print("CẢNH BÁO:", w)
    n_e, k_e, _ = counts(rows, a.method, a.easy)
    n_p, k_p, sel_p = counts(rows, a.method, a.primary)
    print(f"G0 cho phương pháp {a.method}")
    if n_e == 0 or n_p == 0:
        print(f"-> THIẾU DỮ LIỆU: ô kiểm hệ thống '{a.easy}' n={n_e}, ô quyết định '{a.primary}' n={n_p}")
        return 2
    lo_e, hi_e = wilson(k_e, n_e)
    lo_p, hi_p = wilson(k_p, n_p)
    print(f"  ô kiểm hệ thống {a.easy:<10} {k_e}/{n_e} = {k_e / n_e:.1%}  Wilson [{lo_e:.1%}, {hi_e:.1%}]  (cần >= {SANITY_MIN:.0%})")
    print(f"  ô quyết định    {a.primary:<10} {k_p}/{n_p} = {k_p / n_p:.1%}  Wilson [{lo_p:.1%}, {hi_p:.1%}]")
    fails = [r for r in sel_p if r["s"] == 0]
    cc = Counter(r["cause"] for r in fails)
    attr = sum(v for k, v in cc.items() if k in ATTRIB)
    frac = attr / len(fails) if fails else float("nan")
    print(f"  nguyên nhân thất bại ở ô quyết định: {dict(cc)}  | do nhận thức/chọn điểm kẹp: {attr}/{len(fails)}"
          + (f" = {frac:.0%} (cần >= {ATTRIB_MIN:.0%})" if fails else ""))
    kgo = math.floor(GO_MAX * n_p + 1e-9)
    kpv = math.ceil(PIVOT_MIN * n_p - 1e-9)
    if n_e < G0_MIN_N_EASY or n_p < G0_MIN_N_PRIMARY:
        print(f"-> CHƯA ĐỦ LƯỢT (ô kiểm hệ thống >= {G0_MIN_N_EASY}, ô quyết định >= {G0_MIN_N_PRIMARY}). Chạy thêm rồi phân tích lại.")
        return 3
    if k_e / n_e < SANITY_MIN:
        print("-> SỬA HỆ THỐNG TRƯỚC: baseline chưa đạt ở ô kiểm hệ thống, nên thất bại ở ô khó chưa nói lên gì về 'chỗ trống để cải thiện'.")
        return 4
    if k_p >= kpv:
        print(f"-> PIVOT (k={k_p} >= {kpv}/{n_p}): cổ điển đã đủ tốt ở ô quyết định. Không có chỗ cho claim 'học hơn cổ điển'. "
              "Chuyển sang hướng 4 (nghiên cứu đối chứng), dùng lại toàn bộ hạ tầng.")
        return 0
    if k_p <= kgo:
        if fails and frac < ATTRIB_MIN:
            print(f"-> GO CÓ ĐIỀU KIỆN (k={k_p} <= {kgo}/{n_p}) nhưng thất bại chủ yếu KHÔNG do nhận thức/chọn điểm kẹp. "
                  "Chính sách học khó cứu được lỗi này (cùng phần cứng) -> sửa nguyên nhân gốc, chạy lại G0.")
            return 0
        print(f"-> GO (k={k_p} <= {kgo}/{n_p}, thất bại chủ yếu do nhận thức/chọn điểm kẹp): có chỗ trống cho phương pháp học.")
        return 0
    print(f"-> MƠ HỒ ({kgo} < k={k_p} < {kpv} trên {n_p}): chạy CL-1 (mô-đun + phân đoạn nền tảng) ở cùng ô, "
          "áp lại quy tắc cho CL-1; baseline ghi nhận là baseline mạnh nhất trong hai.")
    return 0


def cmd_g2(a):
    rows, warns = read_trials(a.file)
    for w in warns:
        print("CẢNH BÁO:", w)
    by = defaultdict(lambda: defaultdict(list))
    unpaired = 0
    inval_pairs = set()
    for r in rows:
        if r["cell"] != a.cell or r["method"] not in (a.base, a.chal):
            continue
        if r["valid"] == 0:
            inval_pairs.add(r["arr"])
            continue
        by[r["arr"]][r["method"]].append(r["s"])
    pairs = []          # (arr, base_s, chal_s)
    for arr, d in by.items():
        nb, nc = len(d[a.base]), len(d[a.chal])
        for i in range(min(nb, nc)):
            pairs.append((arr, d[a.base][i], d[a.chal][i]))
        unpaired += abs(nb - nc)
    N = len(pairs)
    print(f"G2 ô '{a.cell}': baseline {a.base} vs đối chứng {a.chal}")
    if N == 0:
        print("-> không có cặp nào (cần cùng arrangement_id cho cả hai phương pháp)")
        return 2
    b = sum(1 for _, s0, s1 in pairs if s1 == 1 and s0 == 0)
    c = sum(1 for _, s0, s1 in pairs if s1 == 0 and s0 == 1)
    k0 = sum(s0 for _, s0, _ in pairs)
    k1 = sum(s1 for _, _, s1 in pairs)
    diff = (b - c) / N
    p = mcnemar_exact(b, c)
    per = defaultdict(list)
    for arr, s0, s1 in pairs:
        per[arr].append(s1 - s0)
    d_arr = [sum(v) / len(v) for v in per.values()]
    lo, hi = boot_ci(d_arr)
    l0, h0 = wilson(k0, N)
    l1, h1 = wilson(k1, N)
    print(f"  cặp hợp lệ N={N} (lẻ cặp bị bỏ: {unpaired}; sắp xếp có lượt không hợp lệ cần chạy lại: {len(inval_pairs)})")
    print(f"  {a.base}: {k0}/{N} = {k0 / N:.1%} [{l0:.1%}, {h0:.1%}]")
    print(f"  {a.chal}: {k1}/{N} = {k1 / N:.1%} [{l1:.1%}, {h1:.1%}]")
    print(f"  cặp bất đồng: chỉ {a.chal} thắng b={b}, chỉ {a.base} thắng c={c}; hiệu = {diff:+.1%}; "
          f"McNemar chính xác p={p:.4f}; bootstrap theo sắp xếp 95% [{lo:+.1%}, {hi:+.1%}]")
    if N < a.min_pairs:
        print(f"-> CHƯA ĐỦ CẶP (cần >= {a.min_pairs}). Đừng kết luận.")
        return 3
    if diff >= G2_MIN_DIFF - 1e-9 and p <= ALPHA and k1 / N >= G2_MIN_ABS:
        print(f"-> GO: hiệu >= +{G2_MIN_DIFF:.0%}, p <= {ALPHA}, và {a.chal} >= {G2_MIN_ABS:.0%} tuyệt đối.")
    elif diff > 0 and p <= ALPHA:
        why = []
        if diff < G2_MIN_DIFF:
            why.append(f"hiệu {diff:+.1%} < +{G2_MIN_DIFF:.0%}")
        if k1 / N < G2_MIN_ABS:
            why.append(f"{a.chal} {k1 / N:.0%} < {G2_MIN_ABS:.0%} tuyệt đối")
        print("-> THẮNG NHỎ (khác biệt có ý nghĩa nhưng chưa đạt ngưỡng ghi trước: " + "; ".join(why) + "): báo cáo trung thực, không gọi là 'vượt'.")
    elif hi < G2_MIN_DIFF:
        print(f"-> NO-GO: dữ liệu loại trừ mức chênh +{G2_MIN_DIFF:.0%} (cận trên bootstrap {hi:+.1%}). Báo cáo như kết quả đối chứng.")
    else:
        print("-> KHÔNG KẾT LUẬN: khoảng tin cậy còn chứa cả 0 lẫn mức mục tiêu; thêm cặp nếu còn ngân sách, nếu không thì báo cáo đúng như vậy.")
    return 0


# ------------------------------------------------------------------ tự kiểm
def _fake(rng, method, cell, n, p, causes=None, arr0=0):
    out = []
    for i in range(n):
        s = 1 if rng.random() < p else 0
        fc = ""
        if not s:
            fc = rng.choice(causes or ["merge", "seg_miss", "grasp_point"])
        out.append(dict(trial=f"{method}-{cell}-{i}", method=method, cell=cell, arr=str(arr0 + i), s=s, valid=1, cause=fc))
    return out


def _write(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trial_id", "method", "cell", "arrangement_id", "success", "valid", "fail_cause", "note"])
        for r in rows:
            w.writerow([r["trial"], r["method"], r["cell"], r["arr"], r["s"], r["valid"], r["cause"], ""])


def selftest(_a=None):
    import io, os, tempfile, contextlib
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ok   " if cond else "  LỖI  ") + name)
        ok = ok and cond

    try:
        from scipy import stats as st
        for k, n in [(0, 20), (1, 20), (14, 20), (21, 30), (30, 30), (45, 60)]:
            ref = st.binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
            lo, hi = wilson(k, n)
            check(f"Wilson {k}/{n} khớp scipy", abs(lo - ref.low) < 1e-5 and abs(hi - ref.high) < 1e-5)
        for b, c in [(0, 0), (3, 3), (12, 2), (18, 4), (9, 3), (1, 10)]:
            m = b + c
            ref = 1.0 if m == 0 else st.binomtest(min(b, c), m, 0.5).pvalue
            check(f"McNemar b={b},c={c} khớp scipy ({mcnemar_exact(b, c):.4f})", abs(mcnemar_exact(b, c) - ref) < 1e-9)
    except ImportError:
        print("  (không có scipy: bỏ qua so khớp scipy)")
    rng = random.Random(2026)
    d = tempfile.mkdtemp()
    scen = [
        ("GO",            0.95, 0.55, None,                "-> GO ("),
        ("PIVOT",         0.95, 0.92, None,                "-> PIVOT"),
        ("SỬA HỆ THỐNG",  0.60, 0.50, None,                "-> SỬA HỆ THỐNG TRƯỚC"),
        ("MƠ HỒ",         0.95, 0.77, None,                "-> MƠ HỒ"),
        ("GO CÓ ĐIỀU KIỆN", 0.95, 0.50, ["calib", "timing"], "-> GO CÓ ĐIỀU KIỆN"),
    ]
    for name, pe, pp, causes, expect in scen:
        # chọn hạt giống sao cho số quan sát đúng kịch bản (kiểm logic, không kiểm ngẫu nhiên)
        for attempt in range(200):
            rows = _fake(rng, "CL0", "seen_C0", 20, pe) + _fake(rng, "CL0", "novel_C2", 30, pp, causes)
            n_e, k_e, _ = counts(rows, "CL0", "seen_C0")
            n_p, k_p, _ = counts(rows, "CL0", "novel_C2")
            kp = k_p / n_p
            good = {"GO": kp <= 0.70, "PIVOT": kp >= 0.85, "SỬA HỆ THỐNG": k_e / n_e < 0.80,
                    "MƠ HỒ": 0.70 < kp < 0.85, "GO CÓ ĐIỀU KIỆN": kp <= 0.70}[name]
            if name != "SỬA HỆ THỐNG":
                good = good and k_e / n_e >= 0.80
            if good:
                break
        path = os.path.join(d, f"{name}.csv")
        _write(rows, path)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_g0(argparse.Namespace(file=path, method="CL0", easy="seen_C0", primary="novel_C2"))
        out = buf.getvalue()
        check(f"G0 kịch bản {name}: in '{expect}'", expect in out)
    # G2 dựng trực tiếp theo số cặp bất đồng
    def paired(nb_only_chal, nb_only_base, both, neither):
        rows, i = [], 0
        for s0, s1, cnt in ((0, 1, nb_only_chal), (1, 0, nb_only_base), (1, 1, both), (0, 0, neither)):
            for _ in range(cnt):
                rows.append(dict(trial=f"b{i}", method="CL0", cell="novel_C2", arr=str(i), s=s0, valid=1, cause="" if s0 else "merge"))
                rows.append(dict(trial=f"c{i}", method="ACT", cell="novel_C2", arr=str(i), s=s1, valid=1, cause="" if s1 else "merge"))
                i += 1
        return rows
    for name, args, expect in [
        ("GO", (18, 4, 22, 16), "-> GO:"),                 # N=60, hiệu +23.3%, ACT = 40/60 = 66.7%
        ("THẮNG NHỎ", (12, 3, 30, 15), "-> THẮNG NHỎ"),     # +15% p~0.035 nhưng hiệu 15% đúng ngưỡng -> GO? kiểm bên dưới
        ("KHÔNG KẾT LUẬN", (8, 5, 30, 17), "-> KHÔNG KẾT LUẬN"),
        ("NO-GO", (3, 12, 30, 15), "-> NO-GO"),
    ]:
        rows = paired(*args)
        path = os.path.join(d, f"g2_{name}.csv")
        _write(rows, path)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_g2(argparse.Namespace(file=path, base="CL0", chal="ACT", cell="novel_C2", min_pairs=60))
        out = buf.getvalue()
        if name == "THẮNG NHỎ":
            # (12,3): hiệu = 9/60 = +15.0% (đúng ngưỡng) -> quy tắc ghi trước cho GO nếu p<=0.05; đổi sang (10,3) = +11.7%
            rows = paired(10, 2, 33, 15)
            _write(rows, path)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cmd_g2(argparse.Namespace(file=path, base="CL0", chal="ACT", cell="novel_C2", min_pairs=60))
            out = buf.getvalue()
        check(f"G2 kịch bản {name}: in '{expect}'", expect in out)
    print("TẤT CẢ OK" if ok else "CÓ LỖI")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("cells"); p.add_argument("file"); p.set_defaults(fn=cmd_cells)
    p = sub.add_parser("g0"); p.add_argument("file"); p.add_argument("--method", default="CL0")
    p.add_argument("--easy", default="seen_C0"); p.add_argument("--primary", default="novel_C2"); p.set_defaults(fn=cmd_g0)
    p = sub.add_parser("g2"); p.add_argument("file"); p.add_argument("--base", required=True); p.add_argument("--chal", required=True)
    p.add_argument("--cell", default="novel_C2"); p.add_argument("--min-pairs", type=int, default=G2_MIN_PAIRS); p.set_defaults(fn=cmd_g2)
    p = sub.add_parser("selftest"); p.set_defaults(fn=selftest)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
