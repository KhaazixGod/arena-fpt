// Helpers for build_report.js: Vietnamese thesis layout (A4, Times New Roman 13 pt, 1.5 lines), numbered tables/figures per chapter,
// inline markup  **bold**  `code`  {{placeholder}} (yellow, filled after the TEST / benchmark runs)  and citations [@key] / [@a,@b].
const fs = require("fs");
const D = require("docx");
const { Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType, ImageRun, BorderStyle, LevelFormat } = D;

const FONT = "Times New Roman";
const BODY = 26;           // 13 pt
const SMALL = 22;          // 11 pt (tables)
const CONTENT_W = 9071;    // A4 11906 - left 3 cm (1701) - right 2 cm (1134)

let REFS = [], refIdx = {};
function setRefs(list) { REFS = list; refIdx = {}; list.forEach((r, i) => (refIdx[r.key] = i + 1)); }
function cites(t) {
    return t.replace(/\[@([^\]]+)\]/g, (m, g) => "[" + g.split(",").map(k => {
        k = k.trim().replace(/^@/, "");
        if (!refIdx[k]) throw new Error("unknown reference " + k);
        return refIdx[k];
    }).join(", ") + "]");
}
function runs(text, base = {}) {
    text = cites(text);
    const size = base.size || BODY;
    return text.split(/(\*\*[^*]+\*\*|`[^`]+`|\{\{[^}]+\}\}|_\{[^}]+\})/).filter(p => p).map(p => {
        if (p.startsWith("_{")) return new TextRun({ ...base, font: FONT, size, text: p.slice(2, -1), subScript: true });
        if (p.startsWith("**")) return new TextRun({ ...base, font: FONT, size, text: p.slice(2, -2), bold: true });
        if (p.startsWith("`")) return new TextRun({ ...base, font: "Courier New", size: size - 4, text: p.slice(1, -1) });
        if (p.startsWith("{{")) return new TextRun({ ...base, font: FONT, size, text: p.slice(2, -2), bold: true, highlight: "yellow" });
        return new TextRun({ ...base, font: FONT, size, text: p });
    });
}

let chap = 0, chapLabel = "", tabN = 0, figN = 0, eqN = 0, listInst = 0;
const out = [];
const push = (...x) => out.push(...x);

