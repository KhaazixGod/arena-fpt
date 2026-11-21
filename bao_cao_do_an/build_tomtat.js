// Short report (only what is needed): conclusions, method choice, method, key results with evidence, limitations.  Same sources as build_report.js.
// Run from arena/:  NODE_PATH=<dir with node_modules> node bao_cao_do_an/build_tomtat.js     {{...}} = filled after P6 (TEST) / P7 (benchmark-DEV).
const fs = require("fs"), path = require("path");
const L = require("./lib.js");
const { D, FONT, H1, H2, H3, P, NOTE, BL, EQ, TABLE, FIG, out, push, runs } = L;
const { Document, Packer, Paragraph, TextRun, AlignmentType, Footer, PageNumber, LevelFormat } = D;
const ALL = require("./refs.js");
L.setRefs(["act", "dp", "lerobot", "so101", "isaac", "mcnemar", "wilson", "holm"].map(k => ALL.find(r => r.key === k)));
const fig = f => path.join(__dirname, "figures", f);
const F = require("./fill.js");   // P6 / P7 results, filled automatically once the chains have written them
const CAUGHT_UP = (F.P6.ok && F.P6.modularAhead() === false) || (F.P7.ok && F.P7.learnedBeatsMod());
const FLAG_MOD = CAUGHT_UP ? " {{cần xem lại: TEST mới không cho thấy mô-đun dẫn trước, hoặc P7 có chính sách học vượt CL0_W}}" : "";

H1("BÁO CÁO TÓM TẮT: ACT CHO BÀI TOÁN GẮP VẬT LẠ TRÊN BĂNG CHUYỀN VỚI TAY SO-101", false, "#", { noBreak: true });
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: runs("Mô phỏng Isaac Sim, một camera RGB cố định — bản ngày " + F.today() + (F.P6.ok && F.P7.ok ? "; số TEST mới và so sánh cùng máy đọc tự động từ kết quả của các chuỗi" : F.P6.ok ? "; ô {{vàng}} điền khi so sánh cùng máy (~20/11) xong" : "; ô {{vàng}} điền khi TEST mới (19/11) và so sánh cùng máy (20/11) xong"), { size: 24, italics: true }) }));

