// Reads the result files that the P6 TEST chain and the P7 benchmark-DEV chain write when they finish, and turns them into the cells and
// sentences of the two reports.  Nothing here is typed by hand: every number comes from
//   P6: runs/p6_test_decision.json (written by scripts/p6_decide.py, committed with PREREGISTRATION_PAPER.md) and the newest
//       logs/*_p6_decision.txt (same run, for the descriptive lines that the JSON does not carry), logs/*_p6_test_chain.log (finish time);
//   P7: runs/p7_bench_compare.json (scripts/p7_bench_compare.py) and logs/*_p7_bench_chain.log (finish time).
// While a file does not exist the getters return the {{…}} placeholder, so the reports build at any time.
// Verdict wording follows PREREGISTRATION_PAPER.md section 4.  Where a new number could contradict a sentence written from DEV data, the
// builders print a yellow "{{cần xem lại: …}}" flag instead of silently rewriting the text.
// Test with other inputs:  REPORT_P6_JSON, REPORT_P6_TXT, REPORT_P6_CHAIN, REPORT_P7_JSON, REPORT_P7_CHAIN, REPORT_FIG_DIR, REPORT_OUT.
const fs = require("fs"), path = require("path");
const ARENA = path.join(__dirname, "..");
const E = process.env;
const LOGS = path.join(ARENA, "logs");

function newestLog(suffix, mustContain) {
    let names = [];
    try { names = fs.readdirSync(LOGS).filter(f => f.endsWith(suffix)).sort().reverse(); } catch (e) { return null; }
    for (const f of names) {
        const p = path.join(LOGS, f);
        if (!mustContain || fs.readFileSync(p, "utf8").includes(mustContain)) return p;
    }
    return null;
}
const readJSON = p => (p && fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : null);
const rel = p => path.relative(ARENA, p);

