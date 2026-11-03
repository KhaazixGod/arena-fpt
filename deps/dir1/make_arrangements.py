#!/usr/bin/env python3
"""Sinh sắp xếp vật ngẫu nhiên có hạt giống, để MỌI phương pháp chạy trên CÙNG sắp xếp (ghép cặp) và
để người thử không tự chọn sắp xếp "dễ". Chỉ dùng thư viện chuẩn.

  python3 make_arrangements.py --objects objects.csv --split test --clutter C2 --n 60 \
        --belt-width 200 --seed 11 --out arr_novel_C2.csv

objects.csv:  name,diameter_mm,split        (split: train | dev | test; diameter = đường kính tròn bao quanh, mm)
Ra (CSV dài): arrangement_id,first_method,idx,object,x_mm,y_mm,yaw_deg
  x = dọc băng (so với vật đầu tiên), y = ngang băng (0 = mép trái), first_method = A|B (cân bằng thứ tự chạy 2 phương pháp)
Mức clutter (khoảng cách mép–mép, mm) sửa ở bảng LEVELS cho hợp kẹp của bạn TRƯỚC khi sinh bộ test.
"""
import argparse, csv, math, random, sys

LEVELS = {            # (n vật min,max), (hở mép–mép tới một vật láng giềng: min,max mm), hở tối thiểu giữa MỌI cặp (mm)
    "C0": ((1, 1), (0, 0), 0),
    "C1": ((2, 2), (40, 80), 30),
    "C2": ((3, 4), (10, 25), 8),
    "C3": ((4, 5), (0, 3), 0),
}


def place(rng, objs, gap_rng, min_pair, belt_w, margin=10, max_try=2000):
    pts = []                                   # (x, y, r)
    for o in objs:
        r = o["d"] / 2
        for _ in range(max_try):
            if not pts:
                x, y = 0.0, rng.uniform(margin + r, belt_w - margin - r)
            else:
                bx, by, br = rng.choice(pts)
                gap = rng.uniform(*gap_rng)
                ang = rng.uniform(0, 2 * math.pi)
                dist = br + r + gap
                x, y = bx + dist * math.cos(ang), by + dist * math.sin(ang)
            if not (margin + r <= y <= belt_w - margin - r):
                continue
            ok = True
            for (px, py, pr) in pts:
                if math.hypot(x - px, y - py) < pr + r + min_pair - 1e-9:   # chồng lấn / quá sát
                    ok = False
                    break
            if ok:
                pts.append((x, y, r))
                break
        else:
            return None
    return pts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--objects", required=True)
    ap.add_argument("--split", required=True, choices=["train", "dev", "test"])
    ap.add_argument("--clutter", required=True, choices=sorted(LEVELS))
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--belt-width", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pool = []
    with open(a.objects, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
        for r in csv.DictReader(lines):
            if r["split"].strip() == a.split:
                pool.append(dict(name=r["name"].strip(), d=float(r["diameter_mm"])))
    (nlo, nhi), gap_rng, min_pair = LEVELS[a.clutter]
    if len(pool) < nhi:
        sys.exit(f"Tập '{a.split}' chỉ có {len(pool)} vật, cần >= {nhi} cho mức {a.clutter}")
    rng = random.Random(a.seed)
    rows = []
    for i in range(1, a.n + 1):
        for attempt in range(500):
            k = rng.randint(nlo, nhi)
            objs = rng.sample(pool, k)
            pts = place(rng, objs, gap_rng, min_pair, a.belt_width)
            if pts is not None:
                break
        else:
            sys.exit("Không xếp được: băng quá hẹp hoặc vật quá lớn so với mức clutter này")
        x0 = pts[0][0]
        first = rng.choice("AB")
        for j, (o, (x, y, r)) in enumerate(zip(objs, pts), start=1):
            rows.append([i, first, j, o["name"], f"{x - x0:.1f}", f"{y:.1f}", f"{rng.uniform(0, 180):.0f}"])
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arrangement_id", "first_method", "idx", "object", "x_mm", "y_mm", "yaw_deg"])
        w.writerows(rows)
    print(f"đã ghi {a.n} sắp xếp ({a.clutter}, tập {a.split}) -> {a.out}")


if __name__ == "__main__":
    main()