function H1(text, numbered = true, label = "", opts = {}) {
    if (numbered) { chap += 1; chapLabel = String(chap); } else { chapLabel = label; }
    if (!opts.keepCounters) { tabN = 0; figN = 0; eqN = 0; }
    push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: opts.noBreak ? false : true, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: numbered ? `CHƯƠNG ${chap}. ${text}` : text, font: FONT, size: 30, bold: true })] }));
}
function H2(text) { push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: FONT, size: 28, bold: true })] })); }
function H3(text) { push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: FONT, size: BODY, bold: true, italics: true })] })); }
function P(text, opt = {}) {
    push(new Paragraph({ children: runs(text, opt.run || {}), alignment: opt.align || AlignmentType.JUSTIFIED,
        indent: opt.noIndent ? undefined : { firstLine: 567 }, spacing: { after: 100, line: 360, lineRule: "auto" } }));
}
function NOTE(text) {   // boxed-looking remark: indented, smaller
    push(new Paragraph({ children: runs(text, { size: 24, italics: true }), alignment: AlignmentType.JUSTIFIED, indent: { left: 567, right: 284 },
        spacing: { before: 60, after: 120, line: 320, lineRule: "auto" }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: "8A8984", space: 8 } } }));
}
function BL(items, numbered = false) {
    listInst += 1;
    for (const it of items) {
        push(new Paragraph({ children: runs(it), alignment: AlignmentType.JUSTIFIED, spacing: { after: 60, line: 340, lineRule: "auto" },
            numbering: { reference: numbered ? "num" : "bul", level: 0, instance: listInst } }));
    }
}
function EQ(text) {
    eqN += 1;
    push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 80 }, tabStops: [{ type: "right", position: CONTENT_W }],
        children: [...runs(text, { italics: true }), new TextRun({ text: chapLabel === "#" ? `\t(${eqN})` : `\t(${chapLabel}.${eqN})`, font: FONT, size: BODY })] }));
}
function caption(kind, text) {
    const n = kind === "Bảng" ? ++tabN : ++figN;
    return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: kind === "Bảng", spacing: { before: kind === "Bảng" ? 160 : 60, after: kind === "Bảng" ? 60 : 200, line: 300, lineRule: "auto" },
        children: [new TextRun({ text: chapLabel === "#" ? `${kind} ${n}. ` : chapLabel ? `${kind} ${chapLabel}.${n}. ` : `${kind}: `, font: FONT, size: 24, bold: true }), ...runs(text, { size: 24, italics: true })] });
}
function cellPara(text, bold, align) {
    return new Paragraph({ alignment: align || AlignmentType.LEFT, spacing: { before: 20, after: 20, line: 260, lineRule: "auto" }, children: runs(text, { size: SMALL, bold }) });
}
function TABLE(cap, header, rows, pct, opt = {}) {
    const widths = pct.map(p => Math.floor(CONTENT_W * p / 100));
    widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
    const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
    const borders = { top: border, bottom: border, left: border, right: border };
    const mk = (cells, isHead) => new TableRow({ tableHeader: isHead, cantSplit: true, children: cells.map((t, i) => new TableCell({
        width: { size: widths[i], type: WidthType.DXA }, borders,
        shading: isHead ? { type: ShadingType.CLEAR, fill: "E7E6E2", color: "auto" } : undefined,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: String(t).split("\n").map(line => cellPara(line, isHead, (opt.center || []).includes(i) ? AlignmentType.CENTER : AlignmentType.LEFT)) })) });
    push(caption("Bảng", cap));
    push(new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows: [mk(header, true), ...rows.map(r => mk(r, false))] }));
    if (opt.source) push(new Paragraph({ spacing: { before: 40, after: 160, line: 260, lineRule: "auto" }, children: runs("Nguồn: " + opt.source, { size: 20, italics: true }) }));
    else push(new Paragraph({ spacing: { after: 80 }, children: [] }));
}
function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function FIG(file, widthCm, cap) {
    const [w, h] = pngSize(file);
    const pxW = Math.round(widthCm / 2.54 * 96), pxH = Math.round(pxW * h / w);
    push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 0, line: 240, lineRule: "auto" },
        children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: pxW, height: pxH },
            altText: { title: cap.replace(/\*\*|`/g, ""), description: cap.replace(/\*\*|`/g, ""), name: file.split("/").pop() } })] }));
    push(caption("Hình", cap));
}
function refNo(key) { if (!refIdx[key]) throw new Error("ref " + key); return refIdx[key]; }

// Write the .docx.  If the file on disk is not the one this builder wrote last time (someone edited it in Word/LibreOffice), keep it and write
// <name>_moi.docx next to it instead, so hand edits are never overwritten.  Hashes of the last build: .build_sha256.json in the same folder.
function save(doc, target) {
    const path = require("path"), crypto = require("crypto");
    const sha = b => crypto.createHash("sha256").update(b).digest("hex");
    const rec = path.join(path.dirname(target), ".build_sha256.json"), key = path.basename(target);
    let R = {}; try { R = JSON.parse(fs.readFileSync(rec, "utf8")); } catch (e) { R = {}; }
    let dest = target;
    if (fs.existsSync(target) && R[key] && sha(fs.readFileSync(target)) !== R[key]) {
        dest = target.replace(/\.docx$/, "_moi.docx");
        console.log(`WARNING ${key} changed after the last build (edited by hand?): left as it is, new build written to ${path.basename(dest)}`);
    }
    return D.Packer.toBuffer(doc).then(buf => {
        fs.writeFileSync(dest, buf);
        if (dest === target) { R[key] = sha(buf); fs.writeFileSync(rec, JSON.stringify(R, null, 1)); }
        console.log("wrote", dest, buf.length, "bytes");
    });
}

module.exports = { D, FONT, BODY, SMALL, CONTENT_W, setRefs, runs, H1, H2, H3, P, NOTE, BL, EQ, TABLE, FIG, out, push, refNo, save, getRefs: () => REFS };