// ------------------------------------------------------------------ formatting (Vietnamese: decimal comma)
const vn = (x, d = 1) => x.toFixed(d).replace(".", ",");
const SUP = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
function fp(p) {
    if (p >= 0.9995) return "1,0";
    if (p < 0.001) { const [m, e] = p.toExponential(1).split("e"); return `${m.replace(".", ",")}·10${String(parseInt(e)).split("").map(c => SUP[c]).join("")}`; }
    return Number(p.toPrecision(2)).toString().replace(".", ",");
}
const pts = x => (x > 0 ? "+" : x < 0 ? "−" : "±") + vn(Math.abs(x)) + " điểm";
function wilson(s, n, z = 1.959964) {
    if (!n) return [NaN, NaN];
    const p = s / n, den = 1 + z * z / n, c = (p + z * z / (2 * n)) / den, h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den;
    return [Math.max(0, c - h), Math.min(1, c + h)];
}
const pct = (s, n) => `${Math.round(100 * s / n)}%`;
const ci = (s, n) => { const [lo, hi] = wilson(s, n); return `${Math.round(100 * lo)}–${Math.round(100 * hi)}%`; };
const PH = (t = "…") => `{{${t}}}`;
function ddmm(stamp) {   // "2026-11-19 14:22:10" -> "14:22 ngày 19/11/2026"
    const m = /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/.exec(stamp || "");
    return m ? `${m[4]}:${m[5]} ngày ${m[3]}/${m[2]}/${m[1]}` : "";
}
function today() { const d = new Date(); return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`; }

// ------------------------------------------------------------------ P6 (pre-registered TEST)
const P6_JSON = E.REPORT_P6_JSON || path.join(ARENA, "runs", "p6_test_decision.json");
const P6_TXT = E.REPORT_P6_TXT || newestLog("_p6_decision.txt", "DECISION (PREREGISTRATION_PAPER.md");
const P6_CHAIN = E.REPORT_P6_CHAIN || newestLog("_p6_test_chain.log", "P6 TEST chain done");
const p6 = readJSON(P6_JSON);

function parseDecisionTxt(file) {
    const out = { sr: {}, sr025: {}, pooled: {}, pairs: {}, slow: null };
    if (!file || !fs.existsSync(file)) return null;
    let sec = "decision";
    for (const line of fs.readFileSync(file, "utf8").split("\n")) {
        if (line.startsWith(" test_C2 L0.5, success rate")) sec = "l05";
        else if (line.startsWith(" test_C2 L0.25")) sec = "l025";
        let m = /^\s{2}(\w+)\s+(\d+)\/(\d+)\s+=\s+[\d.]+%\s+\[[^\]]*\]\s+valid=0: (\d+)\s+fails: (\{.*\})\s*$/.exec(line);
        if (m && (sec === "l05" || sec === "l025")) {
            const fails = {}; for (const f of m[5].matchAll(/'([^']+)': (\d+)/g)) fails[f[1]] = +f[2];
            (sec === "l05" ? out.sr : out.sr025)[m[1]] = { s: +m[2], n: +m[3], invalid: +m[4], fails };
            continue;
        }
        m = /^\s{2}(ACT_old|ACT_W|DP_W) pooled\s+(\d+)\/(\d+)/.exec(line);
        if (m) { out.pooled[m[1]] = { s: +m[2], n: +m[3] }; continue; }
        m = /^\s{2}(.+?)\s+mean d =\s*([+-]?[\d.]+) pts\s+\(scenes A better (\d+), B better (\d+), tie (\d+)\)\s+sign-flip p = ([\d.eE+-]+)/.exec(line);
        if (m) { out.pairs[m[1].trim()] = { d: +m[2], a: +m[3], b: +m[4], tie: +m[5], p: +m[6] }; continue; }
        m = /ACT_W_slow s1000 vs ACT_W s1000 \(same seed\): (\d+) vs (\d+), gained (\d+), lost (\d+), two-sided McNemar p = ([\d.eE+-]+)/.exec(line);
        if (m) out.slow = { kx: +m[1], ky: +m[2], gained: +m[3], lost: +m[4], p: +m[5] };
    }
    return out;
}
const p6txt = p6 ? parseDecisionTxt(P6_TXT) : null;
const p6done = (() => {
    if (!P6_CHAIN || !fs.existsSync(P6_CHAIN)) return "";
    const m = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) P6 TEST chain done/m.exec(fs.readFileSync(P6_CHAIN, "utf8"));
    return m ? m[1] : "";
})();

const ACT_OLD = ["act_old_s1000", "act_old_s2000"], ACT_W = ["act_w_s1000", "act_w_s2000", "act_w_s3000"], DP_W = ["dp_w_s1000", "dp_w_s2000", "dp_w_s3000"];
function p6sum(names) { const s = names.reduce((a, k) => a + p6.success[k], 0); return { s, n: p6.n * names.length }; }
function verdict(k) {
    const h = p6[k];
    if (k === "H2") {
        if (h.supported) return "được ủng hộ (ACT_W tốt hơn)";
        return h.holm[2] ? "khác biệt, nhưng ACT_old tốt hơn (H2 không được ủng hộ)" : "không được ủng hộ (không thấy khác biệt)";
    }
    if (h.supported) return "được ủng hộ";
    const need = k === "H1" ? 15 : 5;
    return h.holm[2] ? `không được ủng hộ (p đạt nhưng chênh < +${need} điểm)` : "không được ủng hộ";
}
const short = k => (p6[k].supported ? "ủng hộ" : "không ủng hộ");

const P6 = {
    ok: !!p6,
    doneText: ddmm(p6done),
    src: p6 ? `\`${rel(P6_JSON)}\`${P6_TXT ? `, \`${rel(P6_TXT)}\`` : ""}` : "`logs/*_p6_decision.txt`, `runs/p6_test_decision.json` (tạo khi chuỗi xong)",
    // Table "Kết quả TEST mới": rows [label, L0.5 successes, Wilson, L0.25 successes, note]
    tableRows() {
        if (!p6) return null;
        const one = (k, note, l025) => [k.label, `${p6.success[k.id]}/${p6.n} (${pct(p6.success[k.id], p6.n)})`, ci(p6.success[k.id], p6.n),
            l025 ? `${p6.success_l025[k.id]}/${p6.n} (${pct(p6.success_l025[k.id], p6.n)})` : "—", note];
        const many = (label, ids, note) => { const t = p6sum(ids); return [label, ids.map(i => p6.success[i]).join(" / ") + ` (của ${p6.n})`, `gộp ${t.s}/${t.n} = ${pct(t.s, t.n)}; ${ci(t.s, t.n)}`, "—", note]; };
        return [
            one({ id: "cl0", label: "CL0" }, "", true), one({ id: "cl0_w", label: "CL0_W" }, "H1", true),
            one({ id: "oracle", label: "ORACLE" }, "", true), one({ id: "oracle_w", label: "ORACLE_W" }, "H1b", true),
            many("ACT_old s1000 / s2000", ACT_OLD, "H2 (đối chứng)"), many("ACT_W s1000 / s2000 / s3000", ACT_W, "H2"),
            one({ id: "act_w_slow_s1000", label: "ACT_W_slow s1000" }, "ablation", false), many("DP_W s1000 / s2000 / s3000", DP_W, "mô tả"),
        ];
    },
    decisionRows() {
        if (!p6) return null;
        const h1 = (k, lab) => { const h = p6[k]; return [lab, `${pts(h.gap)} (${h.kx} so với ${h.ky}/${h.n}; được ${h.gained}, mất ${h.lost})`, fp(h.p), fp(h.holm[1]), verdict(k)]; };
        const h = p6.H2;
        return [h1("H1", "H1: CL0_W > CL0 (cần ≥ +15 điểm)"), h1("H1b", "H1b: ORACLE_W > ORACLE (cần ≥ +5 điểm)"),
            ["H2: ACT_W ≠ ACT_old", `d trung bình ${pts(h.mean_d_pts)} (W hơn ở ${h.better_w} cảnh, old hơn ở ${h.better_old}, hòa ${h.ties})`, fp(h.p), fp(h.holm[1]), verdict("H2")]];
    },
    invalidTotal() { return p6 ? Object.values(p6.invalid_rows).reduce((a, b) => a + b, 0) : null; },
    pair(tag) { return p6txt && p6txt.pairs[tag] ? p6txt.pairs[tag] : null; },
    // CL0_W minus pooled ACT_W, sign-flip (descriptive); used to check DEV-based sentences ("ACT chưa vượt mô-đun đã sửa")
    modularAhead() { const q = this.pair("CL0_W - ACT_W"); return q ? q.d > 0 : null; },
    descBullets() {
        if (!p6) return [];
        const T = p6sum(ACT_W), O = p6sum(ACT_OLD), Dd = p6sum(DP_W), n = p6.n;
        const out = [`**Gộp hạt giống (mô tả):** ACT_W ${T.s}/${T.n} (${pct(T.s, T.n)}), ACT_old ${O.s}/${O.n} (${pct(O.s, O.n)}), DP_W ${Dd.s}/${Dd.n} (${pct(Dd.s, Dd.n)}); CL0_W ${p6.success.cl0_w}/${n} (${pct(p6.success.cl0_w, n)}), ORACLE_W ${p6.success.oracle_w}/${n} (${pct(p6.success.oracle_w, n)}).`];
        const lines = [["CL0_W - ACT_W", "CL0_W so với ACT_W"], ["CL0_W - DP_W", "CL0_W so với DP_W"], ["ACT_W - DP_W", "ACT_W so với DP_W"], ["ORACLE_W - ACT_W", "ORACLE_W so với ACT_W"], ["CL0 - ACT_old", "CL0 so với ACT_old"]]
            .map(([tag, lab]) => { const q = this.pair(tag); return q ? `${lab}: ${pts(q.d)} (bên trước hơn ở ${q.a} cảnh, bên sau hơn ở ${q.b}; đổi dấu p = ${fp(q.p)})` : null; }).filter(x => x);
        if (lines.length) out.push("**Ghép cặp theo cảnh, gộp hạt giống (mô tả, không hiệu chỉnh):** " + lines.join("; ") + ".");
        if (p6txt && p6txt.slow) { const s = p6txt.slow; out.push(`**ACT_W_slow s1000 so với ACT_W s1000** (cùng hạt giống, không có demo L0,5): ${s.kx} so với ${s.ky}/${n}, được ${s.gained}, mất ${s.lost}, McNemar hai phía p = ${fp(s.p)}.`); }
        const l = p6.l025_pairs;
        if (l) out.push(`**L0,25 (H3, chỉ mô-đun, mô tả):** CL0_W ${l.cl0_w_vs_cl0.kx} so với CL0 ${l.cl0_w_vs_cl0.ky}/${n} (p = ${fp(l.cl0_w_vs_cl0.p_two_sided)}); ORACLE_W ${l.oracle_w_vs_oracle.kx} so với ORACLE ${l.oracle_w_vs_oracle.ky}/${n} (p = ${fp(l.oracle_w_vs_oracle.p_two_sided)}).`);
        if (p6txt) {
            const top = ids => { const c = {}; ids.forEach(i => Object.entries((p6txt.sr[i] || {}).fails || {}).forEach(([k, v]) => (c[k] = (c[k] || 0) + v)));
                return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `\`${k}\` ${v}`).join(", ") || "không có"; };
            out.push(`**Nguyên nhân hỏng nhiều nhất** (\`fail_cause_auto\`, L0,5): CL0 ${top(["cl0"])}; CL0_W ${top(["cl0_w"])}; ACT_W (3 hạt giống) ${top(ACT_W)}; DP_W (3 hạt giống) ${top(DP_W)}.`);
        }
        return out;
    },
    // one sentence for the abstract / conclusions
    sentence() {
        if (!p6) return null;
        const a = p6.H1, b = p6.H1b, c = p6.H2, T = p6sum(ACT_W), Dd = p6sum(DP_W), n = p6.n;
        return `H1 (CL0_W > CL0) ${verdict("H1")}: ${a.kx}/${n} so với ${a.ky}/${n}, p Holm = ${fp(a.holm[1])}; H1b (ORACLE_W > ORACLE) ${verdict("H1b")}: ${b.kx}/${n} so với ${b.ky}/${n}, p Holm = ${fp(b.holm[1])}; ` +
            `H2 (ACT_W khác ACT_old) ${verdict("H2")}: d = ${pts(c.mean_d_pts)}, p Holm = ${fp(c.holm[1])}. Mô tả: ACT_W đạt ${pct(T.s, T.n)} và DP_W ${pct(Dd.s, Dd.n)} (gộp ba hạt giống), CL0_W đạt ${pct(p6.success.cl0_w, n)}`;
    },
    shortCell() {
        if (!p6) return null;
        const T = p6sum(ACT_W), O = p6sum(ACT_OLD), Dd = p6sum(DP_W), n = p6.n;
        return `H1: CL0_W ${p6.H1.kx} vs CL0 ${p6.H1.ky}, p Holm ${fp(p6.H1.holm[1])} → **${short("H1")}**; H1b: ORACLE_W ${p6.H1b.kx} vs ORACLE ${p6.H1b.ky}, p Holm ${fp(p6.H1b.holm[1])} → **${short("H1b")}**; ` +
            `H2: d = ${pts(p6.H2.mean_d_pts)}, p Holm ${fp(p6.H2.holm[1])} → **${short("H2")}**; gộp hạt giống: ACT_W ${T.s}/${T.n}, ACT_old ${O.s}/${O.n}, DP_W ${Dd.s}/${Dd.n}`;
    },
    // short phrases for sentences that interpret the result (all numbers from the JSON / decision log)
    seedsACTW() { return p6 ? `${ACT_W.map(k => p6.success[k]).slice(0, -1).join(", ")} và ${p6.success[ACT_W[2]]}/${p6.n}` : null; },
    h2Text() { return p6 ? `${pts(p6.H2.mean_d_pts)}, p Holm = ${fp(p6.H2.holm[1])}` : null; },
    modVsAct() { const q = this.pair("CL0_W - ACT_W"), T = p6 && p6sum(ACT_W); return p6 && q ? `CL0_W ${pct(p6.success.cl0_w, p6.n)} so với ACT_W ${pct(T.s, T.n)} gộp ba hạt giống, ${pts(q.d)} theo cảnh, p = ${fp(q.p)}` : null; },
    actVsDp() { const q = this.pair("ACT_W - DP_W"), T = p6 && p6sum(ACT_W), Dd = p6 && p6sum(DP_W); return p6 && q ? `ACT_W ${pct(T.s, T.n)}, DP_W ${pct(Dd.s, Dd.n)} gộp; ${pts(q.d)} theo cảnh, p = ${fp(q.p)}` : null; },
    slowText() { const q = this.pair("ACT_W_slow - ACT_W"); return q ? `ACT_W_slow so với ACT_W ${pts(q.d)}, p = ${fp(q.p)}` : null; },
    statusNote() {
        if (!p6) return null;
        const inv = this.invalidTotal();
        return `Chuỗi P6 xong lúc ${this.doneText || "[chưa kiểm giờ]"}: đủ 60 lượt hợp lệ cho mọi phương pháp ở cả hai tốc độ (p6_decide.py chỉ ghi quyết định khi không thiếu lượt nào), ${inv} dòng valid=0 ở L0,5. ` +
            `Số trong hai bảng trên đọc tự động từ \`${rel(P6_JSON)}\` do \`scripts/p6_decide.py\` (commit cùng tiền đăng ký) ghi; phần mô tả lấy từ \`${P6_TXT ? rel(P6_TXT) : "logs/*_p6_decision.txt"}\`.`;
    },
};

// ------------------------------------------------------------------ P7 (benchmark-DEV, same machine)
const P7_JSON = E.REPORT_P7_JSON || path.join(ARENA, "runs", "p7_bench_compare.json");
const P7_CHAIN = E.REPORT_P7_CHAIN || newestLog("_p7_bench_chain.log", "P7 benchmark-DEV chain done");
const p7raw = readJSON(P7_JSON);
const p7done = (() => {
    if (!P7_CHAIN || !fs.existsSync(P7_CHAIN)) return "";
    const m = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) P7 benchmark-DEV chain done/m.exec(fs.readFileSync(P7_CHAIN, "utf8"));
    return m ? m[1] : "";
})();
// the JSON is only trusted once the chain says it is done (the comparison script can also be run by hand on partial data)
const p7 = p7raw && (p7done || E.REPORT_P7_JSON) ? p7raw : null;
const S7 = p7 ? p7.summary : {};
const has = lab => S7[lab] && S7[lab].n > 0;
const N7 = 40;
function cnt(lab) { if (!has(lab)) return "—"; const s = S7[lab]; return s.n === N7 ? `${s.s}` : `${s.s} (chỉ ${s.n}/${N7} lượt)`; }
function pooled7(labs) { const L = labs.filter(has); const s = L.reduce((a, k) => a + S7[k].s, 0), n = L.reduce((a, k) => a + S7[k].n, 0); return { s, n }; }
function cells7(labs) {
    const keys = ["C0/L0", "C0/L0.25", "C2/L0", "C2/L0.25"];
    return keys.map(k => { let a = 0, b = 0; labs.filter(has).forEach(l => { const [x, y] = S7[l].cells[k].split("/").map(Number); a += x; b += y; }); return `${a}/${b}`; }).join(" · ");
}
function pv(lab, ref) { const q = p7 && (p7.pairs[`${lab} | ${ref}`]); return q ? fp(q.p) : "—"; }
const REF = "CL0_W (W1)";
const GROUPS7 = [
    ["CL0 / CL0_W", ["CL0", "CL0_W (W1)"], false], ["ORACLE / ORACLE_W", ["ORACLE", "ORACLE_W (W1)"], false],
    ["ACT_old s1000 / s2000", ["ACT_old s1000", "ACT_old s2000"], true], ["ACT_W s1000 / s2000 / s3000", ["ACT_W s1000", "ACT_W s2000", "ACT_W s3000"], true],
    ["ACT_W_slow s1000", ["ACT_W_slow s1000"], false], ["DP_W s1000 / s2000 / s3000", ["DP_W s1000", "DP_W s2000", "DP_W s3000"], true],
];
const PAPERS7 = ["P05 CNS frontend", "P07 ViT-VS", "P17 ODIL stage1", "P19 ACT"];
const ports7 = () => Object.keys(S7).filter(k => k.endsWith("(here)") && has(k));
const LEARNED = ["ACT_old s1000", "ACT_old s2000", "ACT_W s1000", "ACT_W s2000", "ACT_W s3000", "ACT_W_slow s1000", "DP_W s1000", "DP_W s2000", "DP_W s3000"];

const P7 = {
    ok: !!p7,
    doneText: ddmm(p7done),
    src: p7 ? `\`${rel(P7_JSON)}\`${P7_CHAIN ? `, \`${rel(P7_CHAIN)}\`` : ""}` : "`logs/*_p7_bench_compare.txt`, `runs/p7_bench_compare.json` (tạo khi chuỗi xong)",
    tableRows() {
        if (!p7) return null;
        const one = l => (has(l) ? `${pct(S7[l].s, S7[l].n)}; ${ci(S7[l].s, S7[l].n)}` : "—");
        const rows = GROUPS7.map(([lab, labs, pool]) => {   // pool = seeds of one method (summed); otherwise one line per method
            const t = pooled7(labs);
            return [lab, labs.map(cnt).join(" / "), pool ? (t.n ? `gộp ${pct(t.s, t.n)}; ${ci(t.s, t.n)}` : "—") : labs.map(one).join("\n"),
                pool ? cells7(labs) : labs.map(l => cells7([l])).join("\n"), labs.map(l => (l === REF ? "—" : pv(l, REF))).join(" / ")];
        });
        for (const k of ports7()) rows.push([`${k.replace(" (here)", "")} (port, chạy lại ở máy này)`, cnt(k), `${pct(S7[k].s, S7[k].n)}; ${ci(S7[k].s, S7[k].n)}`, cells7([k]), pv(k, REF)]);
        rows.push(["P05 / P07 / P17 / P19 (máy benchmark)", PAPERS7.map(cnt).join(" / "), "—", "—", PAPERS7.map(l => pv(l, REF)).join(" / ") + " (khác máy)"]);
        return rows;
    },
    best() {   // best learned policy (single checkpoint) on the 40 pairs
        const L = LEARNED.filter(l => has(l) && S7[l].n === N7).sort((a, b) => S7[b].s - S7[a].s);
        return L.length ? L[0] : null;
    },
    bestPaper() { const L = PAPERS7.filter(has).sort((a, b) => S7[b].s - S7[a].s); return L.length ? L[0] : null; },
    count(lab) { return has(lab) ? S7[lab].s : null; },
    incomplete() { return Object.keys(S7).filter(k => !k.startsWith("bench") && !k.includes("E14") && !PAPERS7.includes(k) && k !== "P18 FlowControl" && S7[k].n < N7); },
    repro() {
        if (!p7) return null;
        const q = p7.pairs["CL0 | bench CL0"] || p7.pairs["bench CL0 | CL0"];
        return q && has("CL0") && has("bench CL0") ? `CL0 chạy lại ở máy này đạt ${S7["CL0"].s}/${N7} so với ${S7["bench CL0"].s}/${N7} trên máy benchmark, cùng kết quả ở ${q.agree}/${q.n} lượt` : null;
    },
    bullets() {
        if (!p7) return [];
        const out = [], b = this.best(), bp = this.bestPaper(), w = this.count(REF);
        if (b && w !== null) {
            const q = p7.pairs[`${b} | ${REF}`];
            out.push(`**Chính sách học tốt nhất trên cùng máy:** ${b} ${S7[b].s}/${N7} (${pct(S7[b].s, N7)}), so với CL0_W ${w}/${N7} (${pct(w, N7)})` +
                (q ? `; chỉ ${b} đạt ở ${q.only_a} lượt, chỉ CL0_W đạt ở ${q.only_b} lượt, McNemar hai phía p = ${fp(q.p)} (Holm trong bảng: ${fp(q.holm)}).` : "."));
        }
        const fam = (lab, labs) => { const t = pooled7(labs); return t.n ? `${lab} ${pct(t.s, t.n)}` : null; };
        const f = [fam("ACT_old", ["ACT_old s1000", "ACT_old s2000"]), fam("ACT_W", ["ACT_W s1000", "ACT_W s2000", "ACT_W s3000"]), fam("DP_W", ["DP_W s1000", "DP_W s2000", "DP_W s3000"])].filter(x => x);
        if (f.length) out.push(`**Trung bình theo họ (gộp hạt giống):** ${f.join(", ")}; ORACLE_W ${has("ORACLE_W (W1)") ? pct(S7["ORACLE_W (W1)"].s, N7) : "—"}.`);
        if (b && bp) out.push(`**So với bài báo tái lập** (bài báo chạy trên máy benchmark, nên đây vẫn là so khác máy): tốt nhất trong các bài báo là ${bp} ${S7[bp].s}/${N7}; ${b} hơn ${S7[b].s - S7[bp].s >= 0 ? S7[b].s - S7[bp].s : "−" + (S7[bp].s - S7[b].s)} lượt.`);
        const r = this.repro(); if (r) out.push(`**Độ lặp lại giữa hai máy:** ${r}.`);
        const inc = this.incomplete(); if (inc.length) out.push(`{{Chưa đủ 40 lượt: ${inc.join(", ")} — xem log P7}}`);
        return out;
    },
    shortCell() {
        if (!p7) return null;
        const b = this.best(), f = (labs) => { const t = pooled7(labs); return t.n ? pct(t.s, t.n) : "—"; };
        return `CL0_W ${cnt(REF)}, CL0 ${cnt("CL0")}, ORACLE_W ${cnt("ORACLE_W (W1)")}; ACT_old ${f(["ACT_old s1000", "ACT_old s2000"])}, ACT_W ${f(["ACT_W s1000", "ACT_W s2000", "ACT_W s3000"])}, DP_W ${f(["DP_W s1000", "DP_W s2000", "DP_W s3000"])} (gộp hạt giống)` +
            (b ? `; tốt nhất ${b} ${S7[b].s}/${N7}, vs CL0_W p = ${pv(b, REF)}` : "");
    },
    sentence() {
        if (!p7) return null;
        const b = this.best(), w = this.count(REF);
        return b ? `chạy cùng máy (P7, ${this.doneText}), chính sách học tốt nhất là ${b} với ${S7[b].s}/${N7}, CL0_W đạt ${w}/${N7} (McNemar p = ${pv(b, REF)})` : "P7 xong nhưng chưa có chính sách học nào đủ 40 lượt";
    },
};

// ------------------------------------------------------------------ figures and cover
const FIG_DIR = E.REPORT_FIG_DIR || path.join(__dirname, "figures");
const figIf = f => { const p = path.join(FIG_DIR, f); return fs.existsSync(p) ? p : null; };
const INFO = readJSON(path.join(__dirname, "thong_tin.json")) || {};
const OUT_DIR = E.REPORT_OUT || __dirname;

module.exports = { P6, P7, PH, fp, pts, vn, pct, ci, today, figIf, FIG_DIR, INFO, OUT_DIR };
