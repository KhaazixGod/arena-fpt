// Short report (only what is needed): conclusions, method choice, method, key results with evidence, limitations.  Same sources as build_report.js.
// Run from arena/:  NODE_PATH=<dir with node_modules> node bao_cao_do_an/build_tomtat.js     {{...}} = filled after P6 (TEST) / P7 (benchmark-DEV).
const fs = require("fs"), path = require("path");
const L = require("./lib.js");
const { D, FONT, H1, H2, P, NOTE, BL, EQ, TABLE, FIG, out, push, runs } = L;
const { Document, Packer, Paragraph, TextRun, AlignmentType, Footer, PageNumber, LevelFormat } = D;
const ALL = require("./refs.js");
L.setRefs(["act", "dp", "lerobot", "so101", "isaac", "mcnemar", "wilson", "holm"].map(k => ALL.find(r => r.key === k)));
const fig = f => path.join(__dirname, "figures", f);
const F = require("./fill.js");   // P6 / P7 results, filled automatically once the chains have written them
const CAUGHT_UP = (F.P6.ok && F.P6.modularAhead() === false) || (F.P7.ok && !!F.P7.best() && F.P7.count("CL0_W (W1)") !== null && F.P7.count(F.P7.best()) >= F.P7.count("CL0_W (W1)"));
const FLAG_MOD = CAUGHT_UP ? " {{cần xem lại: ở TEST mới hoặc P7 có chính sách học không thua CL0_W}}" : "";

H1("BÁO CÁO TÓM TẮT: ACT CHO BÀI TOÁN GẮP VẬT LẠ TRÊN BĂNG CHUYỀN VỚI TAY SO-101", false, "#", { noBreak: true });
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: runs("Mô phỏng Isaac Sim, một camera RGB cố định — bản ngày " + F.today() + (F.P6.ok && F.P7.ok ? "; số TEST mới và so sánh cùng máy đọc tự động từ kết quả của các chuỗi" : F.P6.ok ? "; ô {{vàng}} điền khi so sánh cùng máy (~20/11) xong" : "; ô {{vàng}} điền khi TEST mới (19/11) và so sánh cùng máy (20/11) xong"), { size: 24, italics: true }) }));

H2("1. Kết luận");
BL([
    "**Chọn ACT** [@act] làm chính sách học: trong 30 bài báo mà nhóm thử tái lập trên cùng môi trường, ACT là phương pháp học duy nhất được port nguyên vẹn, có sẵn trong LeRobot [@lerobot] cho SO-101 [@so101] và huấn luyện được trong khoảng 2,3 giờ trên GPU 8 GB.",
    "**Giao diện I2 là điều chỉnh quyết định.** Cho ACT xuất mục tiêu đầu kẹp tương đối trong hệ quy chiếu băng: ở 75 mm/s đạt 13/20 so với 4/20 của ACT mặc định (p = 0,022), dù demo không có tốc độ này.",
    "**Hơn mọi bài báo tái lập**, trên cùng 40 lượt DEV của benchmark: ACT đạt 75%, các bài báo đạt 30–62,5%. Bản port ACT gốc đạt 50% (p = 0,041). ACT vẫn **thấp hơn pipeline mô-đun CL0** (87,5%), dù chênh lệch chưa có ý nghĩa (p = 0,125).",
    "**TEST có tiền đăng ký của đồ án (G2):** ACT 35% và 30% (hai hạt giống), CL0 37% → giả thuyết “ACT hơn mô-đun ≥ 15 điểm” bị bác bỏ.",
    "**Sau đóng băng:** bộ thực thi của baseline mô-đun có lỗi cổ tay ở băng nhanh. Sửa bằng W1 nâng CL0 từ 25/60 lên 52/60 trên DEV, nên kết quả G2 nhiều khả năng bị lẫn bởi lỗi này. " + (F.P6.ok ? `**TEST mới có tiền đăng ký** (xong ${F.P6.doneText}): ${F.P6.sentence()}.` : "TEST mới: {{kết quả, ~19/11}}.") + FLAG_MOD,
]);

