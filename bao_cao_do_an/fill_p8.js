// P8 (PREREGISTRATION_P8.md): the paper ports re-implemented in ports/ and P19, run on the P6 TEST sheet.  Read by build_report.js / build_tomtat.js.
// Source: runs/p8_test_decision.json (scripts/p8_decide.py, written at the end of scripts/p8_test.sh) + the newest logs/*_p8_decision.txt.
// P8.ok is false until both exist; the builders then keep their pre-P8 sentences.
const fs = require("fs");
const path = require("path");
const ARENA = path.dirname(__dirname);
const E = process.env;
const JS = E.REPORT_P8_JSON || path.join(ARENA, "runs", "p8_test_decision.json");
const newest = suf => { const d = path.join(ARENA, "logs"); const f = fs.readdirSync(d).filter(x => x.endsWith(suf)).sort(); return f.length ? path.join(d, f[f.length - 1]) : null; };
const TXT = E.REPORT_P8_TXT || newest("_p8_decision.txt");
let J = null;
try { J = JSON.parse(fs.readFileSync(JS, "utf8")); } catch (e) { J = null; }
const txt = TXT && fs.existsSync(TXT) ? fs.readFileSync(TXT, "utf8") : "";
const ok = !!(J && J.F1 && Object.keys(J.F1).length === 4 && /wrote runs\/p8_test_decision\.json/.test(txt));
const rel = p => path.relative(ARENA, p);

const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
function fp(p, floor = true) {     // floor: sign-flip p with 100 000 permutations cannot go below 1e-5; exact McNemar p can
    if (p >= 0.9995) return "1,0";
    if (floor && p <= 1.00001e-5) return "≤ 1·10⁻⁵";
    if (p < 0.001) { const [m, e] = p.toExponential(1).split("e"); return `${m.replace(".", ",")}·10${String(parseInt(e)).split("").map(c => SUP[c]).join("")}`; }
    return Number(p.toPrecision(2)).toString().replace(".", ",");
}
const peq = p => (p <= 1.00001e-5 ? "p ≤ 1·10⁻⁵" : `p = ${fp(p)}`);
const pct = (s, n) => `${Math.round(100 * s / n)}%`;
const vn = x => String(x).replace(".", ",");
const pts = d => `${d >= 0 ? "+" : "−"}${vn(Math.abs(d).toFixed(1))} điểm`;
const S = k => (J && J.success[k] !== undefined ? J.success[k] : null);
const sum = (sp, names) => { const v = names.map(n => S(`${sp}/${n}`)); return v.some(x => x === null) ? null : v.reduce((a, b) => a + b, 0); };
const cell = (sp, names) => { const s = sum(sp, names); const n = 60 * names.length; return s === null ? "—" : `${s}/${n} (${pct(s, n)})`; };
const seeds = (sp, names) => names.map(n => S(`${sp}/${n}`)).join(" / ");
const ACT_W = ["act_w_s1000", "act_w_s2000", "act_w_s3000"], P19 = ["p19_s1000", "p19_s2000", "p19_s3000"];
const pooledLine = key => {   // "l025 ACT_W (3) vs CL0_W  mean d = -17.8 pts (scenes A better 10, B better 29, tie 21)  sign-flip p = 0.01"
    const s = J && J.desc[key]; if (typeof s !== "string") return null;
    const m = /mean d =\s*([-+]?[\d.]+) pts.*A better (\d+), B better (\d+), tie (\d+).*p = ([\d.e-]+)/.exec(s);
    return m ? { d: parseFloat(m[1]), a: +m[2], b: +m[3], tie: +m[4], p: parseFloat(m[5]) } : null;
};
const F1V = { "ACT_W better": "ACT_W hơn", "paper better": "bài báo hơn", "no difference shown": "không thấy khác biệt" };
const F2V = { "CL0_W better": "CL0_W hơn", "port better": "bài báo hơn", "no difference shown": "không thấy khác biệt" };
const NAME = { "P05_CNS_W": "P05 CNS (+W1)", "P07_VITVS_W": "P07 ViT-VS (+W1)", "P17_ODIL_W": "P17 ODIL (+W1)", "P19 (3 seeds)": "P19 ACT gốc (3 hạt giống)" };
const SHORT = { "P05_CNS_W": "P05 CNS", "P07_VITVS_W": "P07 ViT-VS", "P17_ODIL_W": "P17 ODIL", "P19 (3 seeds)": "P19 (ACT gốc)" };