H2("1. Kết luận");
BL([
    "**Chọn ACT** [@act] làm chính sách học: trong 30 bài báo mà nhóm thử tái lập trên cùng môi trường, ACT là phương pháp học duy nhất được port nguyên vẹn, có sẵn trong LeRobot [@lerobot] cho SO-101 [@so101] và huấn luyện được trong khoảng 2,3 giờ trên GPU 8 GB.",
    "**Giao diện I2 là điều chỉnh quyết định.** Cho ACT xuất mục tiêu đầu kẹp tương đối trong hệ quy chiếu băng: ở 75 mm/s đạt 13/20 so với 4/20 của ACT mặc định (p = 0,022), dù demo không có tốc độ này.",
    F.P7.ok && F.P7.slowVsMod()
        ? `**Hơn mọi bài báo tái lập** trên cùng 40 lượt DEV của benchmark: các bài báo đạt 30–62,5%, bản port ACT gốc 50%. Chạy cùng máy (P7, băng đứng yên và 37,5 mm/s): ${F.P7.slowVsMod()}.`
        : "**Hơn mọi bài báo tái lập**, trên cùng 40 lượt DEV của benchmark: ACT đạt 75%, các bài báo đạt 30–62,5%. Bản port ACT gốc đạt 50% (p = 0,041). ACT vẫn **thấp hơn pipeline mô-đun CL0** (87,5%), dù chênh lệch chưa có ý nghĩa (p = 0,125).",
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
P("Mọi con số bên dưới là **số lượt thành công / số lượt thử**; ví dụ 13/20 nghĩa là thành công 13 trong 20 lượt. Mục 5.1 so với các bài báo, mục 5.2 là kết quả đánh giá nội bộ của đồ án. Các ký hiệu được giải thích ở Bảng 2.");
TABLE("Chú giải ký hiệu dùng trong mục 5", ["Ký hiệu", "Nghĩa"], [
    ["**DEV / TEST**", "DEV: tập cảnh dùng để thử và tinh chỉnh. TEST: tập cảnh khóa, chỉ chạy một lần theo tiền đăng ký, dùng để kết luận."],
    ["**C0, C1, C2, C3**", "Độ lộn xộn của cảnh. C0: 1 vật. C1: 2 vật cách xa. C2: 3–4 vật cách nhau 10–25 mm. C3: 4–5 vật gần như chạm nhau (0–3 mm). Ví dụ “DEV, C2” là cảnh DEV mức C2."],
    ["**L0 … L1,0**", "Tốc độ băng. L0: đứng yên. L0,25: 37,5 mm/s. L0,5: 75 mm/s. L1,0: 150 mm/s."],
    ["**ACT_J0**", "ACT mặc định của LeRobot: xuất góc khớp, không biết băng đang chạy."],
    ["**ACT_I2**", "ACT với giao diện hệ băng I2 (mục 4). Có ba cách chạy: **/100** (lập kế hoạch lại sau mỗi 100 khung, tức trọn một chunk), **/10** (lập lại sau mỗi 10 khung) và **COMMIT** (lập lại mỗi 10 khung khi kẹp còn mở, rồi chạy hết chunk khi có lệnh đóng kẹp)."],
    ["**ACT_old, ACT_W, DP_W**", "ACT_I2 hoặc Diffusion Policy học từ demo của ORACLE chưa sửa lỗi (old) hoặc đã sửa lỗi cổ tay W1 (W). Hậu tố s1000, s2000, s3000 là **hạt giống**: mỗi lần huấn luyện lại với số ngẫu nhiên khác. “Gộp” là cộng lượt của các hạt giống."],
    ["**CL0, CL0_W**", "Pipeline mô-đun không huấn luyện (mục 4). CL0_W là CL0 có thêm sửa lỗi W1."],
    ["**ORACLE, ORACLE_W**", "Phương pháp dùng thông tin thật của mô phỏng (ground truth); cho biết trần của môi trường và sinh demo. ORACLE_W có thêm W1."],
    ["**W1**", "Sửa bộ thực thi: chọn hướng kẹp sao cho cổ tay không chạm giới hạn khớp khi bám theo băng chạy nhanh."],
    ["**p, p Holm**", "Xác suất thấy chênh lệch lớn như vậy nếu hai phương pháp thật ra ngang nhau (kiểm định ghép cặp). p < 0,05 nghĩa là chênh lệch có ý nghĩa thống kê. p Holm là p đã hiệu chỉnh khi kiểm nhiều giả thuyết cùng lúc."],
    ["**H1, H1b, H2**", "Các giả thuyết ghi trước khi chạy TEST mới. H1: CL0_W hơn CL0 ít nhất 15 điểm phần trăm. H1b: ORACLE_W hơn ORACLE ít nhất 5 điểm. H2: ACT_W khác ACT_old."],
    ["**NO-GO**", "Giả thuyết đặt trước bị bác bỏ."],
], [24, 76], { source: "định nghĩa theo `arena/README.md`, `PREREGISTRATION_PAPER.md` và mục 4 báo cáo này." });


const ph = t => `{{${t}}}`;
H3("5.1. So với các bài báo", { pageBreak: true });
P("**Lưu ý khi đọc:** con số các bài báo tự công bố (cột 2) được đo trên bài toán khác (robot thật hai tay, mô phỏng khác, nhiệm vụ khác), và benchmark của nhóm đánh dấu mọi cặp đó là “không so trực tiếp được”. Vì vậy so sánh công bằng là **cột 3**: bài báo được chạy lại trên **cùng arena và cùng 40 lượt DEV** với phương pháp của đồ án. Các bài báo (P05, P07, P17, P19) chạy trên máy benchmark còn phương pháp của đồ án chạy trên máy này, nên chênh khoảng ±5 lượt có thể chỉ do máy. P05, P07, P17 chỉ chạy một thành phần của bài báo, không phải cả phương pháp.");
const P7p = F.P7.plain();
const fr = (s, n) => `${s}/${n} (${Number((100 * s / n).toFixed(1)).toString().replace(".", ",")}%)`;
const one = l => (P7p && P7p.has(l) ? fr(P7p.S[l].s, P7p.S[l].n) : ph("…"));
const many = labs => { if (!P7p) return ph("…"); const t = P7p.pooled(labs); return t.n ? fr(t.s, t.n) : ph("…"); };
TABLE("So sánh với các bài báo trên cùng 40 lượt DEV", ["Phương pháp", "Bài báo tự công bố (bài toán gốc, không so trực tiếp)", "Chạy trên arena, 40 lượt DEV", "Ghi chú"], [
    ["**Bài báo tái lập (máy benchmark)**", "", "", ""],
    ["P19 – ACT (port nguyên phương pháp)", "Mô phỏng hai tay: 86% (chuyển khối), 32% (lắp khớp); robot thật: 20–96% tùy nhiệm vụ", one("P19 ACT"), "Port cả phương pháp"],
    ["P17 – ODIL (chỉ giai đoạn 1)", "Robot thật hai tay: 77,2% trung bình", one("P17 ODIL stage1"), "Một thành phần"],
    ["P05 – CNS (chỉ phần nhận thức)", "Robot thật: 100% (cảnh dễ, có RANSAC); mô phỏng: 100%", one("P05 CNS frontend"), "Một thành phần"],
    ["P07 – ViT-VS", "Mô phỏng: 100% (không nhiễu), 76,6% (có nhiễu)", one("P07 ViT-VS"), "Một thành phần"],
    ["P18 – FlowControl", "Robot thật: 19/20 (Pick-Stow)", "0/12 (chạy dở, ~22 phút mỗi lượt)", "Một thành phần, chưa đủ 40 lượt"],
    ["**Đồ án (máy này)**", "", "", ""],
    ["ACT_old (2 hạt giống)", "—", many(["ACT_old s1000", "ACT_old s2000"]), "ACT_I2, demo từ ORACLE chưa sửa"],
    ["ACT_W (3 hạt giống)", "—", many(["ACT_W s1000", "ACT_W s2000", "ACT_W s3000"]), "ACT_I2, demo từ ORACLE đã sửa W1"],
    ["DP_W (3 hạt giống)", "—", many(["DP_W s1000", "DP_W s2000", "DP_W s3000"]), "Diffusion Policy, giao diện I2"],
    ["CL0_W", "—", one("CL0_W (W1)"), "Mô-đun, đã sửa W1"],
    ["CL0", "—", one("CL0"), "Mô-đun, chưa sửa W1"],
    ["ORACLE", "—", one("ORACLE"), "Trần của môi trường"],
], [24, 31, 19, 26], { source: "cột 2: `arena_mectrics/new1/paper_reported_metrics.csv`; cột 3: `Benmark_Capstone/reports/deadline/latest/coverage_30.csv` (bài báo) và " + (F.P7.ok ? F.P7.src : "`runs/p7_bench_compare.json`") + " (đồ án)." });
P(F.P7.ok && F.P7.slowVsMod() && !F.P7.learnedBeatsMod()
    ? "**Kết luận:** trên cùng 40 lượt, ACT của đồ án đạt khoảng 78–81%, cao hơn mọi bài báo tái lập (30–62,5%), kể cả bản port ACT gốc (50%). Tuy vậy ACT chưa vượt pipeline mô-đun CL0_W (80%): hai bên ngang nhau ở băng đứng yên và 37,5 mm/s."
    : "**Kết luận:** " + ph("điền sau khi so sánh cùng máy (P7) xong, hoặc cần xem lại vì có chính sách học vượt CL0_W") + ".");
if (F.P7.ok && (F.figIf("fig_p7_bench_gon.png") || F.figIf("fig_p7_bench.png"))) FIG(F.figIf("fig_p7_bench_gon.png") || F.figIf("fig_p7_bench.png"), F.figIf("fig_p7_bench_gon.png") ? 11 : 12, "Mọi phương pháp trên 40 lượt DEV chung của benchmark: phương pháp của đồ án chạy cùng máy (P7" + (F.figIf("fig_p7_bench_gon.png") ? "; các hạt giống của một phương pháp được cộng gộp" : "") + "), bài báo tái lập lấy từ máy benchmark");
else FIG(fig("fig_benchmark_dev.png"), 14, "ACT của đồ án so với các bài báo tái lập trên 40 lượt DEV chung của benchmark");

H3("5.2. Kết quả đánh giá nội bộ của đồ án");
const P6p = F.P6.plain();
const dpt = x => F.pts(x).replace(" điểm", " điểm phần trăm");
const h6 = (k, lab) => {       // one pre-registered hypothesis -> table row
    if (!P6p) return [lab, "test_C2 mới, L0,5, 60 lượt", ph("kết quả TEST mới"), ph("kết luận")];
    const h = P6p.d[k], v = P6p.verdict[k];
    return [lab, `test_C2 mới, L0,5, ${P6p.n} lượt`, k === "H2" ? "" : `${dpt(h.gap)}: ${h.kx}/${P6p.n} so với ${h.ky}/${P6p.n}`, `**${v}** (p Holm = ${F.fp(h.holm[1])})`];
};
const rowH1 = h6("H1", "**6. TEST mới – H1**\nCL0_W so với CL0");
const rowH1b = h6("H1b", "**7. TEST mới – H1b**\nORACLE_W so với ORACLE");
const rowH2 = h6("H2", "**8. TEST mới – H2**\nACT_W so với ACT_old");
if (P6p) rowH2[2] = `ACT_W hơn ACT_old trung bình ${dpt(P6p.d.H2.mean_d_pts)} (hơn ở ${P6p.d.H2.better_w} cảnh, kém ở ${P6p.d.H2.better_old}, hòa ${P6p.d.H2.ties})`;
const rowAll = P6p
    ? ["**9. TEST mới – gộp hạt giống**\n(mô tả)", `test_C2 mới, L0,5, ${P6p.n} lượt mỗi hạt giống`,
        `ACT_W: ${P6p.actW.s}/${P6p.actW.n} (${F.pct(P6p.actW.s, P6p.actW.n)})\nACT_old: ${P6p.actOld.s}/${P6p.actOld.n} (${F.pct(P6p.actOld.s, P6p.actOld.n)})\nDP_W: ${P6p.dpW.s}/${P6p.dpW.n} (${F.pct(P6p.dpW.s, P6p.dpW.n)})\nCL0_W: ${P6p.d.success.cl0_w}/${P6p.n} (${F.pct(P6p.d.success.cl0_w, P6p.n)})`, "Chỉ mô tả, chưa kiểm định"]
    : ["**9. TEST mới – gộp hạt giống**", "test_C2 mới, L0,5", ph("ACT_W, ACT_old, DP_W, CL0_W"), ""];
TABLE("Kết quả nội bộ của đồ án (thành công / số lượt thử; hai phương pháp so trên cùng các cảnh)", ["Thí nghiệm", "Điều kiện", "Kết quả", "Kết luận"], [
    ["**1. Giao diện I2** so với ACT mặc định", "DEV, C2, L0,5, 20 lượt", "ACT_I2: 13/20\nACT_J0: 4/20\nCL0: 6/20\nORACLE: 16/20", "I2 hơn ACT mặc định (p = 0,022)"],
    ["**2. Cách chạy ACT_I2** và thêm demo", "DEV, C2 và C3, L0,25 và L0,5, 80 lượt mỗi cách", "/100: 48/80\nThêm demo L0,5: 50/80\nCOMMIT: 41/80\n/10: 39/80\nCL0: 43/80, ORACLE: 61/80", "Giữ /100; không biến thể nào hơn"],
    ["**3. TEST G2** (bản đóng băng)", "TEST, C2, L0,5, 60 lượt, vật lạ", "ACT_I2: 21/60 và 18/60 (hai hạt giống)\nCL0: 22/60\nORACLE: 28/60", "**NO-GO**: ACT không hơn CL0 (p = 1,0 và 0,48)"],
    ["**4. 40 nhiệm vụ** (gắp, đặt, kéo, lật)", "Băng đứng yên; một mô hình ACT cho mọi nhiệm vụ", "Nhiệm vụ đã học: 122/160 (76,2%)\n8 nhiệm vụ chưa thấy: 58/80 (72,5%)", "Giả thuyết đặt trước được ủng hộ (một hạt giống)"],
    ["**5. Sửa lỗi W1** (sau đóng băng)", "DEV, C2, L0,5, 60 lượt", "CL0: 25 → 52/60 (p = 5·10⁻⁷)\nORACLE: 45 → 58/60 (p = 2·10⁻⁴)\n(trước → sau khi sửa)", "W1 tăng mạnh thành công của cả hai"],
    rowH1, rowH1b, rowH2, rowAll,
], [24, 22, 33, 21]);
P("**Nguồn dữ liệu theo số dòng.** (1) `runs/e14_*`, `runs/e10_base_L05`. (2) `logs/2026-11-08_175431_e16_pair_final.txt`. (3) `logs/2026-11-10_210822_g2_decision.txt`. (4) `logs/2026-11-12_204650_e18_decision.txt`. (5) `BAO_CAO_PAPER_DEV.md` mục 5. (6–9) " + (F.P6.ok ? F.P6.src : "`logs/*_p6_decision.txt`") + ".", { noIndent: true, align: AlignmentType.LEFT, run: { size: 20 } });
H2("6. Phương pháp đề xuất và hạn chế");
P("**Phương pháp đề xuất cho nền tảng giá rẻ:** ACT với giao diện hệ băng I2, thực hiện trọn chunk 100 khung, học từ demo của một chuyên gia" + (F.P6.ok ? ` đã được sửa lỗi bộ thực thi (TEST mới: ACT_W hơn ACT_old ${F.P6.h2Text()})` : "") + ". Cấu hình này mạnh hơn mọi bài báo mà nhóm tái lập được. Tuy vậy, ACT chưa vượt pipeline mô-đun khi bộ thực thi của pipeline đã được sửa" + (F.P7.ok && F.P7.slowVsMod() ? ": hai bên ngang nhau khi băng đứng yên hoặc chậm (P7), còn ở 75 mm/s mô-đun hơn rõ" : "") + (F.P6.ok ? ` (TEST mới: ${F.P6.modVsAct()})` : "") + "." + FLAG_MOD + " Lợi thế của ACT là không cần nhận thức thủ công và học được nhiều kỹ năng trong một mô hình (E18).");
BL([
    "Chỉ mô phỏng (lockstep, không có trễ suy luận), demo từ chuyên gia có đặc quyền; chưa có số trên robot thật.",
    "Lỗi chính của ACT: va chạm và đóng kẹp vào chỗ trống (lệch ngang khoảng −9 mm); phương sai giữa các hạt giống lớn" + (F.P6.ok ? ` (TEST mới: ACT_W ${F.P6.seedsACTW()})` : " (13–16/20)") + ".",
    F.P7.ok ? "Bài báo chỉ có số từ máy benchmark (khác máy; chênh khoảng ±5 lượt có thể chỉ do máy)." : "So sánh với benchmark là khác máy: chênh lệch khoảng ±5 lượt có thể chỉ do máy. Chuỗi P7 chạy lại cùng máy.",
    "Ở 150 mm/s mọi phương pháp đều thất bại vì tầm với và thời gian.",
]);

H2("7. Việc tiếp theo");
BL([
    ...(F.P6.ok && F.P7.ok ? [] : [F.P6.ok ? "Điền bảng so sánh cùng máy (~20/11) vào báo cáo." : "Điền kết quả TEST mới (~19/11) và bảng so sánh cùng máy (~20/11) vào báo cáo."]),
    "Kiểm chứng ACT_I2 và CL0_W trên tay SO-101 thật.",
    "Áp W1 cho bộ thực thi của ACT/DP; giảm lệch ngang của ACT.",
]);
NOTE("Báo cáo đầy đủ: `bao_cao_do_an/Bao_cao_do_an_ACT.docx`.");

H2("Tài liệu tham khảo");
L.getRefs().forEach((r, i) => push(new Paragraph({ spacing: { after: 30, line: 250, lineRule: "auto" }, indent: { left: 567, hanging: 567 },
    children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 20 }), new TextRun({ text: r.text, font: FONT, size: 20 })] })));

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