H2("2. Bài toán");
P("Tay SO-101 (5 khớp + kẹp) cạnh băng rộng 200 mm; camera RGB cố định nhìn từ trên; biết quãng băng đã đi s(t) và góc khớp. Mỗi lượt có 1–5 vật **chưa có trong demo**; phương pháp có 20 s để nhấc một vật và giữ 2 s. Tốc độ băng: L0 (đứng yên), L0,25 (37,5 mm/s), L0,5 (75 mm/s), L1,0 (150 mm/s). **Ô chính:** 3–4 vật cách nhau 10–25 mm (C2), L0,5. Mọi số liệu là mô phỏng Isaac Sim 6.0.0.1 [@isaac], `engine=isaac`.");

H2("3. Chọn phương pháp từ 30 bài báo");
P("Benchmark của nhóm (`Benmark_Capstone`) thử chạy 30 bài báo (visual servoing, thao tác hai tay, học bắt chước) trên **cùng arena**: cùng vật, cùng cảnh, cùng 40 lượt DEV (dev_C0, dev_C2 × L0, L0,25), ghép cặp với CL0.");
TABLE("Kết quả tái lập 30 bài báo trên arena", ["Trạng thái", "Số bài", "Ghi chú"], [
    ["Bài tổng quan, không chạy", "3", "P01–P03"],
    ["Bị chặn vì phần cứng", "15", "Cần tay thứ hai, xúc giác/lực, camera cổ tay hoặc robot di động"],
    ["Bị chặn vì mã/checkpoint/dữ liệu", "7", "Chưa công bố, gắn với môi trường khác, hoặc chưa qua cổng kỹ thuật"],
    ["Chạy một phần", "1", "P18 FlowControl: 12/40 lượt, 0 thành công, ~22 phút/lượt"],
    ["Chạy trọn DEV", "4", "P05, P07, P17 (chỉ thành phần), **P19 ACT (port nguyên phương pháp)**"],
], [38, 10, 52], { center: [1], source: "`Benmark_Capstone/reports/deadline/latest/coverage_30.csv`." });
P("**Lý do chọn:** ACT là ứng viên duy nhất thỏa cả năm tiêu chí: (i) một tay, camera RGB cố định; (ii) có mã và hỗ trợ SO-101; (iii) huấn luyện trên 8 GB (1,8 GB VRAM, ~2,3 giờ); (iv) cơ chế chunk chịu được trễ; (v) có kết quả trên arena. **Diffusion Policy** [@dp] là baseline học thứ hai; **CL0** (pipeline mô-đun không huấn luyện, chung bộ thực thi) là baseline cổ điển; **ORACLE** (nhận thức bằng ground truth) đo trần của môi trường và sinh demo.");

H2("4. Phương pháp");
P("**ACT:** CVAE với ResNet-18 + Transformer (encoder 4 lớp, decoder 1 lớp, d_model 512), dự đoán chunk 100 hành động; mặc định LeRobot 0.6.1, 100.000 bước, batch 8. Demo: 444 tập thành công của ORACLE ở L0 và L0,25 (không có L0,5).");
P("**Giao diện I2 (đóng góp):** mạng nhận ảnh + trạng thái đầu kẹp [x_{b}, y_{b}, z, cos 2ψ, sin 2ψ, kẹp] tại lúc chụp t_{img}, và xuất mục tiêu đầu kẹp **tương đối trong hệ băng**. Bộ thực thi đổi về hệ thế giới bằng quãng băng đi thêm, rồi giải IK ở 50 Hz:");
EQ("a_{k} = p_{b, mục tiêu}(t_{img} + kΔ) − p_{b, EE}(t_{img}),   p_{b} = p_{w} − s(t) · û");
EQ("p_{w, lệnh}(t_{x}) = p_{w, EE}(t_{img}) + a_{k} + ( s(t_{x}) − s(t_{img}) ) · û");
P("Mô hình ACT không đổi; chỉ thay bộ tiền/hậu xử lý (`train_act_i2.py`) và bộ thực thi (`arena/methods/act_i2.py`). Chế độ suy luận chốt bằng quy tắc ghi trước: thực hiện trọn chunk 100 khung rồi mới lập kế hoạch lại (/100).");
FIG(fig("fig_act_i2_pipeline.png"), 15, "Sơ đồ ACT_I2");
BL([
    "**Các phương pháp so sánh:** CL0 (tách nền, điểm kẹp theo biến đổi khoảng cách, theo dõi trong hệ băng); ORACLE; DP_W (Diffusion Policy, cùng giao diện I2, UNet thu nhỏ để vừa 8 GB); CL0_W/ORACLE_W (thêm W1: chọn nhánh góc kẹp sao cho cổ tay không chạm giới hạn khớp khi bám băng).",
    "**Đánh giá:** ghép cặp trên cùng cảnh, McNemar chính xác [@mcnemar], khoảng Wilson 95% [@wilson], Holm khi kiểm nhiều giả thuyết [@holm]. Tinh chỉnh chỉ trên DEV; TEST khóa và chỉ chạy một lần theo tiền đăng ký đã commit.",
]);