const P8 = {
    ok,
    src: ok ? `\`${rel(JS)}\`, \`${rel(TXT)}\`` : "`runs/p8_test_decision.json` (tạo khi chuỗi P8 xong)",
    rows() {
        if (!ok) return null;
        const port = (lab, p, extra) => [lab, `${S(`l05/${p}_w`)} / ${S(`l05/${p}`)}`, `${S(`l025/${p}_w`)} / ${S(`l025/${p}`)}`, extra];
        return [
            ["CL0_W (mô-đun + W1; lượt chạy của P6)", `${S("l05/cl0_w")}/60 (${pct(S("l05/cl0_w"), 60)})`, `${S("l025/cl0_w")}/60 (${pct(S("l025/cl0_w"), 60)})`, "mốc so sánh"],
            ["ACT_W, 3 hạt giống (đồ án)", `${cell("l05", ACT_W)}\n${seeds("l05", ACT_W)}`, `${cell("l025", ACT_W)}\n${seeds("l025", ACT_W)}`, "L0,5: lượt chạy của P6"],
            ["P19 ACT gốc (góc khớp + temporal ensembling), 3 hạt giống", `${cell("l05", P19)}\n${seeds("l05", P19)}`, `${cell("l025", P19)}\n${seeds("l025", P19)}`, "cùng demo E6 với ACT_old"],
            port("P05 CNS: có W1 / không", "p05_cns", "SIFT"),
            port("P07 ViT-VS: có W1 / không", "p07_vitvs", "DINOv2"),
            port("P17 ODIL: có W1 / không", "p17_odil", "FPFH + FGR + ICP, độ sâu lý tưởng"),
            ["Có thêm ảnh mẫu của vật TEST (nhãn riêng): P05 / P07 / P17, có W1", `${S("l05/p05_cns_w_t")} / ${S("l05/p07_vitvs_w_t")} / ${S("l05/p17_odil_w_t")}`, "—", "biết trước vật lạ"],
        ];
    },
    f1Rows() {
        if (!ok) return null;
        return Object.entries(J.F1).map(([k, r]) => [`ACT_W vs ${NAME[k] || k}`, `${pts(r.d_pts)} (ACT_W hơn ở ${r.a_better} cảnh, bài báo hơn ở ${r.b_better}, hòa ${r.tie})`,
            peq(r.p).replace("p = ", "").replace("p ", ""), fp(r.holm), F1V[r.verdict] || r.verdict]);
    },
    f2Rows() {
        if (!ok) return null;
        return Object.entries(J.F2).map(([k, q]) => [`CL0_W vs ${NAME[k] || k}`, `${q.kx}/60 vs ${q.ky}/60 (chỉ CL0_W đạt ${q.gained}, chỉ bài báo đạt ${q.lost})`, fp(q.p, false), fp(q.holm, false), F2V[q.verdict] || q.verdict]);
    },
    better() { return ok ? Object.entries(J.F1).filter(([k, r]) => r.rejected && r.d_pts > 0).map(([k]) => SHORT[k] || k) : []; },
    notBetter() { return ok ? Object.entries(J.F1).filter(([k, r]) => !(r.rejected && r.d_pts > 0)).map(([k]) => SHORT[k] || k) : []; },
    l025() { const q = pooledLine("l025 ACT_W vs CL0_W"); return ok && q ? `CL0_W ${pct(S("l025/cl0_w"), 60)} so với ACT_W ${pct(sum("l025", ACT_W), 180)} gộp ba hạt giống, d = ${pts(q.d)}, ${peq(q.p)} (mô tả)` : null; },
    l05() { const q = pooledLine("l05 ACT_W vs CL0_W"); return ok && q ? `CL0_W ${pct(S("l05/cl0_w"), 60)} so với ACT_W ${pct(sum("l05", ACT_W), 180)}, d = ${pts(q.d)}` : null; },
    w1(p, sp = "l05") { const q = J && J.desc[`${sp} W1 ${p}`]; return q ? `${q.ky} → ${q.kx}/60 (McNemar p = ${fp(q.p, false)})` : "—"; },
    testref(p) { const q = J && J.desc[`l05 testrefs ${p}`]; return q ? `${q.ky} → ${q.kx}/60 (McNemar p = ${fp(q.p, false)})` : "—"; },
    // one sentence for the abstract / conclusions
    sentence() {
        if (!ok) return null;
        const f = J.F1, g = J.F2;
        return `ACT_W hơn ${this.better().join(" và ")} (Holm ${Object.values(f).filter(r => r.rejected && r.d_pts > 0).map(r => fp(r.holm)).join(" và ")}), ` +
            `không thấy khác biệt với ${this.notBetter().join(" và ")} (hai bài này có W1); CL0_W hơn cả ba bài nhận thức khi dùng chung bộ thực thi đã sửa ` +
            `(${Object.values(g).map(q => `${q.kx} so với ${q.ky}/60`).join("; ")})`;
    },
};
module.exports = { P8 };