H2("5. Kết quả chính");
TABLE("Kết quả chính (số lượt thành công; ghép cặp trên cùng cảnh)", ["Thí nghiệm", "Điều kiện", "Kết quả", "Nguồn"], [
    ["I2 so với ACT mặc định (E14)", "dev_C2, L0,5, n = 20", "ACT_I2 13, ACT_J0 4, CL0 6, ORACLE 16; I2 vs J0 p = 0,022", "`runs/e14_*`, `runs/e10_base_L05`"],
    ["Biến thể suy luận/dữ liệu (E15, E16)", "dev_C2, dev_C3 × L0,25, L0,5; n = 80", "/100: 48, thêm demo L0,5: 50, COMMIT: 41, /10: 39 (CL0 43, ORACLE 61) → giữ /100", "`logs/2026-11-08_175431_e16_pair_final.txt`"],
    ["**TEST G2** (đồ án, tiền đăng ký)", "test_C2, L0,5, n = 60, vật lạ", "ACT 21/60 và 18/60, CL0 22/60, ORACLE 28/60; p = 1,0 và 0,48 → **NO-GO**", "`logs/2026-11-10_210822_g2_decision.txt`"],
    ["40 nhiệm vụ (E18, tiền đăng ký)", "gắp/đặt/kéo/lật, băng đứng yên", "Đã học 122/160 (76,2%); 8 nhiệm vụ chưa thấy 58/80 (72,5%)", "`logs/2026-11-12_204650_e18_decision.txt`"],
    ["W1 (sau đóng băng)", "dev_C2, L0,5, n = 60", "CL0 25 → 52 (p = 5·10⁻⁷); ORACLE 45 → 58 (p = 2·10⁻⁴)", "`BAO_CAO_PAPER_DEV.md` mục 5"],
    ["Chính sách học mới (sau đóng băng)", "dev_C2, L0,5, n = 20", "ACT 13–15, DP 13–16, CL0 7, CL0_W 17, ORACLE_W 19", "`runs/p4_dev_*`, `runs/p2_*`, `runs/p5_*`"],
    ["So với bài báo (benchmark)", "40 lượt DEV chung, khác máy", "ACT 30/40; P17 25, P19 20, P05 18, P07 12; CL0 35, ORACLE 40", "`Benmark_Capstone/results/raw`, `runs/e14_*`"],
    ["**TEST mới** (tiền đăng ký)", "test_C2 mới, L0,5, n = 60", F.P6.shortCell() || "H1 CL0_W > CL0: {{…}}; H1b ORACLE_W > ORACLE: {{…}}; H2 ACT_W vs ACT_old: {{…}}; DP: {{…}}", F.P6.ok ? F.P6.src : "`logs/*_p6_decision.txt`"],
    ["So sánh cùng máy (P7)", "40 lượt DEV của benchmark", F.P7.shortCell() || "9 chính sách học + CL0/CL0_W/ORACLE/ORACLE_W: {{…}}", F.P7.ok ? F.P7.src : "`logs/*_p7_bench_compare.txt`"],
], [22, 20, 36, 22]);
if (F.P7.ok && F.figIf("fig_p7_bench.png")) FIG(F.figIf("fig_p7_bench.png"), 12, "Mọi phương pháp trên 40 lượt DEV chung của benchmark: phương pháp của đồ án chạy cùng máy (P7), bài báo tái lập lấy từ máy benchmark");
else FIG(fig("fig_benchmark_dev.png"), 14, "ACT của đồ án so với các bài báo tái lập trên 40 lượt DEV chung của benchmark");

H2("6. Phương pháp đề xuất và hạn chế");
P("**Phương pháp đề xuất cho nền tảng giá rẻ:** ACT với giao diện hệ băng I2, thực hiện trọn chunk 100 khung, học từ demo của một chuyên gia. Cấu hình này mạnh hơn mọi phương pháp đã công bố mà nhóm tái lập được trên cùng arena. Tuy vậy, ACT chưa vượt pipeline mô-đun khi bộ thực thi của pipeline đã được sửa." + FLAG_MOD + " Lợi thế của ACT là không cần nhận thức thủ công và học được nhiều kỹ năng trong một mô hình (E18).");
BL([
    "Chỉ mô phỏng (lockstep, không có trễ suy luận thật); chưa có số trên robot thật.",
    "Demo sinh bởi chuyên gia có đặc quyền; demo người ở 75 mm/s khó hơn nhiều.",
    "Lỗi chính của ACT: va chạm và đóng kẹp vào chỗ trống (lệch ngang khoảng −9 mm). Phương sai giữa các hạt giống (13–16/20) và giữa các lần chạy (3/20 lượt đổi kết quả) lớn.",
    F.P7.ok ? "So sánh với bài báo vẫn là khác máy: phương pháp của đồ án đã chạy lại cùng máy (P7), các bản port bài báo chỉ có số từ máy benchmark; chênh lệch khoảng ±5 lượt có thể chỉ do máy." : "So sánh với benchmark là khác máy: chênh lệch khoảng ±5 lượt có thể chỉ do máy. Chuỗi P7 chạy lại cùng máy.",
    "Ở 150 mm/s mọi phương pháp đều thất bại vì tầm với và thời gian.",
]);

H2("7. Việc tiếp theo");
BL([
    ...(F.P6.ok && F.P7.ok ? [] : [F.P6.ok ? "Điền bảng so sánh cùng máy (~20/11) vào báo cáo." : "Điền kết quả TEST mới (~19/11) và bảng so sánh cùng máy (~20/11) vào báo cáo."]),
    "Kiểm chứng ACT_I2 và CL0_W trên tay SO-101 thật.",
    "Áp W1 cho bộ thực thi của ACT/DP; giảm lệch ngang của ACT bằng dữ liệu hoặc huấn luyện.",
]);
NOTE("Báo cáo đầy đủ (40 trang, mọi bảng và đường dẫn bằng chứng): `arena/bao_cao_do_an/Bao_cao_do_an_ACT.docx`.");

H2("Tài liệu tham khảo");
L.getRefs().forEach((r, i) => push(new Paragraph({ spacing: { after: 60, line: 280, lineRule: "auto" }, indent: { left: 567, hanging: 567 },
    children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 22 }), new TextRun({ text: r.text, font: FONT, size: 22 })] })));

const doc = new Document({
    creator: "arena", title: "Báo cáo tóm tắt: ACT cho gắp vật trên băng chuyền",
    styles: {
        default: { document: { run: { font: FONT, size: 26 }, paragraph: { spacing: { line: 320, lineRule: "auto" } } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true },
              paragraph: { spacing: { before: 0, after: 120 }, keepNext: true, outlineLevel: 0, alignment: AlignmentType.CENTER } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true },
              paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
        ],
    },
    numbering: { config: [
        { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 567, hanging: 284 } } } }] },
        { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 567, hanging: 340 } } } }] },
    ] },
    sections: [{
        properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1701, right: 1134 } } },
        footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] }) },
        children: out,
    }],
});
L.save(doc, path.join(F.OUT_DIR, "Bao_cao_tom_tat_ACT.docx"));
