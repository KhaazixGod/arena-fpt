// Bachelor-thesis report on ACT (Vietnamese).  Run from arena/:  NODE_PATH=<dir with node_modules> node bao_cao_do_an/build_report.js
// Every number below comes from a log or trials.csv named in the text or in Appendix A.  {{...}} marks values that do not exist yet
// (P6 TEST, P7 benchmark-DEV) and are filled when those runs finish.
const fs = require("fs"), path = require("path");
const L = require("./lib.js");
const { D, FONT, H1, H2, H3, P, NOTE, BL, EQ, TABLE, FIG, out, push, runs } = L;
const { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, Footer, PageNumber, TableOfContents, LevelFormat } = D;
L.setRefs(require("./refs.js"));
const F = require("./fill.js");   // P6 / P7 results, filled automatically once the chains have written them
const { P8 } = require("./fill_p8.js");   // P8: the papers rebuilt here and run on the TEST sheet (runs/p8_test_decision.json)
// sentences written from DEV data that a new result could contradict get a yellow flag instead of being rewritten automatically
const LEARNED_CAUGHT_UP = (F.P6.ok && F.P6.modularAhead() === false) || (F.P7.ok && F.P7.learnedBeatsMod());
const FLAG_MOD = LEARNED_CAUGHT_UP ? " {{cần xem lại: TEST mới không cho thấy mô-đun dẫn trước, hoặc P7 có chính sách học vượt CL0_W}}" : "";
const FIGS = path.join(__dirname, "figures");
const fig = f => path.join(FIGS, f);

// ======================================================================= cover
const center = (text, size, bold = false, after = 120, italics = false) => push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after },
    children: runs(text, { size, bold, italics }) }));
center(F.INFO.truong || "{{TÊN TRƯỜNG ĐẠI HỌC}}", 28, true, 60);
center("NGÀNH TRÍ TUỆ NHÂN TẠO", 26, true, 1400);
center("BÁO CÁO ĐỒ ÁN TỐT NGHIỆP", 32, true, 600);
center("SỬ DỤNG ACT (ACTION CHUNKING WITH TRANSFORMERS)", 34, true, 60);
center("CHO BÀI TOÁN GẮP VẬT LẠ TRÊN BĂNG CHUYỀN", 34, true, 60);
center("VỚI TAY ROBOT GIÁ RẺ SO-101:", 34, true, 60);
center("SO SÁNH VỚI CÁC PHƯƠNG PHÁP ĐÃ CÔNG BỐ", 34, true, 1200);
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: runs("Sinh viên thực hiện: " + (F.INFO.sinh_vien || "{{Họ và tên — MSSV}}")) }));
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: runs("Giảng viên hướng dẫn: " + (F.INFO.gvhd || "{{Họ và tên}}")) }));
push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1600 }, children: runs(F.P6.ok && F.P7.ok ? `Bản ngày ${F.today()}` : `Bản nháp ngày ${F.today()} — ${F.P6.ok ? "bảng so sánh benchmark cùng máy" : "số liệu TEST mới và bảng so sánh benchmark"} sẽ được điền khi chuỗi chạy xong`) }));
center(`${F.INFO.thanh_pho || "{{Thành phố}}"}, tháng 11 năm 2026`, 26, false, 0, true);

// ======================================================================= front matter
H1("TÓM TẮT", false);
P("Đồ án nghiên cứu việc dùng **ACT (Action Chunking with Transformers)** [@act], một chính sách học bắt chước từ ảnh, cho bài toán gắp vật **chưa từng thấy** từ **băng chuyền đang chạy** bằng tay robot giá rẻ **SO-101** [@so101] với **một camera RGB cố định**. Toàn bộ thí nghiệm chạy trong một môi trường mô phỏng Isaac Sim [@isaac] dựng theo bàn thí nghiệm thật (gọi là **arena**), với 36 vật sinh theo thủ tục, bốn mức lộn xộn và nhiều tốc độ băng.");
P("Để chọn phương pháp, đồ án dựa trên một benchmark của nhóm đã thử tái lập **30 bài báo** gần đây (visual servoing, thao tác hai tay, học bắt chước) trên cùng arena. Chỉ 4 bài chạy được trọn lưới đánh giá DEV; 15/22 bài bị chặn vì cần phần cứng ngoài nền tảng (tay thứ hai, cảm biến xúc giác, camera cổ tay). Trong số các phương pháp chạy được, ACT là phương pháp duy nhất được port nguyên vẹn, có sẵn trong LeRobot [@lerobot] cho SO-101 và huấn luyện được trong khoảng 2,5 giờ trên GPU 8 GB, nên được chọn làm chính sách học trọng tâm; Diffusion Policy [@dp] là baseline học thứ hai, và một pipeline mô-đun không cần huấn luyện (CL0) là baseline cổ điển.");
P("Đóng góp kỹ thuật chính về phía ACT là **giao diện hành động I2**: chính sách xuất mục tiêu đầu kẹp **tương đối, trong hệ quy chiếu đi theo băng**, còn bộ thực thi bù quãng băng đi trong lúc thực hiện. Ở 75 mm/s, I2 đạt 13/20 so với 4/20 của ACT mặc định trên cùng cảnh DEV (McNemar p = 0,022), dù demo chỉ được ghi ở băng đứng yên và băng chậm. Trên 40 lượt DEV chung của benchmark, ACT_I2 đạt **30/40 (75%)**, cao hơn cả bốn bài báo tái lập (30–62,5%, trong đó bản port ACT gốc đạt 50%) nhưng thấp hơn CL0 (87,5%).");
P("Ở kiểm định có tiền đăng ký của đồ án (G2, 60 cảnh TEST, 75 mm/s), ACT_I2 đạt 35% và 30% (hai hạt giống), không khác CL0 (37%); giả thuyết “ACT hơn mô-đun ≥ 15 điểm” bị bác bỏ. Một mở rộng 40 nhiệm vụ (E18) cho thấy ACT đa nhiệm vụ tổng quát hóa sang 8 nhiệm vụ chưa thấy (72,5%). Sau khi đóng băng đồ án, phân tích lỗi phát hiện bộ thực thi của baseline mô-đun chọn sai nhánh góc kẹp khi cổ tay chạm giới hạn khớp ở băng nhanh; bản sửa W1 nâng CL0 từ 25/60 lên 52/60 trên DEV. Một TEST mới có tiền đăng ký (ACT, ACT với demo đã sửa, Diffusion Policy, CL0, CL0 + W1) " + (F.P6.ok ? `đã chạy xong (${F.P6.doneText}): ${F.P6.sentence()}.` : "đang chạy; kết quả: {{điền sau khi TEST xong, dự kiến 19/11/2026}}.") + (F.P7.ok ? ` Trên 40 lượt DEV của benchmark, ${F.P7.sentence()}.` : "") + (P8.ok ? ` Vì số của các bài báo chỉ có trên DEV và từ máy khác, đồ án dựng lại P05 CNS, P07 ViT-VS, P17 ODIL và P19 ACT trên cùng máy rồi chạy trên đúng TEST 60 cảnh (P8, có tiền đăng ký): ${P8.sentence()}.` : ""));
P("**Từ khóa:** học bắt chước, ACT, Diffusion Policy, gắp vật trên băng chuyền, SO-101, Isaac Sim, tiền đăng ký, McNemar.", { noIndent: true });

H1("DANH MỤC TỪ VIẾT TẮT", false);
TABLE("Các từ viết tắt và thuật ngữ dùng trong báo cáo", ["Viết tắt", "Ý nghĩa"], [
    ["ACT", "Action Chunking with Transformers: chính sách học bắt chước dự đoán một chuỗi (chunk) hành động [@act]"],
    ["ACT_J0", "ACT mặc định của LeRobot: hành động là góc khớp tuyệt đối"],
    ["ACT_I2 / ACT_old", "ACT với giao diện I2 (mục tiêu đầu kẹp tương đối trong hệ băng), học từ demo E6 của ORACLE; là chính sách của G2"],
    ["ACT_W, ACT_W_slow", "ACT_I2 học từ demo của ORACLE_W (chuyên gia đã sửa W1); bản _slow chỉ dùng demo ở L0 và L0,25"],
    ["DP, DP_W", "Diffusion Policy [@dp]; DP_W học cùng dữ liệu với ACT_W"],
    ["CL0", "Pipeline mô-đun không huấn luyện: tách nền, chọn điểm kẹp, theo dõi trong hệ băng, bộ thực thi BeltExecutor"],
    ["ORACLE", "Chuyên gia có đặc quyền: nhận thức bằng ground truth + bộ thực thi của CL0; là trần của môi trường và nguồn demo"],
    ["W1, CL0_W, ORACLE_W", "Bộ chọn nhánh góc kẹp theo cổ tay; CL0_W/ORACLE_W là CL0/ORACLE có W1"],
    ["L0, L0,25, L0,5, L1,0", "Tỉ số dẫn trước L = v·τ/w; tương ứng băng đứng yên, 37,5, 75 và 150 mm/s"],
    ["C0–C3", "Mức lộn xộn: 1 vật; 2 vật xa nhau; 3–4 vật cách 10–25 mm; 4–5 vật chạm nhau"],
    ["DEV, TEST", "Tập phát triển (được tinh chỉnh, chọn) và tập kiểm tra khóa (chỉ chạy một lần theo tiền đăng ký)"],
    ["EE, TCP", "Đầu cuối tay (end effector), tâm kẹp (tool center point)"],
    ["IK, FK", "Động học ngược, động học thuận"],
    ["CVAE", "Conditional Variational Autoencoder [@cvae]"],
    ["DDPM", "Denoising Diffusion Probabilistic Model [@ddpm]"],
    ["VLA", "Vision-Language-Action model"],
    ["GT", "Ground truth: trạng thái thật do mô phỏng cung cấp"],
    ["SR, Wilson 95%", "Tỉ lệ thành công; khoảng tin cậy Wilson 95% [@wilson]"],
], [26, 74]);

push(new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "MỤC LỤC", font: FONT, size: 30, bold: true })] }));
push(new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-3" }));
push(new Paragraph({ spacing: { before: 200 }, children: runs("(Mở bằng Microsoft Word, nhấn chuột phải vào mục lục → Update Field để cập nhật số trang.)", { size: 22, italics: true }) }));

// ======================================================================= Chapter 1
H1("MỞ ĐẦU");
H2("1.1. Bối cảnh và động lực");
P("Gắp vật từ băng chuyền là một trong những tác vụ phổ biến nhất của robot trong sản xuất và logistics. Trong công nghiệp, bài toán này thường được giải bằng bộ mã hóa gắn trên băng và một hệ tọa độ đi theo băng (conveyor tracking) [@abb], kết hợp với nhận thức thị giác được thiết kế riêng cho từng loại sản phẩm. Cách làm này chính xác, nhưng tốn công thiết kế lại mỗi khi xuất hiện loại vật mới, và thường đi kèm phần cứng đắt tiền.");
P("Trong vài năm gần đây, học bắt chước từ ảnh đã cho thấy tay robot giá rẻ có thể học thao tác tinh từ vài chục đến vài trăm lần trình diễn (demo). Tiêu biểu là ACT [@act], được giới thiệu cùng hệ phần cứng giá rẻ ALOHA, và Diffusion Policy [@dp]. Thư viện LeRobot [@lerobot] đã đưa các chính sách này lên tay SO-101 [@so101], nên câu hỏi “một chính sách học từ ảnh có thay được chuỗi mô-đun thủ công trên băng chuyền hay không” đã trở thành câu hỏi thực tế với một phòng thí nghiệm nhỏ.");
P("Tuy vậy, phần lớn kết quả công bố cho chính sách học được đo trên vật đứng yên, robot hai tay hoặc camera gắn cổ tay. Các công trình gần nhất với băng chuyền chỉ so với chính sách học khác hoặc không so với phương pháp nào [@chen,@foretime,@dynamicvla]. Chúng tôi chưa tìm thấy công trình nào so một chính sách học từ ảnh với một baseline mô-đun được tinh chỉnh công bằng, trên băng chuyền, với vật lạ trong cảnh lộn xộn. Đồ án này đặt câu hỏi đó ở quy mô một đồ án cử nhân, trong mô phỏng, với quy trình đánh giá chặt (ghép cặp, tiền đăng ký, tập kiểm tra khóa).");

H2("1.2. Phát biểu bài toán");
P("Một tay SO-101 (5 khớp quay và một kẹp) đặt cạnh một băng chuyền rộng 200 mm. Một camera RGB cố định nhìn từ trên xuống (eye-to-hand); hệ thống biết quãng đường băng đã đi s(t) qua bộ đếm xung, và biết góc các khớp. Mỗi lượt thử đặt 1–5 vật lên băng theo một **tờ sắp xếp** cố định; băng chạy với tốc độ v. Phương pháp có 20 giây (thời gian mô phỏng) để nhấc **một** vật bất kỳ khỏi băng. Lượt được tính **thành công** khi đáy vật cao ít nhất 25 mm so với mặt băng và vật nằm giữa hai má kẹp (cách TCP theo phương ngang không quá 30 mm) liên tục trong 2 giây.");
P("Tốc độ băng được chuẩn hóa bằng **tỉ số dẫn trước** L = v·τ/w, với τ là tổng trễ vòng điều khiển (giả định 0,4 s) và w là độ mở kẹp hữu dụng (60 mm). L nhỏ nghĩa là sai số do băng trôi nằm trong dung sai của kẹp; L ≥ 0,5 thì cách phương pháp xử lý chuyển động của băng bắt đầu quyết định kết quả. Các tốc độ dùng trong đồ án là L0 (băng đứng yên), L0,25 (37,5 mm/s), L0,5 (75 mm/s) và L1,0 (150 mm/s). **Ô chính** của đồ án là vật lạ, mức lộn xộn C2 (3–4 vật cách nhau 10–25 mm), L0,5.");

H2("1.3. Mục tiêu và câu hỏi nghiên cứu");
P("Mục tiêu của đồ án là chọn, cài đặt và đánh giá công bằng một chính sách học từ ảnh cho bài toán trên, và rút ra phương pháp phù hợp cho nền tảng giá rẻ. Bốn câu hỏi nghiên cứu:");
BL([
    "**CH1 (chọn phương pháp).** Trong các phương pháp gần đây về visual servoing, thao tác hai tay và học bắt chước, phương pháp nào chạy được trên nền tảng một tay, camera RGB cố định, GPU 8 GB? Nên chọn phương pháp học nào làm trọng tâm?",
    "**CH2 (biểu diễn hành động).** Biểu diễn hành động và cách suy luận nào giúp ACT gắp được vật trên băng chạy, kể cả ở tốc độ không có trong demo?",
    "**CH3 (so với mô-đun).** ACT có hơn một pipeline mô-đun không cần huấn luyện, được tinh chỉnh công bằng, ở ô chính hay không?",
    "**CH4 (dữ liệu và chính sách học khác).** Sửa lỗi của chuyên gia sinh demo có làm ACT tốt lên không? ACT so với Diffusion Policy và với các bài báo tái lập trên cùng arena ra sao?",
], true);

H2("1.4. Đóng góp");
BL([
    "**Quy trình chọn phương pháp dựa trên bằng chứng:** phân loại 30 bài báo theo khả năng chạy trên nền tảng (dựa trên benchmark của nhóm) và so sánh trên cùng 40 lượt DEV ghép cặp (Chương 2, mục 4.9).",
    "**Giao diện I2 cho ACT:** hành động là mục tiêu đầu kẹp tương đối trong hệ quy chiếu băng; cài vào LeRobot bằng cách đổi bộ tiền/hậu xử lý, không đổi mô hình. I2 cho phép dùng demo ghi ở băng đứng yên và băng chậm để gắp ở băng nhanh (mục 3.4, 4.2).",
    "**Chuỗi thí nghiệm có kiểm soát:** các biến thể suy luận và dữ liệu của ACT với quy tắc chọn ghi trước (E15, E16), kiểm định có tiền đăng ký G2, mở rộng 40 nhiệm vụ E18 và TEST mới sau đóng băng (mục 4.3–4.8).",
    "**Phân tích lỗi của bộ thực thi:** lỗi chọn nhánh góc kẹp khi cổ tay chạm giới hạn khớp làm hỏng baseline mô-đun ở băng nhanh; bản sửa W1 cho thấy so sánh ACT với CL0 ở G2 bị lẫn bởi lỗi này (mục 4.6).",
    "**Hạ tầng tái lập được:** arena, bộ chạy có tiếp tục (resume), bộ gán nhãn tự động, kịch bản thống kê, và băm SHA-256 của mã, tờ sắp xếp và checkpoint (Phụ lục A).",
]);

H2("1.5. Phạm vi và giới hạn");
BL([
    "**Chỉ mô phỏng.** Mọi số liệu là của Isaac Sim (ghi `engine=isaac`), không mang sang robot thật; kiểm chứng trên tay thật là việc tiếp theo.",
    "**Phần cứng tính toán:** một máy với GPU RTX 3070 Ti 8 GB cho cả mô phỏng và huấn luyện; không chạy mô phỏng song song với huấn luyện.",
    "**Mô phỏng chạy lockstep:** thời gian suy luận của mạng không làm robot chậm lại trong thời gian ảo, nên độ trễ suy luận thật chưa được mô hình hóa.",
    "**Mốc đóng băng.** Phần đồ án đóng băng ở tag `thesis-freeze-2026-11-14`. Phần làm sau mốc này (nhánh `paper-dev`: W1, ACT_W, DP_W, TEST mới) được đánh dấu rõ là **sau đóng băng** trong báo cáo.",
]);

H2("1.6. Cấu trúc báo cáo");
P("Chương 2 tổng quan các hướng tiếp cận và trình bày việc so sánh 30 bài báo để chọn phương pháp. Chương 3 mô tả arena, chuyên gia sinh demo, ACT, giao diện I2, các baseline và giao thức đánh giá. Chương 4 trình bày kết quả theo trình tự phát triển: từ ACT mặc định đến ACT_I2, kiểm định G2, mở rộng đa nhiệm vụ, phân tích lỗi cổ tay, các chính sách học mới, TEST mới và so sánh với các bài báo. Chương 5 kết luận và nêu hướng phát triển.");

// ======================================================================= Chapter 2
H1("TỔNG QUAN VÀ SO SÁNH CÁC PHƯƠNG PHÁP");
H2("2.1. Gắp vật trên băng chuyền");
P("**Hướng công nghiệp.** Hệ conveyor tracking dùng encoder hai pha trên băng và một hệ tọa độ đi theo vật; theo tài liệu của hãng, TCP bám trong ±2 mm ở tốc độ tới 350 mm/s khi hiệu chuẩn tốt [@abb]. Như vậy, bản thân ý tưởng “làm việc trong hệ quy chiếu của băng” là kỹ thuật cổ điển; đồ án dùng lại ý tưởng này làm giao diện cho chính sách học (mục 3.4).");
P("**Hướng mô-đun.** Chuỗi “phát hiện → ước lượng điểm kẹp → theo dõi → dự đoán → điều khiển” vẫn là cách làm phổ biến. Phần nhận thức có thể là thủ công (tách nền, biến đổi khoảng cách) hoặc học sẵn, ví dụ GG-CNN tổng hợp điểm kẹp theo từng pixel từ ảnh độ sâu [@ggcnn]. Điểm yếu thường được nêu là vật lạ, vật lõm hoặc mỏng, và nhiều vật dính nhau.");
P("**Hướng học.** Chen và cộng sự (2025) gắp vật lạ di động trong clutter dày trên băng bằng so khớp tương đồng với camera gắn tay, ở 5,5 và 11,0 cm/s, nhưng không so với phương pháp nào khác [@chen]. ForeTime-VLA (2026) dùng một VLA lớn trên băng chuyền thật và chỉ so với chính sách học khác [@foretime]; DynamicVLA xử lý vật lăn/ném trên bàn [@dynamicvla]; Yamamoto và cộng sự kéo giãn thời gian demo chậm để gắp ở tốc độ chưa dạy, với một vật [@yamamoto]. Các số này được đọc ở mức tóm tắt bài báo, chưa đối chiếu toàn văn.");
NOTE("Nhận xét: chưa có công trình nào trong danh sách trên so chính sách học từ ảnh với một baseline mô-đun mạnh dùng cùng bộ thực thi, trên băng chuyền, với vật lạ và clutter. Đây là chỗ trống mà đồ án nhắm tới.");

H2("2.2. Học bắt chước cho thao tác robot");
P("**Behavior cloning và action chunking.** Học bắt chước có giám sát học ánh xạ từ quan sát sang hành động trên dữ liệu demo. Nhược điểm cổ điển là sai số tích lũy khi chính sách đi lệch khỏi phân bố demo. ACT [@act] giảm vấn đề này bằng cách dự đoán **một chuỗi k hành động** (chunk) mỗi lần thay vì một hành động, giúp giảm số bước ra quyết định hiệu dụng đi k lần; mô hình là một CVAE [@cvae] với bộ mã hóa ảnh ResNet [@resnet] và Transformer [@transformer]. Bài gốc báo cáo 86% (demo theo kịch bản) và 50% (demo người) trên tác vụ chuyển khối trong mô phỏng, và từ 20% đến 96% trên sáu tác vụ thật với tay đôi ALOHA (bốn tác vụ trên 80%), với vài chục demo mỗi tác vụ.");
P("**Diffusion Policy.** DP [@dp] mô hình hóa phân bố của chuỗi hành động bằng quá trình khuếch tán khử nhiễu (DDPM [@ddpm]), có lợi khi demo đa mode. Đổi lại, suy luận cần nhiều bước khử nhiễu và mạng UNet lớn hơn. Một số công trình gần đây cho rằng lợi thế của chính sách sinh chủ yếu đến từ tính toán lặp có giám sát bước giữa, không phải từ khả năng đa mode, và một hồi quy hai bước (MIP) có thể ngang flow/diffusion [@mip].");
P("**Mô hình thị giác–ngôn ngữ–hành động (VLA).** π0 [@pi0] và SmolVLA [@smolvla] tận dụng mô hình nền tảng lớn và dữ liệu đa robot. Với GPU 8 GB, việc tinh chỉnh các mô hình này có thể không vừa bộ nhớ (chưa kiểm), và chúng không phải trọng tâm của đồ án.");

H2("2.3. Visual servoing và thao tác hai tay");
P("Visual servoing điều khiển robot sao cho ảnh hiện tại tiến tới một ảnh đích, theo hướng cổ điển (IBVS/PBVS) hoặc học sâu [@P01,@P02]. Các phương pháp học gần đây dùng tương ứng đặc trưng (CNS [@P05], CNSv2 [@P06]), đặc trưng ViT tiền huấn luyện (ViT-VS [@P07]), luồng quang học (FlowControl [@P18]) hoặc chính sách khuếch tán (DiffusionVS [@P04]). Phần lớn giả định camera gắn tay và một ảnh đích của vật, tức là bài toán “tiến tới tư thế đích” hơn là “bắt một vật đang trôi”.");
P("Thao tác hai tay [@P03] mở rộng học bắt chước sang phối hợp hai tay: ACT gốc [@act] và các biến thể phối hợp liên tay [@P21], học một lần (ODIL [@P17]), chính sách khuếch tán có ràng buộc an toàn hoặc động học [@P23,@P24,@P25,@P26], tăng cường dữ liệu [@P30], và các chính sách 3D [@P29]. Những phương pháp này cần tay thứ hai, nhiều camera, hoặc cảm biến xúc giác/lực [@P11,@P22].");

H2("2.4. Benchmark 30 bài báo trên cùng arena");
P("Để trả lời CH1 bằng bằng chứng thay vì ấn tượng, đồ án dùng một benchmark của nhóm (thư mục `Benmark_Capstone`): 30 bài báo được chọn trước, mỗi bài được cố gắng tái lập trên **chính arena của đồ án** (commit `4963d40`, cùng bộ vật, cùng cảnh, cùng tờ sắp xếp DEV) với cùng giao thức: lưới DEV 40 lượt (dev_C0 và dev_C2, 10 cảnh mỗi ô, ở L0 và L0,25), so ghép cặp với CL0, ORACLE và NOOP. Mỗi bài được gắn một mức trung thực: **port nguyên phương pháp**, **cài lại trung thành**, **phương pháp điều chỉnh**, **chỉ thành phần**, hoặc **không cài được**, kèm lý do bị chặn nếu có.");
TABLE("Tình trạng của 30 bài báo trên arena (benchmark của nhóm, xuất ngày 10/11/2026)", ["Mã", "Bài báo (rút gọn)", "Nhóm", "Trạng thái trên arena", "Lý do chính / ghi chú"], [
    ["P01–P03", "Ba bài tổng quan [@P01,@P02,@P03]", "Tổng quan", "Không chạy", "Không có phương pháp để chạy"],
    ["P04", "DiffusionVS [@P04]", "VS + khuếch tán", "Bị chặn", "Không có mã/trọng số; camera gắn tay; cần ~2,4 triệu khung huấn luyện"],
    ["P05", "CNS [@P05]", "VS", "Xong DEV (thành phần)", "Chỉ bộ so khớp; 18/40"],
    ["P06", "CNSv2 [@P06]", "VS", "Bị chặn", "Chưa công bố mã; camera gắn tay; cần 6.852 mô hình 3D"],
    ["P07", "ViT-VS [@P07]", "VS", "Xong DEV (thành phần)", "Chỉ tương ứng DINOv2; 12/40"],
    ["P08", "Hyper-network VS [@P08]", "VS", "Bị chặn", "Không mã/checkpoint; camera gắn tay"],
    ["P09", "VFAS-Grasp [@P09]", "Gắp vòng kín", "Bị chặn", "Thiếu checkpoint; cần đám mây điểm từ camera cổ tay"],
    ["P10", "Grasp-MPC [@P10]", "Gắp vòng kín", "Bị chặn", "Không công bố mã, hàm giá trị và dữ liệu 2 triệu quỹ đạo"],
    ["P11", "Reactive DP [@P11]", "IL xúc giác", "Bị chặn", "Cần cảm biến xúc giác/lực và camera cổ tay"],
    ["P12", "YOLO11-SMMA [@P12]", "VS thu hoạch", "Bị chặn", "Toàn văn trả phí; không mã"],
    ["P13–P16", "VS tay đôi, người máy, đa camera, robot bay [@P13,@P14,@P15,@P16]", "Tay đôi", "Bị chặn", "Hai tay / robot bay; phần lớn không có mã"],
    ["P17", "ODIL [@P17]", "IL tay đôi", "Xong DEV (thành phần)", "Chỉ giai đoạn đăng ký hình học; 25/40"],
    ["P18", "FlowControl [@P18]", "VS", "Một phần", "12/40 lượt, 0 thành công; ~22 phút mỗi lượt"],
    ["P19", "ACT [@act]", "IL", "Xong DEV (port nguyên)", "Một tay, một camera; 20/40"],
    ["P20–P22", "Transformer IL tay đôi, ACT phối hợp liên tay, Bi-Touch [@P20,@P21,@P22]", "IL/RL tay đôi", "Bị chặn", "Cần tay thứ hai hoặc xúc giác; không mã/checkpoint"],
    ["P23–P28", "SafeBimanual, PACT, KStar Diffuser, ManiDP, DP đế di động, VLM-SFD [@P23,@P24,@P25,@P26,@P27,@P28]", "DP tay đôi", "Bị chặn", "Mã chưa công bố hoặc gắn với môi trường khác; cần hai tay"],
    ["P29", "3D FlowMatch Actor [@P29]", "IL 3D", "Bị chặn", "Chưa qua cổng dữ liệu độ sâu khi chuẩn bị"],
    ["P30", "D-CODA [@P30]", "Tăng cường dữ liệu", "Bị chặn", "Cần camera cổ tay và tay thứ hai"],
], [9, 30, 13, 18, 30], { source: "`Benmark_Capstone/reports/deadline/latest/coverage_30.csv`, `COVERAGE_30.md`." });
P("Tổng kết: 3 bài tổng quan không chạy; **22 bài bị chặn**, trong đó 15 bài cần phần cứng ngoài nền tảng (tay thứ hai, cảm biến xúc giác/lực, camera cổ tay hoặc robot di động) và 7 bài thiếu mã, checkpoint hoặc dữ liệu, hay chưa qua cổng kỹ thuật; 1 bài chạy một phần; **4 bài chạy trọn lưới DEV**, trong đó 3 bài chỉ là thành phần (bộ nhận thức của bài được gắn vào bộ thực thi của CL0) và chỉ **P19 (ACT) là port nguyên phương pháp**.");
TABLE("Kết quả DEV của benchmark trên 40 lượt chung (dev_C0, dev_C2 × L0, L0,25; ghép cặp với CL0, McNemar chính xác hai phía)", ["Phương pháp", "Mức trung thực", "Thành công", "Wilson 95%", "Chỉ PP đạt / chỉ CL0 đạt", "p"], [
    ["ORACLE", "đặc quyền (trần)", "40/40 (100%)", "91,2–100", "5 / 0", "0,0625"],
    ["CL0", "baseline mô-đun", "35/40 (87,5%)", "73,9–94,5", "—", "—"],
    ["P17 ODIL", "thành phần", "25/40 (62,5%)", "47,0–75,8", "3 / 13", "0,021"],
    ["P19 ACT", "port nguyên", "20/40 (50,0%)", "35,2–64,8", "3 / 18", "0,0015"],
    ["P05 CNS", "thành phần", "18/40 (45,0%)", "30,7–60,2", "0 / 17", "< 0,001"],
    ["P07 ViT-VS", "thành phần", "12/40 (30,0%)", "18,1–45,4", "1 / 24", "< 0,001"],
    ["NOOP", "không làm gì", "0/40", "0–8,8", "—", "—"],
], [20, 18, 16, 14, 18, 14], { center: [2, 3, 4, 5], source: "tính lại từ `Benmark_Capstone/results/raw/*/trials.csv` bằng `scripts/p7_bench_compare.py` (khớp số của benchmark)." });

H2("2.5. Tiêu chí và ma trận chọn phương pháp");
P("Từ yêu cầu của bài toán và của nền tảng, đồ án dùng năm tiêu chí: (i) chạy được với **một tay và một camera RGB cố định**, không cần độ sâu, xúc giác hay camera cổ tay; (ii) có **mã nguồn** và hỗ trợ SO-101; (iii) **huấn luyện được trên GPU 8 GB** trong vài giờ; (iv) có cách xử lý **vật đang di chuyển**; (v) có **kết quả đo được** trên arena. Bảng 2.3 tóm tắt các ứng viên.");
TABLE("Ma trận chọn phương pháp học", ["Ứng viên", "(i) Một tay, RGB cố định", "(ii) Mã, SO-101", "(iii) GPU 8 GB", "(iv) Vật di động", "(v) Trên arena (DEV)"], [
    ["ACT [@act]", "Có", "Có (LeRobot)", "Có: ~2,3 giờ, 1,8 GB VRAM", "Gián tiếp (chunk); cần giao diện hệ băng", "P19: 50%; ACT_I2 của đồ án: 75%"],
    ["Diffusion Policy [@dp]", "Có", "Có (LeRobot)", "Có, phải thu nhỏ UNet; ~4 giờ", "Gián tiếp", "Benchmark chưa huấn luyện; DP_W: 65–80% (L0,5)"],
    ["VLA (π0, SmolVLA) [@pi0,@smolvla]", "Có", "Có (LeRobot)", "Tinh chỉnh có thể không vừa (chưa kiểm)", "—", "Không chạy"],
    ["VS học (CNS, ViT-VS, FlowControl)", "Cần ảnh đích; bài gốc dùng camera gắn tay", "Một phần", "Không cần huấn luyện lại (thành phần)", "Không: servo tới ảnh đích", "30–45%; FlowControl 0/12"],
    ["Đăng ký hình học (ODIL)", "Cần độ sâu", "Một phần", "Không cần huấn luyện (thành phần)", "Không", "62,5%"],
    ["CL0 (mô-đun, không học)", "Có", "Tự viết", "Không cần huấn luyện", "Có: theo dõi trong hệ băng", "87,5%"],
], [19, 17, 13, 17, 16, 18]);
P("**Lựa chọn.** ACT được chọn làm **chính sách học trọng tâm** vì là phương pháp duy nhất thỏa cả năm tiêu chí: thiết kế ngay từ đầu cho phần cứng giá rẻ, có sẵn trong LeRobot cho SO-101, huấn luyện 100.000 bước chỉ mất khoảng 2,3 giờ và 1,8 GB VRAM trên RTX 3070 Ti (đo ở E11), và là bài báo duy nhất trong 30 bài được port nguyên phương pháp. Cơ chế dự đoán chunk của ACT cũng phù hợp với độ trễ của camera cố định. Điểm thiếu duy nhất là xử lý vật di động; đây chính là chỗ đồ án đóng góp giao diện I2 (mục 3.4). **Diffusion Policy** được giữ làm baseline học thứ hai để trả lời CH4. **CL0** là baseline mô-đun mạnh nhất chạy được, dùng chung bộ thực thi hệ băng, nên phép so ACT với CL0 cô lập được phần “nhận thức và chọn điểm kẹp”. **ORACLE** (nhận thức bằng ground truth) đo trần của môi trường.");

H2("2.6. Kết luận chương");
P("So sánh 30 bài báo cho thấy phần lớn phương pháp gần đây không chạy được trên nền tảng một tay, camera cố định, chủ yếu vì yêu cầu phần cứng. Trong số chạy được, ACT là ứng viên học duy nhất được port nguyên vẹn và vừa với ngân sách tính toán. Bản port ACT mặc định của benchmark chỉ đạt 50% trên DEV, thấp hơn CL0 (87,5%), gợi ý rằng ACT “nguyên bản” chưa đủ cho bài toán băng chuyền và cần được điều chỉnh, đặc biệt ở biểu diễn hành động. Chương 3 trình bày các điều chỉnh đó.");

// ======================================================================= Chapter 3
H1("PHƯƠNG PHÁP");
H2("3.1. Môi trường mô phỏng arena");
P("Arena được dựng trên Isaac Sim 6.0.0.1 [@isaac] theo bố trí của bàn thí nghiệm thật: mô hình USD của SO-101 (đã kiểm FK so với động học của CL0), băng rộng 200 mm với mặt băng ngang đế robot, và camera đặt tại [249, −280, 497,6] mm như camera thật. Vật lý chạy 300 bước mỗi giây, điều khiển 50 Hz và camera 30 khung/s, để biên của nhịp điều khiển và khung hình trùng với bước vật lý. Mô phỏng chạy **lockstep** với phương pháp: phương pháp nhận khung hình, trả lệnh, rồi mô phỏng mới tiến. Mỗi lượt dựng lại cảnh PhysX từ đầu; kiểm tra lặp lại cho thấy 40/40 lượt cho cùng kết quả bất kể thứ tự chạy.");
P("**Bộ vật.** 36 vật được sinh theo thủ tục (hộp, trụ, chữ L, chữ T, cốc, vòng, chữ U, tấm mỏng), chia cố định thành 20 vật **train** (chỉ dùng để ghi demo), 6 vật **dev** (tinh chỉnh) và 10 vật **test**. Bộ test gồm các dạng khó với heuristic: 3 vật lõm hoặc có quai, 2 vật mỏng, 2 vật tương phản thấp với mặt băng và 3 vật thường (Hình 3.1).");
FIG(fig("fig_objects.png"), 12, "Bộ 36 vật của arena và vị trí trên băng; nhãn dưới mỗi vật ghi tên và tập (train, dev, test) cùng dạng khó (`runs/e5/objects_sheet.png`)");
P("**Tờ sắp xếp và tập dữ liệu.** Mỗi ô (mức lộn xộn C0–C3) có tờ sắp xếp sinh bằng hạt giống cố định cho từng tập: `train_C*` (ghi demo), `dev_C*` (phát triển) và `test_C*` (khóa trong thư mục `locked/`, chỉ chạy khi có lệnh). Mỗi tờ sắp xếp dùng chung cho mọi phương pháp, nên mọi so sánh là **ghép cặp** trên cùng cảnh.");
P("**Gán nhãn tự động.** Bộ gán nhãn đọc chuỗi ground truth 50 Hz của mỗi lượt và áp quy tắc viết trước (`LABEL_RULES.md`): thành công (M1), thành công sạch (không vật nào khác bị xô quá 10 mm) và nguyên nhân thất bại theo danh sách đóng `collision`, `slip`, `grasp_point`, `timing`, `calib`, `seg_miss`, `merge`, `other`. Lượt **không hợp lệ** (`valid=0`) chỉ dành cho lỗi mô phỏng (Isaac sập, NaN vật lý, vật xuyên băng); thất bại của phương pháp luôn được tính. Nếu quá 10% lượt không hợp lệ thì dừng và sửa.");

H2("3.2. Chuyên gia ORACLE và dữ liệu demo");
P("Không có người điều khiển trong mô phỏng, nên demo được sinh bởi **ORACLE**: nhận thức lấy từ ground truth (vị trí, hướng và kích thước thật của vật) và phần điều khiển dùng đúng bộ thực thi hệ băng của CL0. Chính sách học chỉ thấy ảnh camera và trạng thái của tay, không thấy ground truth.");
BL([
    "**Demo E6 (đồ án):** ORACLE chạy 560 lượt trên vật train, các ô `train_C0..C3`, ở L0 và L0,25; giữ 444 tập thành công (115.908 khung, 0 lượt không hợp lệ). Demo **không có** tốc độ L0,5.",
    "**Demo P3 (sau đóng băng):** ORACLE_W (ORACLE có W1, mục 3.6) chạy 840 lượt ở L0, L0,25 và L0,5; giữ 677 tập (229, 233 và 215 tập theo tốc độ; 171.834 khung).",
    "**Định dạng:** LeRobotDataset; ảnh 3×360×640, trạng thái 6 chiều, hành động 6 chiều, 30 khung/s.",
]);

H2("3.3. Kiến trúc ACT");
P("ACT [@act] là một CVAE [@cvae] điều kiện theo quan sát. Bộ mã hóa ảnh ResNet-18 [@resnet] (tiền huấn luyện ImageNet) biến ảnh camera thành lưới đặc trưng; cùng với trạng thái của tay và một biến ẩn z, các token này đi qua bộ mã hóa Transformer [@transformer], và bộ giải mã Transformer xuất ra **một chunk k = 100 hành động** liên tiếp. Khi huấn luyện, một bộ mã hóa phụ nhìn chuỗi hành động thật để suy ra phân bố hậu nghiệm q(z | a, s); khi suy luận, z lấy bằng trung bình tiên nghiệm (z = 0). Hàm mất mát là:");
EQ("ℒ = ‖â₁:ₖ − a₁:ₖ‖₁ + β · KL( q(z | a₁:ₖ, s) ‖ 𝒩(0, I) ),   β = 10");
P("Bảng 3.1 ghi cấu hình dùng trong đồ án. Cấu hình là mặc định của LeRobot 0.6.1 cho ACT; đồ án không tinh chỉnh siêu tham số của mạng, để mọi khác biệt giữa các biến thể đến từ giao diện, dữ liệu hoặc cách suy luận.");
TABLE("Cấu hình ACT (đọc từ `config.json` của checkpoint `runs/act_i2_s1000`)", ["Tham số", "Giá trị", "Tham số", "Giá trị"], [
    ["Bộ mã hóa ảnh", "ResNet-18 (ImageNet)", "Kích thước chunk k", "100"],
    ["d_model / số đầu chú ý", "512 / 8", "Số lớp encoder / decoder", "4 / 1"],
    ["Chiều biến ẩn z", "32", "Trọng số KL β", "10"],
    ["Learning rate (mạng, backbone)", "1·10⁻⁵, 1·10⁻⁵", "Dropout", "0,1"],
    ["Số bước huấn luyện / batch", "100.000 / 8", "Hạt giống", "1000 (và 2000, 3000)"],
    ["Đầu vào", "ảnh 3×360×640 + trạng thái 6 chiều", "Đầu ra", "100 × 6 hành động"],
], [27, 23, 27, 23]);

H2("3.4. Giao diện hành động I2 cho băng chuyền");
P("ACT mặc định của LeRobot (gọi là **J0**) xuất **góc khớp tuyệt đối**. Trên băng chạy, cách này có hai nhược điểm: (1) trong 3,3 giây thực hiện một chunk 100 khung, vật đã trôi đi 250 mm ở 75 mm/s, nên mọi hành động “đúng lúc chụp ảnh” đều sai lúc thực hiện; (2) demo chỉ có ở băng đứng yên và băng chậm, nên mạng chưa từng thấy bù chuyển động ở băng nhanh. Đồ án đề xuất giao diện **I2**, dựa trên ý tưởng conveyor tracking [@abb]: mạng chỉ học “đi đâu so với vật, trong hệ quy chiếu của băng”, còn **bộ thực thi** gánh phần băng trôi.");
P("Ký hiệu s(t) là quãng băng đã đi, û là vector đơn vị theo chiều băng, p_{w} là vị trí trong hệ thế giới (gốc ở đế robot). Vị trí trong hệ băng là:");
EQ("p_{b} = p_{w} − s(t) · û");
P("Với ảnh chụp tại t_{img}, nhãn huấn luyện của hành động thứ k là mục tiêu đầu kẹp trong hệ băng, tương đối so với đầu kẹp lúc chụp:");
EQ("a_{k} = p_{b, mục tiêu}(t_{img} + kΔ) − p_{b, EE}(t_{img})");
P("Khi thực hiện ở thời điểm t_{x}, bộ thực thi đổi ngược về hệ thế giới bằng quãng băng đi thêm từ lúc chụp:");
EQ("p_{w, lệnh}(t_{x}) = p_{w, EE}(t_{img}) + a_{k} + ( s(t_{x}) − s(t_{img}) ) · û");
P("Trạng thái đưa vào mạng là vector 6 chiều của đầu kẹp tại t_{img}: [x_{b}, y_{b}, z, cos 2ψ, sin 2ψ, g], với ψ là góc xoay kẹp và g là độ mở kẹp. Góc ψ được mã hóa bằng (cos 2ψ, sin 2ψ) vì kẹp hai má đối xứng: ψ và ψ + 180° là cùng một cách kẹp, nên 89° và −89° phải là hai giá trị gần nhau. Góc chúc của kẹp cố định thẳng đứng. Khi băng đứng yên, s(t) không đổi và nhãn I2 trùng nhãn hệ thế giới; đó là lý do demo ghi lúc băng đứng yên hoặc chậm vẫn dùng được khi băng nhanh.");
P("**Cài đặt.** Đồ án không sửa mô hình ACT. Ba thành phần được thêm: (1) `to_lerobot_i2.py` đổi nhãn 444 tập demo sang I2, lấy s(t) từ ground truth của băng và tính lại thống kê chuẩn hóa ở dạng tương đối; (2) `train_act_i2.py` chạy `lerobot-train` nguyên bản, chỉ thay bộ tiền/hậu xử lý của ACT bằng thứ tự của π0 trong LeRobot (dữ liệu thô → hành động tương đối → chuẩn hóa → mô hình → bỏ chuẩn hóa → hành động tuyệt đối); (3) `arena/methods/act_i2.py` là bộ thực thi: mỗi nhịp 50 Hz lấy mục tiêu nội suy ở chỉ số (t − t_{img})·30 trong chunk, đổi về hệ thế giới theo phương trình (3.4), giải IK ở góc chúc cố định, giới hạn tốc độ khớp và độ cao tối thiểu trên băng như bộ thực thi của CL0 (Hình 3.2).");
FIG(fig("fig_act_i2_pipeline.png"), 16, "Sơ đồ ACT_I2: ảnh và trạng thái I2 tại thời điểm chụp → ACT xuất chunk 100 mục tiêu tương đối trong hệ băng → bộ thực thi bù quãng băng đi và giải IK ở 50 Hz");
P("**Kiểm tra trước khi học.** Hai kiểm tra không cần huấn luyện xác nhận giao diện đúng. Thứ nhất, đổi nhãn không làm mất thông tin: góc chúc của hành động demo nằm trong 1° quanh 90° ở 99,4% số khung, và FK → IK ở góc chúc cố định sai không quá 0,016 mm. Thứ hai, phát lại hở (open-loop) nhãn I2 của 4 tập demo qua đúng bộ thực thi, trên đúng cảnh và tốc độ của lượt gốc, gắp thành công 3/4; tập hỏng có quỹ đạo TCP trùng lượt gốc trong khoảng 1 mm tới 2,7 s, và hỏng vì kẹp kẹt trên vật khi khép (lượt gốc vốn sát nút).");

H2("3.5. Cách suy luận: chunk và lập kế hoạch lại");
P("Với n_action_steps = 100, chính sách thực hiện trọn chunk 100 khung (khoảng 3,3 s) rồi mới chụp ảnh và lập kế hoạch lại; đồ án gọi chế độ này là **/100**. Đồ án thử thêm hai chế độ: **/10** (lập kế hoạch lại mỗi 10 khung) và **COMMIT** (lập kế hoạch lại mỗi 10 khung khi chính sách còn ra lệnh mở kẹp, và chạy hết chunk khi nó ra lệnh đóng). Mỗi lần chọn chế độ đều dùng một **quy tắc ghi trước** khi xem kết quả (mục 4.3). Temporal ensembling của ACT gốc không được dùng, vì với I2 mỗi chunk gắn với một thời điểm chụp riêng.");

H2("3.6. Các phương pháp so sánh");
H3("3.6.1. CL0: pipeline mô-đun không huấn luyện");
P("CL0 là baseline cổ điển, viết trước khi có arena và được đóng băng bằng băm SHA-256 của mã (`006af1c9…`). Các bước: (1) hiệu chuẩn camera → mặt phẳng băng; (2) tách nền bằng mô hình nền của băng trống → mặt nạ → thành phần liên thông; (3) với mỗi vật, điểm kẹp là cực đại của biến đổi khoảng cách (chịu được vật lõm tốt hơn trọng tâm), góc kẹp vuông góc trục dài theo PCA, bỏ vật rộng hơn độ mở kẹp; (4) chọn vật xuôi dòng nhất trong vùng với tới; (5) theo dõi vị trí vật trong hệ băng qua nhiều khung; (6) bộ thực thi **BeltExecutor** (IK + s(t)), cũng là bộ thực thi mà ORACLE dùng. CL0 được tinh chỉnh tối đa trong giới hạn thời gian ghi trước, chỉ trên vật và cảnh DEV.");
H3("3.6.2. ORACLE và NOOP");
P("ORACLE thay bước (2)–(5) của CL0 bằng ground truth, nên là trần của môi trường với cùng bộ thực thi; đây không phải trần thuật toán, vì nó bị giới hạn bởi chính bộ thực thi. NOOP không làm gì, để phát hiện thành công “miễn phí” do môi trường gây ra.");
H3("3.6.3. Diffusion Policy (DP_W)");
P("DP_W dùng Diffusion Policy của LeRobot [@dp] với cùng giao diện I2 và cùng dữ liệu với ACT_W: horizon 64 bước, 2 quan sát, thực hiện 32 bước mỗi lần, UNet 1D với các kênh (256, 512, 1024), DDPM [@ddpm] 100 bước cả khi huấn luyện và suy luận, ResNet-18 với spatial softmax 32 điểm, learning rate 10⁻⁴, batch 16, 82.000 bước. UNet mặc định (512, 1024, 2048) không vừa 8 GB VRAM ở batch 16, nên phải thu nhỏ; quyết định này chốt trước khi có kết quả DP nào. Vì DP nhìn 2 quan sát, bước tương đối của LeRobot được viết lại để lấy trạng thái của quan sát cuối làm mốc (`arena/dp_i2.py`).");
H3("3.6.4. W1: chọn nhánh góc kẹp theo cổ tay (sau đóng băng)");
P("Với kẹp thẳng đứng của SO-101, góc trục khép của kẹp liên hệ với khớp đế q1 và khớp xoay cổ tay q5 theo yaw = −q1 + q5 + 177,21° (đúng theo FK, kiểm trên 1.026 tư thế). IK của CL0 khớp góc theo mod 180°, nên có hai nhánh θ và θ + 180°; nhánh được chọn theo lệnh trước đó. Khi bám vật trên băng nhanh, khớp đế quay 20–50° và cổ tay quay theo đúng chừng đó; nếu nhánh đang dùng đẩy cổ tay tới giới hạn khớp, IK thất bại, lệnh bị giữ và vật trôi mất. **W1** dự báo quỹ đạo khớp trên cửa sổ bám 0,5–4,0 s cho mọi nhánh θ + 180°·k (xoay tối đa 270°), dùng tốc độ lệnh của băng cùng dốc tăng tốc 200 mm/s², và chỉ đổi nhánh khi cổ tay dự báo vào trong 10° quanh biên; khi đó chọn nhánh vi phạm muộn nhất. Lượt không cần đổi nhánh chạy đúng mã CL0. W1 không đổi nhận thức hay cách chọn vật, mất trung vị 195 ms mỗi lượt, và được duyệt như một thay đổi thuật toán của baseline (CL0_W) ngày 15/11/2026, trước khi chạy TEST mới.");

H2("3.7. Giao thức đánh giá");
BL([
    "**Ghép cặp.** Mọi phương pháp chạy trên cùng tờ sắp xếp và tốc độ; so hai phương pháp bằng **kiểm định McNemar chính xác** [@mcnemar] trên các cặp bất đồng (chỉ A đạt / chỉ B đạt). Tỉ lệ thành công đi kèm khoảng **Wilson 95%** [@wilson].",
    "**Tách DEV và TEST.** Mọi tinh chỉnh, chọn checkpoint và chọn chế độ suy luận chỉ dùng DEV. Tờ TEST sinh trước, khóa trong `locked/`, và chỉ chạy một lần theo lệnh rõ ràng.",
    "**Tiền đăng ký.** Trước mỗi TEST, giả thuyết, ngưỡng, số lượt, phương pháp, checkpoint (băm SHA-256) và quy tắc quyết định được viết vào một file và commit: `PREREGISTRATION_G2.md` (đồ án), `PREREGISTRATION_E18.md` (40 nhiệm vụ), `PREREGISTRATION_PAPER.md` (TEST mới). Sai lệch chỉ được ghi thêm vào mục “Sai lệch”, không sửa nội dung đã khóa.",
    "**Nhiều phép so.** Khi kiểm nhiều giả thuyết trên cùng TEST, dùng hiệu chỉnh Holm [@holm]. Giả thuyết về hạt giống (H2 của TEST mới) dùng kiểm định hoán vị đổi dấu trên chênh lệch trung bình theo hạt giống.",
    "**Trung thực.** Không sửa tay file kết quả, không xóa lượt hay log; mọi con số trong báo cáo có đường dẫn bằng chứng (Phụ lục A).",
]);

// ======================================================================= Chapter 4
H1("THỰC NGHIỆM VÀ KẾT QUẢ");
H2("4.1. Thiết lập thực nghiệm");
P("Mọi thí nghiệm chạy trên một máy với GPU RTX 3070 Ti 8 GB, Isaac Sim 6.0.0.1 (Python 3.12) cho mô phỏng và LeRobot 0.6.1 trong một môi trường Python riêng cho chính sách học. Chính sách học chạy như một **máy chủ suy luận** riêng, nói chuyện với arena qua socket; mỗi lượt ACT mất khoảng 140 s thời gian thực (20 s mô phỏng cộng chuyển ảnh qua cầu nối). Bảng 4.1 tóm tắt chi phí huấn luyện.");
TABLE("Chi phí huấn luyện các chính sách học (RTX 3070 Ti 8 GB)", ["Mô hình", "Dữ liệu", "Bước × batch", "Thời gian", "Ghi chú"], [
    ["ACT_J0 s1000", "444 tập E6, góc khớp", "100.000 × 8", "2 giờ 15 phút", "12,4 bước/s, 1,8 GB VRAM; loss 13,9 → 0,038"],
    ["ACT_I2 s1000 (ACT_old)", "444 tập E6, I2", "100.000 × 8", "2 giờ 27 phút", "loss 4,44 → 0,053"],
    ["ACT_I2F s1000", "520 tập (E6 + 76 tập L0,5)", "100.000 × 8", "2 giờ 14 phút", "chỉ khác dữ liệu"],
    ["ACT_W s1000/2000/3000", "677 tập P3, I2", "100.000 × 8", "~2,25 giờ mỗi hạt giống", "sau đóng băng"],
    ["DP_W s1000/2000/3000", "677 tập P3, I2", "82.000 × 16", "~4 giờ mỗi hạt giống", "sau đóng băng; UNet thu nhỏ"],
], [24, 22, 14, 17, 23], { source: "`ARENA_SETUP_REPORT.md` (E11, E14, E15), `BAO_CAO_PAPER_DEV.md` mục 6, log `logs/*_train_*.log`." });

H2("4.2. Từ ACT mặc định đến ACT_I2 (E11, E14)");
P("**E11: ACT mặc định (J0).** Bước đầu kiểm đường ống: ACT mặc định của LeRobot, hành động là góc khớp, học trên 444 tập E6. Trên DEV, ACT_J0 đạt 15/20 và 19/20 ở dev_C0 (L0 và L0,25), 14/20 và 14/20 ở dev_C1, ngang CL0 (12, 17, 15, 14) và dưới ORACLE (20/20 mỗi ô); không ô nào khác CL0 có ý nghĩa. ACT làm được việc cơ bản trên vật lạ ở băng chậm.");
P("**E14: giao diện I2.** Bảng 4.2 so ACT_I2 với ACT_J0, CL0 và ORACLE trên cùng cảnh. Kết quả nổi bật nằm ở **L0,5 (75 mm/s), tốc độ không có trong demo**: ACT_I2 đạt 13/20 so với 4/20 của ACT_J0 (I2 hơn 11 cặp, kém 2 cặp; p = 0,022) và gần ORACLE (16/20). Ở băng đứng yên, I2 lại kém J0 và CL0 (dev_C0 + dev_C1 ở L0: 20/40 so với 29/40 và 27/40), chưa có ý nghĩa ở từng ô; nguyên nhân chưa được kiểm (giả thuyết: mạng không thấy góc khớp, mã hóa yaw, lập kế hoạch lại chỉ mỗi 3,3 s).");
TABLE("ACT_I2 so với ACT_J0, CL0 và ORACLE trên DEV (n = 20 mỗi ô, ghép cặp, McNemar chính xác hai phía)", ["Ô", "ACT_I2", "ACT_J0", "CL0", "ORACLE", "I2 vs J0 (hơn/kém, p)", "I2 vs CL0 (hơn/kém, p)"], [
    ["dev_C0 L0", "11", "15", "12", "20", "2/6, 0,29", "3/4, 1"],
    ["dev_C0 L0,25", "19", "19", "17", "20", "1/1, 1", "3/1, 0,63"],
    ["dev_C1 L0", "9", "14", "15", "20", "2/7, 0,18", "1/7, 0,070"],
    ["dev_C1 L0,25", "11", "14", "14", "20", "4/7, 0,55", "3/6, 0,51"],
    ["dev_C2 L0", "11", "—", "12", "20", "", "5/6, 1"],
    ["dev_C2 L0,25", "16", "—", "16", "18", "", "3/3, 1"],
    ["**dev_C2 L0,5**", "**13**", "**4**", "**6**", "16", "**11/2, 0,022**", "10/3, 0,092"],
], [17, 10, 10, 9, 11, 21, 22], { center: [1, 2, 3, 4, 5, 6], source: "`ARENA_SETUP_REPORT.md` mục E14; `runs/e14_act_i2_dev`, `runs/e14_act_i2_dev2`, `runs/e11_act_dev`, `runs/e14_act_j0_dev2`, `runs/e8_real`, `runs/e9_clutter_real`, `runs/e10_base_L05`." });
FIG(fig("fig_j0_vs_i2.png"), 15, "Giao diện hành động ở băng nhanh (dev_C2, L0,5, 20 cảnh): I2 nâng ACT từ 4/20 lên 13/20 dù demo không có tốc độ này");
NOTE("Ý nghĩa: giao diện I2 là điều chỉnh quan trọng nhất giúp ACT dùng được trên băng chạy. Vì J0 khác I2 cả ở giao diện lẫn không gian hành động (khớp so với đầu kẹp), kết quả này chưa tách riêng được hai yếu tố.");

H2("4.3. Biến thể suy luận và dữ liệu của ACT_I2 (E15, E16)");
P("Sau E14, đồ án thử ba hướng cải thiện ACT_I2 ở băng nhanh và nhiều vật, mỗi hướng có quy tắc chọn ghi trước: (a) lập kế hoạch lại thường xuyên hơn (/10), (b) thêm 76 tập demo ở L0,5 (ACT_I2F), (c) chế độ COMMIT. Đánh giá trên 4 ô DEV khó nhất (dev_C2, dev_C3 × L0,25, L0,5; tổng 80 lượt).");
FIG(fig("fig_act_variants.png"), 15, "Các biến thể của ACT_I2 trên 80 lượt DEV (dev_C2, dev_C3 × L0,25, L0,5); không biến thể nào hơn /100 có ý nghĩa");
BL([
    "**/10 so với /100:** 39/80 so với 48/80. /10 giúp ở dev_C3 L0,25 (16 so với 10) nhưng hại ở L0,5 (dev_C2: 6 so với 13). Theo quy tắc ghi trước, giữ /100.",
    "**Thêm demo L0,5 (ACT_I2F):** 50/80 so với 48/80 (hơn 13, kém 11; p = 0,84). Lợi thế ở băng nhanh đến từ giao diện I2, không cần demo nhanh.",
    "**COMMIT:** 41/80; quy tắc ghi trước đòi ≥ 53/80, nên không nhận. Phân tích GT cho thấy COMMIT sửa được lệch ngang của điểm kẹp (trung vị −9,2 → +1,8 mm) nhưng gây lệch dọc băng (−6,6 mm) và nhấc sớm hơn.",
    "**Sàn nhiễu:** chạy lại /100 trên dev_C2 L0,5 cho 13 → 14/20, với 3/20 lượt đổi kết quả. Chênh ±3 lượt trên một ô 20 lượt chưa phân biệt được với nhiễu giữa các lần chạy.",
]);
P("**Phân tích lỗi (E16, chỉ từ ground truth).** Lỗi chính của ACT_I2 /100 là **đóng kẹp vào chỗ trống**: trong 62 lượt hỏng trên sáu ô DEV, 37 lượt (60%) khép hẳn kẹp mà không có vật, 16 lượt nhấc được một phần, 8 lượt nhấc nhưng không giữ đủ 2 s. Độ lệch ngang của TCP so với tâm vật gần nhất lúc đóng kẹp có trung vị −9,2 mm (độ lệch chuẩn 13,6 mm), trong khi CL0 là +2,3 mm và ORACLE +0,1 mm. Lệch này không tỉ lệ với vị trí hay chiều cao vật, và biến mất khi lập kế hoạch lại mỗi 10 khung, nên nhiều khả năng đến từ kế hoạch đầu của mô hình chứ không phải bộ thực thi. Kết luận rút ra cho đồ án: cải thiện chỉ ở phía suy luận không đủ; muốn vượt /100 cần thay đổi ở dữ liệu hoặc huấn luyện. Chính sách ACT_I2 /100 hạt giống 1000 được chốt cho G2.");

H2("4.4. Kiểm định có tiền đăng ký của đồ án (G2)");
P("**Thiết kế.** `PREREGISTRATION_G2.md` (commit trước lượt TEST đầu tiên) chốt: ô chính test_C2, L0,5, 60 cảnh ghép cặp; chính sách ACT_I2 /100 học trên demo E6, hạt giống 1000 là chính và hạt giống 2000 để nhắc lại (chỉ ước lượng điểm); claim C thành công khi ACT hơn CL0 **ít nhất 15 điểm**, McNemar p ≤ 0,05 và ACT đạt ≥ 60%.");
FIG(fig("fig_g2_test.png"), 15, "Kết quả TEST G2 (test_C2, L0,5, 60 cảnh vật lạ ghép cặp)");
TABLE("Kết quả G2 trên test_C2, L0,5 (n = 60, 0 lượt không hợp lệ)", ["Phương pháp", "Thành công", "Wilson 95%", "So với CL0: chỉ ACT / chỉ CL0", "McNemar p"], [
    ["ORACLE", "28/60 (47%)", "35–59", "—", "—"],
    ["CL0", "22/60 (37%)", "26–49", "—", "—"],
    ["ACT_I2 hạt giống 1000", "21/60 (35%)", "24–48", "8 / 9", "1,00"],
    ["ACT_I2 hạt giống 2000", "18/60 (30%)", "20–43", "7 / 11", "0,48"],
], [26, 18, 16, 24, 16], { center: [1, 2, 3, 4], source: "`logs/2026-11-10_210822_g2_decision.txt`." });
P("**Kết luận G2: NO-GO.** Cả hai hạt giống đều không đạt ngưỡng (chênh −1,7 và −6,7 điểm), nên claim “ACT hơn mô-đun ≥ 15 điểm” bị bác bỏ theo đúng quy tắc ghi trước, không đổi ngưỡng, chính sách hay hạt giống. Các ô mô tả cũng cho kết quả tương tự: test_C0 (1 vật) ACT 9/30, CL0 10/30, ORACLE 18/30; test_C3 (4–5 vật chạm nhau) ACT 14/30, CL0 9/30, ORACLE 18/30. Đáng chú ý, ORACLE chỉ đạt 47% ở ô chính: trần của môi trường ở 75 mm/s thấp, nên chênh lệch giữa các phương pháp bị ép lại. Mục 4.6 giải thích trần thấp này.");
P("**Các kiểm tra phụ.** H4 (dev_C0 ở L1,0, 150 mm/s) cho 0/30 với mọi phương pháp kể cả ORACLE (hiệu ứng sàn, không kiểm được). Kiểm tra hệ thống G0 trên vật quen không đạt ngưỡng (CL0 6/20 ở L0,5); quyết định ghi trong mục “Sai lệch” của tiền đăng ký: vẫn chạy G2 với CL0 đóng băng và báo cáo giới hạn này.");

H2("4.5. Mở rộng đa nhiệm vụ (E18, phụ lục có tiền đăng ký)");
P("Để kiểm khả năng của ACT ngoài bài toán gắp, E18 huấn luyện **một** ACT_I2 đa nhiệm vụ (ACT_I2T) cho 40 nhiệm vụ trên băng đứng yên: gắp (6 loại vật), đặt vào vùng (12), kéo theo hướng (15) và lật đổ (7). Mã nhiệm vụ 12 chiều (họ, loại vật, tham số trong hệ băng) được đưa vào như một quan sát phụ, không đổi mô hình. 32 nhiệm vụ có demo; 8 nhiệm vụ **giữ lại** không có demo nhưng mỗi thành phần của chúng đều xuất hiện trong ít nhất một nhiệm vụ huấn luyện (tổng quát hóa tổ hợp).");
TABLE("Kết quả TEST E18 theo họ nhiệm vụ (ACT_I2T, một hạt giống; chuyên gia có đặc quyền TASK_EXPERT làm trần)", ["Họ", "ACT_I2T: nhiệm vụ đã học", "ACT_I2T: nhiệm vụ giữ lại", "Chuyên gia: đã học", "Chuyên gia: giữ lại"], [
    ["Gắp", "22/25 (88%)", "9/10 (90%)", "23/25", "10/10"],
    ["Đặt", "36/50 (72%)", "15/20 (75%)", "49/50", "18/20"],
    ["Kéo", "34/55 (62%)", "27/40 (67,5%)", "44/55", "36/40"],
    ["Lật", "30/30 (100%)", "7/10 (70%)", "28/30", "10/10"],
    ["**Tổng**", "**122/160 (76,2%)**", "**58/80 (72,5%)**", "", ""],
], [14, 22, 22, 21, 21], { center: [1, 2, 3, 4], source: "`logs/2026-11-12_204650_e18_decision.txt`; NOOP 0/80 trên nhiệm vụ giữ lại." });
P("Cả hai giả thuyết ghi trước đều được ủng hộ: **H-skills** (nhiệm vụ đã học ≥ 50% và mỗi họ ≥ 30%) và **H-compose** (nhiệm vụ giữ lại ≥ 30%, kiểm định nhị thức một phía so với p₀ = 0,01: p ≈ 2·10⁻⁹⁷). Đây là điểm mạnh rõ của ACT mà pipeline mô-đun không có sẵn: một mô hình duy nhất học được nhiều kỹ năng và ghép chúng cho nhiệm vụ mới. Kết quả chỉ có một hạt giống và ở băng đứng yên.");

H2("4.6. Sau đóng băng: lỗi cổ tay của bộ thực thi và W1");
P("Trần thấp của ORACLE ở 75 mm/s (47% ở G2) được điều tra trên DEV sau khi đóng băng đồ án. Thay đổi thông số vật lý của kẹp (ma sát, ma sát xoắn, độ cao kẹp, tốc độ nhấc, độ mở) không làm tăng thành công. Phân tích chuỗi khớp cho thấy cơ chế ở mục 3.6.4: khi bám vật, cổ tay quay theo khớp đế tới giới hạn −157,2°, IK thất bại, lệnh bị giữ 10 nhịp rồi nhảy 3°, tay ngừng bám và vật trôi thêm 30–50 mm, làm vật bị kéo hoặc xoay trong kẹp. Lỗi có ở 8/19 lượt hỏng của ORACLE trên train_C2 L0,5 nhưng chỉ 1/41 lượt đạt và 0/60 lượt khi băng đứng yên. Hình 4.4 minh họa một lượt ORACLE thất bại khác ở cùng tốc độ, do vật trượt khỏi kẹp.");
FIG(fig("fig_failure_seq.png"), 13, "Một lượt ORACLE thất bại ở L0,5 (train_C2_001, nhãn `slip`): kẹp khép trên vật trụ khi băng đang chạy, vật xoay trong kẹp và tuột lúc nhấc (`runs/p1_video_001`; lượt này không thuộc nhóm lỗi cổ tay)");
P("**CL0 chịu lỗi này nặng hơn nhiều so với ORACLE và ACT.** CL0 nhắm góc kẹp 90–130°, nên nhánh gần nhất đẩy cổ tay về phía biên âm: trên dev_C2 L0,5, 37/60 lượt CL0 có lệnh bị giữ ở biên cổ tay. Ngược lại, chỉ 2/100 lượt DEV của ACT_I2 có cổ tay chạm biên khi IK hỏng. Hình 4.5 và Bảng 4.5 cho tác dụng của W1 trên cùng cảnh.");
FIG(fig("fig_w1_effect.png"), 15, "Tác dụng của W1 trên cùng cảnh: lớn ở L0,5, nhỏ ở L0,25");
TABLE("Tác dụng của W1 (ghép cặp, McNemar chính xác hai phía)", ["Tờ, tốc độ", "Phương pháp", "Gốc → W1", "Mất / được", "p"], [
    ["train_C2 L0,5", "ORACLE", "41 → 49/60", "0 / 8", "0,0078"],
    ["train_C3 L0,5", "ORACLE", "35 → 44/60", "0 / 9", "0,0039"],
    ["dev_C2 L0,5", "ORACLE", "45 → 58/60", "0 / 13", "0,0002"],
    ["dev_C2 L0,5", "CL0", "25 → 52/60", "2 / 29", "5·10⁻⁷"],
    ["dev_C2 L0,25", "ORACLE / CL0", "27 → 29/30 / 24 → 26/30", "0 / 2 mỗi PP", "0,50"],
    ["dev_C2 L1,0", "ORACLE / CL0", "0 → 0/60", "0 / 0", "1"],
], [20, 18, 26, 18, 18], { center: [2, 3, 4], source: "`BAO_CAO_PAPER_DEV.md` mục 5; các thư mục `runs/p1_*`, `runs/p2_*`, `runs/p5_*`." });
P("**Hệ quả cho so sánh ACT với mô-đun.** Ở G2, CL0 bị lỗi cổ tay ở phần lớn số lượt trong khi ACT gần như không gặp, nên kết quả “ACT ≈ CL0” nhiều khả năng **bị lẫn**: nó so một ACT không gặp lỗi với một CL0 bị lỗi bộ thực thi. Với baseline mô-đun đã sửa (CL0_W đạt 52/60 trên DEV), một giả thuyết kiểu “ACT hơn mô-đun 15 điểm” gần như không thể đúng. Đây là suy luận từ DEV; TEST mới (mục 4.8) kiểm điều này. Ở L1,0, mọi phương pháp thất bại vì vật đi khoảng 315 mm trước khi tay kịp hạ xuống, ra khỏi tầm với; điều này giải thích 0/30 của H4 ở G2.");

H2("4.7. Chính sách học mới trên DEV: ACT_W và DP_W (sau đóng băng)");
P("Câu hỏi CH4 là: nếu chuyên gia sinh demo tốt hơn (ORACLE_W thay ORACLE) và có thêm demo L0,5, học sinh có tốt hơn không? Ba hạt giống ACT_W, một ACT_W_slow (chỉ demo L0, L0,25) và ba hạt giống DP_W được huấn luyện trên 677 tập demo P3, rồi đánh giá trên 20 cảnh DEV chung (dev_C2, L0,5) cùng mọi phương pháp khác (Hình 4.6).");
FIG(fig("fig_dev_l05_all.png"), 15, "Mọi phương pháp trên 20 cảnh DEV chung (dev_C2, L0,5); với 20 cảnh, khoảng tin cậy rộng khoảng ±20 điểm");
BL([
    "**Thầy tốt hơn không làm học sinh tốt hơn trên DEV:** ACT_W s1000 so với ACT_old s1000: mất 3, được 3 (15/20 mỗi bên). ACT_W_slow cũng 15/20. Khớp với E15 (thêm demo L0,5 không đổi kết quả)." + (F.P6.ok ? ` **TEST mới 60 cảnh cho kết quả ngược lại:** ACT_W hơn ACT_old ${F.P6.h2Text()} (H2, mục 4.8); 20 cảnh DEV không đủ để thấy chênh lệch này.` : ""),
    "**ACT và DP ngang nhau:** ACT 13–15/20, DP 13–16/20; chênh lệch giữa các hạt giống (13–16) cỡ chênh lệch giữa hai họ chính sách.",
    "**Lỗi của chính sách học là va chạm, không phải lỗi cổ tay:** ACT và DP thất bại chủ yếu do `collision` (3–7 lượt mỗi mô hình).",
    "**Baseline mô-đun đã sửa đứng đầu nhóm không đặc quyền:** CL0_W 17/20, so với CL0 gốc 7/20.",
]);

H2(F.P6.ok ? "4.8. TEST mới có tiền đăng ký (sau đóng băng)" : "4.8. TEST mới có tiền đăng ký (sau đóng băng, đang chạy)");
P("`PREREGISTRATION_PAPER.md` được khóa ở commit `248c7e8` ngày 18/11/2026, trước lượt TEST đầu tiên: tờ mới `locked/paper/test_C2.csv` (60 cảnh, hạt giống 1611, dùng lại 10 vật TEST cũ), mọi phương pháp ở L0,5 và các phương pháp mô-đun thêm ở L0,25. Ba giả thuyết với hiệu chỉnh Holm (α = 0,05): **H1** CL0_W hơn CL0 (McNemar một phía, chênh ≥ +15 điểm); **H1b** ORACLE_W hơn ORACLE (chênh ≥ +5 điểm); **H2** ACT_W khác ACT_old (hoán vị đổi dấu hai phía trên trung bình theo hạt giống). So sánh DP, ablation, học so với mô-đun và ô L0,25 chỉ để mô tả.");
TABLE("Kết quả TEST mới (test_C2 mới, n = 60 mỗi phương pháp)" + (F.P6.ok ? "" : " — điền khi chuỗi P6 xong"), ["Phương pháp", "L0,5: thành công", "Wilson 95%", "L0,25: thành công", "Ghi chú"], F.P6.tableRows() || [
    ["CL0", "{{…/60}}", "{{…}}", "{{…/60}}", ""],
    ["CL0_W", "{{…/60}}", "{{…}}", "{{…/60}}", "H1"],
    ["ORACLE", "{{…/60}}", "{{…}}", "{{…/60}}", ""],
    ["ORACLE_W", "{{…/60}}", "{{…}}", "{{…/60}}", "H1b"],
    ["ACT_old s1000 / s2000", "{{… / …}}", "{{…}}", "—", "H2 (đối chứng)"],
    ["ACT_W s1000 / s2000 / s3000", "{{… / … / …}}", "{{…}}", "—", "H2"],
    ["ACT_W_slow s1000", "{{…/60}}", "{{…}}", "—", "ablation"],
    ["DP_W s1000 / s2000 / s3000", "{{… / … / …}}", "{{…}}", "—", "mô tả"],
], [26, 20, 22, 16, 16], { center: [1, 2, 3], source: F.P6.src + "." });
TABLE("Quyết định theo tiền đăng ký (Holm trên H1, H1b, H2; α = 0,05)" + (F.P6.ok ? "" : " — điền khi chuỗi P6 xong"), ["Giả thuyết", "Chênh lệch", "p (thô)", "p (Holm)", "Kết luận"], F.P6.decisionRows() || [
    ["H1: CL0_W > CL0", "{{…}}", "{{…}}", "{{…}}", "{{…}}"],
    ["H1b: ORACLE_W > ORACLE", "{{…}}", "{{…}}", "{{…}}", "{{…}}"],
    ["H2: ACT_W ≠ ACT_old", "{{…}}", "{{…}}", "{{…}}", "{{…}}"],
], [24, 30, 10, 10, 26], { center: [2, 3], source: F.P6.ok ? F.P6.src + "; McNemar chính xác một phía (H1, H1b), hoán vị đổi dấu hai phía (H2)." : undefined });
if (F.P6.ok) {
    NOTE(F.P6.statusNote());
    if (F.figIf("fig_p6_test.png")) FIG(F.figIf("fig_p6_test.png"), 15, "TEST mới: mọi phương pháp trên test_C2 mới ở L0,5 (60 cảnh, vật chưa thấy); chỉ H1, H1b, H2 quyết định, phần còn lại là mô tả");
    P("**Phần mô tả** (không tham gia quyết định, theo mục 4 của tiền đăng ký):", { noIndent: true });
    BL([...F.P6.descBullets(),
        // checked against logs/2026-11-19_122405_p6_w1_compare.txt (commit c8b3449), test_C2 L0.5 blocks
        "**Cơ chế của W1 trên TEST** (L0,5, mô tả; `logs/2026-11-19_122405_p6_w1_compare.txt`): số lượt bị giữ lệnh ở biên khớp cổ tay xoay giảm từ 19 xuống 0 với CL0 và từ 16 xuống 0 với ORACLE; tổng số nhịp giữ lệnh giảm từ 3482 xuống 266 và từ 1548 xuống 0. W1 đổi nhánh ở 27 lượt CL0 và 18 lượt ORACLE; cả 7 lượt được của ORACLE và 20 trong 22 lượt được của CL0 nằm trong các lượt này, và không lượt đổi nhánh nào bị kém đi. Hai lượt được và một lượt mất còn lại của CL0 thuộc các lượt W1 không đổi nhánh (cùng đường mã với bản gốc), tức là nhiễu giữa hai lần chạy."]);
} else {
    NOTE("Tình trạng lúc viết (18/11/2026, 20:44): 7/17 lần chạy đã xong với 60/60 lượt hợp lệ mỗi lần, 0 lượt không hợp lệ; tỉ lệ thành công chưa được xem, theo đúng tiền đăng ký. Dự kiến xong khoảng 14:30 ngày 19/11/2026.");
}

H2("4.9. So sánh với các bài báo trên benchmark");
P("Phần này trả lời vế thứ hai của CH4 trên **đúng 40 lượt DEV** mà benchmark dùng cho mọi bài báo (dev_C0 và dev_C2, cảnh 001–010, ở L0 và L0,25). Benchmark chạy arena ở commit `4963d40`, tổ tiên của mã hiện tại, với cùng tệp vật, cùng cảnh và cùng tờ sắp xếp; khác biệt duy nhất là máy chạy (Windows, RTX 4060 Laptop) và tệp hiệu chuẩn camera.");
FIG(fig("fig_benchmark_dev.png"), 15, "ACT_I2 của đồ án (ACT_old s1000) so với các bài báo tái lập trên 40 lượt DEV chung của benchmark");
TABLE("ACT_old s1000 (đồ án) so với các phương pháp của benchmark, ghép cặp trên 40 lượt (McNemar chính xác hai phía, khác máy)", ["So sánh", "Thành công", "Chỉ ACT_old đạt", "Chỉ bên kia đạt", "p"], [
    ["ACT_old s1000 vs P19 ACT (port gốc)", "30/40 vs 20/40", "15", "5", "0,041"],
    ["ACT_old s1000 vs P17 ODIL", "30/40 vs 25/40", "11", "6", "0,33"],
    ["ACT_old s1000 vs CL0 (benchmark)", "30/40 vs 35/40", "1", "6", "0,125"],
    ["ACT_old s1000 vs ORACLE (benchmark)", "30/40 vs 40/40", "0", "10", "0,002"],
    ["ACT_J0 s1000 vs P19 ACT (chỉ dev_C0)", "19/20 vs 13/20", "7", "1", "0,070"],
], [38, 18, 15, 15, 14], { center: [1, 2, 3, 4], source: "`runs/e14_act_i2_dev`, `runs/e14_act_i2_dev2`, `runs/e11_act_dev`; `Benmark_Capstone/results/raw/*/trials.csv`." });
BL([
    "**ACT của đồ án hơn mọi bài báo tái lập** trên cùng 40 lượt (75% so với 30–62,5%), kể cả bản port ACT gốc (50%; p = 0,041)" + (P8.ok ? " (số DEV, khác máy; trên TEST với các bài báo dựng lại trên cùng máy thì không còn đúng với mọi bài, xem mục 4.10)" : "") + ". Hai bản ACT khác nhau ở biểu diễn hành động (I2 so với góc khớp tuyệt đối có temporal ensembling), ở bộ demo (444 tập E6 so với 480 lượt RGB-D tự ghi của benchmark, khoảng 380 thành công; chưa kiểm số tập thực dùng để huấn luyện) và bộ thực thi; chưa thử riêng từng yếu tố.",
    "**ACT vẫn thấp hơn CL0** trên lưới này (75% so với 87,5%), nhưng chênh chưa có ý nghĩa (1 so với 6 cặp, p = 0,125)" + (F.P7.ok ? "; chạy lại cùng máy (P7, bên dưới), hai bên ngang nhau." : "."),
    "**Cần đọc thận trọng:** hai bên chạy trên hai máy. Trên máy của đồ án, CL0 cũng đạt 35/40 trên 40 lượt này (`runs/e7_cl0_vs_ggcnn`) nhưng chỉ 30/40 lượt cho cùng kết quả với máy benchmark; chênh khoảng ±5 lượt có thể chỉ do khác máy. Mỗi ô chỉ có 10 lượt.",
    "**Không so trực tiếp với số trong bài báo gốc** (ví dụ ACT 86% trên tác vụ chuyển khối, DP 20,7% trung bình trên RoboTwin): khác tác vụ, khác robot, khác định nghĩa thành công; chính benchmark cũng ghi “không so được”.",
]);
P("Để so cả chín chính sách học và các phương pháp có W1 trên cùng máy, chuỗi P7 chạy lại toàn bộ trên 40 lượt này ngay sau TEST (`scripts/p7_bench_dev.sh`, so sánh bằng `scripts/p7_bench_compare.py`). " + (F.P7.ok ? `Chuỗi xong lúc ${F.P7.doneText}; Bảng 4.9 và hình ngay sau nó đọc tự động từ kết quả của chuỗi.` : "Bảng 4.9 sẽ được điền khi chuỗi xong.") + "");
TABLE("Mọi phương pháp của đồ án trên 40 lượt DEV của benchmark, chạy trên cùng máy (P7)" + (F.P7.ok ? "" : " — điền khi chuỗi P7 xong"), ["Phương pháp", "Thành công /40", "Wilson 95%", F.P7.ok ? "C0 L0 · C0 L0,25 · C2 L0 · C2 L0,25 (hàng nhiều hạt giống: cộng)" : "C0 L0 / C0 L0,25 / C2 L0 / C2 L0,25", "So với CL0_W (McNemar p)"], F.P7.tableRows() || [
    ["CL0 / CL0_W", "{{… / …}}", "{{…}}", "{{…}}", "{{…}}"],
    ["ORACLE / ORACLE_W", "{{… / …}}", "{{…}}", "{{…}}", "{{…}}"],
    ["ACT_old s1000 / s2000", "{{… / …}}", "{{…}}", "{{…}}", "{{…}}"],
    ["ACT_W s1000 / s2000 / s3000", "{{… / … / …}}", "{{…}}", "{{…}}", "{{…}}"],
    ["ACT_W_slow s1000", "{{…}}", "{{…}}", "{{…}}", "{{…}}"],
    ["DP_W s1000 / s2000 / s3000", "{{… / … / …}}", "{{…}}", "{{…}}", "{{…}}"],
    ["P05 / P07 / P17 / P19 (benchmark, khác máy)", "18 / 12 / 25 / 20", "", "", "{{…}}"],
], [26, 17, 17, 22, 18], { center: [1, 2, 3, 4], source: F.P7.src + (F.P7.ok ? "; McNemar chính xác hai phía, không hiệu chỉnh (Holm trong log)." : ".") });
if (F.P7.ok) {
    BL(F.P7.bullets());
    if (F.figIf("fig_p7_bench.png")) FIG(F.figIf("fig_p7_bench.png"), 15, "Mọi phương pháp trên 40 lượt DEV của benchmark: phương pháp của đồ án chạy cùng máy (P7), bài báo tái lập lấy từ máy benchmark");
}

if (P8.ok) {
    H2("4.10. Các bài báo dựng lại trên cùng máy, chạy trên TEST (P8)");
    P("Số của bốn bài báo ở Bảng 2.2, 4.8 và 4.9 có ba điểm yếu: chỉ có trên 40 lượt DEV ở băng đứng yên và 37,5 mm/s; chạy trên máy khác (Windows, mã `4963d40`); và ba bài chỉ là phần nhận thức gắn vào bộ thực thi CL0 còn lỗi W1. Vì mã adapter của benchmark không có trên máy này, đồ án **dựng lại** các bài báo (`ports/`): P05 CNS là phần so khớp cổ điển (SIFT, FLANN, tỉ số 0,75, RANSAC 5 px, theo mã CNS giấy phép MIT); P07 ViT-VS là phần so khớp đặc trưng DINOv2 ViT-S/14 lớp 11 kiểu best-buddy; P17 ODIL bước 1 là đăng ký đám mây điểm FPFH + FGR + ICP trên ảnh độ sâu lý tưởng. Cả ba tìm vật bằng ảnh mẫu (một vật nằm một mình trên băng, render từ sim, kèm điểm gắp tốt đã lưu của vật) rồi chuyển điểm gắp mẫu sang vật đang thấy; bộ bám, chọn vật và thực thi là của CL0, có hoặc không có W1. Tập ảnh mẫu chính chỉ gồm vật train và dev, nên vật TEST là vật lạ với mọi phương pháp. P19 dùng đúng công thức của benchmark (ACT mặc định của LeRobot + temporal ensembling 0,01) trên checkpoint ACT_J0, tức học từ cùng 444 demo E6 với ACT_old, ba hạt giống.");
    P("Trình tự giống P6: chạy DEV trước (cả 16 lần chạy đủ lượt, 0 lượt không hợp lệ; CL0_W chạy lại cho **cùng kết quả 20/20** với lần chạy ngày 15/11, nên mã mới không đổi môi trường), rồi khóa tiền đăng ký `PREREGISTRATION_P8.md` (luật quyết định, hash của mã, ảnh mẫu và checkpoint) trước lượt TEST đầu tiên. TEST dùng đúng tờ 60 cảnh của P6, ở L0,5 (chính) và L0,25 (phụ); CL0_W và ACT_W ở L0,5 lấy từ lần chạy P6 trên cùng tờ, cùng máy. 24 lần chạy × 60 lượt, 0 lượt không hợp lệ (xong 11:26 ngày 21/11/2026).");
    TABLE("Các bài báo dựng lại trên TEST (60 cảnh mỗi lần chạy; hàng ba hạt giống: cộng gộp, rồi từng hạt giống)", ["Phương pháp", "75 mm/s (L0,5)", "37,5 mm/s (L0,25)", "Ghi chú"], P8.rows(),
        [40, 20, 20, 20], { center: [1, 2], source: P8.src });
    TABLE("Quyết định theo tiền đăng ký P8 (L0,5): họ F1 = ACT_W so với từng bài (hoán vị dấu theo cảnh, Holm trên 4 phép); họ F2 = CL0_W so với từng bài nhận thức có W1 (McNemar chính xác, Holm trên 3 phép)",
        ["So sánh", "Chênh lệch", "p", "p Holm", "Kết luận"], [...P8.f1Rows(), ...P8.f2Rows()], [27, 37, 11, 11, 14], { center: [2, 3], source: P8.src });
    if (F.figIf("fig_p8_test.png")) FIG(F.figIf("fig_p8_test.png"), 14, "TEST, các bài báo dựng lại trên cùng máy so với CL0_W và ACT_W (bản có W1 cho các bài nhận thức; hạt giống cộng gộp)");
    BL([
        `**ACT của đồ án hơn hai bài, ngang hai bài.** ACT_W hơn P19 (ACT gốc) và P05 CNS; không thấy khác biệt với P07 ViT-VS và P17 ODIL khi hai bài này dùng chung bộ thực thi đã sửa. P07 + W1 còn cao hơn ACT_W về số (40/60 so với 54% gộp), nhưng chưa có ý nghĩa sau Holm. Câu “ACT mạnh hơn mọi bài báo tái lập” chỉ đúng với số DEV khác máy.`,
        `**Giao diện hành động quyết định với ACT.** P19 và ACT_old học từ cùng bộ demo E6, chỉ khác biểu diễn hành động (góc khớp + temporal ensembling so với I2 trong hệ băng); P19 chỉ đạt ${P8.rows()[2][1].split("\n")[0]} ở 75 mm/s, đúng như ACT mặc định ở E11.`,
        `**Mô-đun đã sửa vẫn đứng đầu.** CL0_W hơn cả ba bài nhận thức dùng chung bộ thực thi, nên phần chênh nằm ở khâu nhận thức. Một giải thích khả dĩ \`[chưa kiểm]\`: vật trong sim có màu đồng nhất, ít vân, hợp với cách tách nền của CL0 hơn so khớp đặc trưng (SIFT chỉ bắt được 0–20 điểm trên một vật).`,
        `**W1 giúp cả các bài báo ở băng nhanh** (L0,5, mô tả): P07 ${P8.w1("p07_vitvs")}, P17 ${P8.w1("p17_odil")}, P05 ${P8.w1("p05_cns")}. Số benchmark của ba bài này chạy trên bộ thực thi chưa sửa.`,
        `**Băng chậm thu hẹp khoảng cách nhưng không xóa nó.** Trên TEST ở 37,5 mm/s: ${P8.l025()}, so với ${P8.l05()} ở 75 mm/s. Trên lưới DEV (P7), hai bên ngang nhau: lưới đó dễ hơn (có cả băng đứng yên, cảnh DEV).`,
        `**Biết trước vật TEST** (nhãn riêng, có W1, L0,5, mô tả): P05 ${P8.testref("p05_cns")}, P17 ${P8.testref("p17_odil")}, P07 ${P8.testref("p07_vitvs")}; không bài nào vượt CL0_W kể cả khi có ảnh mẫu của chính vật lạ.`,
        `**Số của bài báo phụ thuộc mạnh vào cách hiện thực.** Trên cùng lưới DEV, bản dựng lại của P07 đạt 29/40 so với 12/40 của máy benchmark, P17 30/40 so với 25/40, P05 17/40 so với 18/40. Đây là bản dựng lại phần nhận thức của đồ án, không phải toàn bộ hệ thống gốc (vòng servo của CNS và ViT-VS, phần lặp lại và UKF của ODIL không được chạy, như ở benchmark).`,
    ]);
}

H2("4.11. Thảo luận");
H3("4.11.1. ACT làm tốt ở đâu");
BL([
    "**Chịu được băng nhanh khi có giao diện đúng.** Với I2, ACT học từ demo ở băng đứng yên và băng chậm vẫn gắp được ở 75 mm/s (13/20, gần ORACLE 16/20), trong khi ACT mặc định chỉ 4/20.",
    "**Không phụ thuộc nhận thức thủ công.** ACT không cần tách nền, không cần ngưỡng màu, nên không gặp các lỗi kiểu “vật dính nhau” hay “tương phản thấp” của CL0; ở ô 4–5 vật chạm nhau của G2 (test_C3, mô tả), ACT đạt 14/30 so với 9/30 của CL0.",
    "**Gần như không gặp lỗi cổ tay** của bộ thực thi (2/100 lượt DEV), vì quỹ đạo do mạng sinh ra không ép góc kẹp vào vùng gây lỗi như CL0.",
    "**Tổng quát hóa tổ hợp nhiệm vụ** (E18): một mô hình cho 40 nhiệm vụ, 72,5% trên nhiệm vụ chưa thấy.",
    ...(F.P7.ok && F.P7.slowVsMod() ? [P8.ok ? `**Gần mô-đun hơn khi băng chậm.** Trên lưới DEV (P7, 0 và 37,5 mm/s): ${F.P7.slowVsMod()}. Trên TEST ở 37,5 mm/s khoảng cách hẹp lại nhưng vẫn còn: ${P8.l025()}.` : `**Ngang mô-đun khi băng đứng yên hoặc chậm.** Trên lưới benchmark chạy cùng máy (P7, 0 và 37,5 mm/s): ${F.P7.slowVsMod()}.`] : []),
    "**Rẻ:** khoảng 2,3 giờ huấn luyện, 1,8 GB VRAM; " + (P8.ok ? "trên TEST hơn ACT gốc (P19) và P05 CNS, ngang P07 ViT-VS và P17 ODIL (mục 4.10)." : "mạnh hơn mọi bài báo tái lập trên lưới DEV của benchmark."),
]);
H3("4.11.2. Hạn chế của ACT trong bài toán này");
BL([
    "**Va chạm và đóng kẹp vào chỗ trống** là lỗi chủ yếu; có độ lệch ngang hệ thống khoảng −9 mm ở kế hoạch đầu.",
    "**Phương sai giữa các hạt giống và giữa các lần chạy lớn** (13–16/20 giữa hạt giống trên DEV" + (F.P6.ok ? `; trên TEST mới, ba hạt giống ACT_W đạt ${F.P6.seedsACTW()}` : "") + "; 3/20 lượt đổi kết quả khi chạy lại), nên cần nhiều lượt và nhiều hạt giống để kết luận.",
    (F.P7.ok && F.P7.slowVsMod() ? "**Không vượt được baseline mô-đun đã sửa ở băng nhanh.** Trên DEV ở L0,5, CL0_W (17/20) đứng trên mọi chính sách học (13–16/20)." : "**Không vượt được baseline mô-đun đã sửa.** Trên DEV ở L0,5, CL0_W (17/20) đứng trên mọi chính sách học (13–16/20); trên lưới benchmark, CL0 (87,5%) đứng trên ACT (75%).") + (F.P6.ok ? ` TEST mới xác nhận: ${F.P6.modVsAct()} (mô tả).` : "") + (F.P7.ok && F.P7.slowVsMod() ? (P8.ok ? ` Trên TEST ở 37,5 mm/s chênh còn khoảng 18 điểm (${P8.l025()}); trên lưới DEV (P7) hai bên ngang nhau. Băng nhanh làm khoảng cách rộng thêm, nhưng không phải nguyên nhân duy nhất.` : " Ở băng đứng yên và 37,5 mm/s (P7) hai bên ngang nhau, nên điểm yếu của ACT nằm ở việc bắt vật trên băng nhanh; lưới P7 khác TEST cả tốc độ lẫn tập cảnh, nên đây là mô tả.") : "") + FLAG_MOD + "",
    F.P6.ok ? `**Chất lượng demo quan trọng hơn tốc độ demo.** Trên DEV, thêm demo nhanh (E15) hay đổi sang chuyên gia đã sửa (ACT_W) đều không thấy khác. Trên TEST mới, ACT học từ chuyên gia đã sửa hơn ACT cũ ${F.P6.h2Text()} (H2), còn bỏ demo L0,5 không làm kém đi rõ (${F.P6.slowText()}, mô tả). H2 so hai bộ demo khác nhau cả chuyên gia lẫn số tập (677 so với 444), nên chưa tách được hai yếu tố này.` : "**Dữ liệu tốt hơn không giúp.** Thêm demo nhanh (E15) hay đổi sang chuyên gia đã sửa (ACT_W) đều không đổi kết quả trên DEV.",
]);
H3("4.11.3. Mối đe dọa đến tính đúng đắn");
BL([
    "**Mô phỏng:** vật lý kẹp, ma sát và render khác thực tế; mô phỏng lockstep bỏ qua độ trễ suy luận.",
    "**Chuyên gia có đặc quyền:** demo từ ORACLE sạch và nhất quán hơn demo người; trên robot thật, ghi demo bằng tay leader ở 75 mm/s khó hơn nhiều.",
    "**Cỡ mẫu:** ô DEV 20 lượt chỉ thấy được chênh lớn (≳ 30 điểm); các kết luận mạnh chỉ dựa trên TEST 60 lượt có tiền đăng ký.",
    P8.ok ? "**Bài báo là bản dựng lại:** P05, P07, P17 chỉ là phần nhận thức, do đồ án dựng lại theo bài báo, chạy trên bộ thực thi CL0; trên cùng lưới DEV, số của bản dựng lại khác máy benchmark tới 17/40 lượt (P07), nên số của một bài báo phụ thuộc nhiều vào cách hiện thực. P19 dùng checkpoint ACT_J0 của đồ án theo công thức của benchmark." : F.P7.ok ? "**So sánh với bài báo vẫn khác máy:** các phương pháp của đồ án đã chạy lại cùng máy (P7), nhưng các bản port bài báo vẫn chỉ có số từ máy benchmark." : "**So sánh khác máy** với benchmark (mục 4.9), sẽ được thay bằng P7 chạy cùng máy.",
]);

// ======================================================================= Chapter 5
H1("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN");
H2("5.1. Kết luận");
P("Đồ án đã chọn, cài đặt và đánh giá công bằng ACT cho bài toán gắp vật lạ từ băng chuyền với tay SO-101 và camera RGB cố định, trong mô phỏng. Trả lời các câu hỏi nghiên cứu:");
BL([
    "**CH1 (chọn phương pháp).** Trong 30 bài báo, chỉ 4 chạy được trọn lưới DEV trên nền tảng một tay; ACT là phương pháp học duy nhất được port nguyên vẹn và vừa ngân sách tính toán, nên được chọn làm trọng tâm, với Diffusion Policy là baseline học thứ hai và CL0 là baseline mô-đun.",
    "**CH2 (biểu diễn hành động).** Giao diện I2 (mục tiêu đầu kẹp tương đối trong hệ băng, bộ thực thi bù băng trôi) là điều chỉnh quyết định: ở 75 mm/s, 13/20 so với 4/20 của ACT mặc định (p = 0,022), dù demo không có tốc độ này. Thực hiện trọn chunk 100 khung (/100) tốt hơn hoặc bằng các chế độ lập kế hoạch lại dày hơn.",
    "**CH3 (so với mô-đun).** Ở TEST có tiền đăng ký của đồ án (G2), ACT_I2 (35%, 30%) không khác CL0 (37%); claim “hơn 15 điểm” bị bác bỏ. Phân tích sau đóng băng cho thấy CL0 khi đó bị lỗi cổ tay của bộ thực thi; sau khi sửa (W1), baseline mô-đun dẫn trước trên DEV. Kết quả TEST mới: " + (F.P6.ok ? F.P6.sentence() + "." : "{{điền sau 19/11}}.") + (F.P6.ok && F.P6.modularAhead() === false ? " {{cần xem lại: trên TEST mới ACT_W không thua CL0_W — viết lại các câu “ACT chưa vượt mô-đun”}}" : ""),
    "**CH4 (dữ liệu, DP, bài báo khác).** " + (F.P6.ok ? `Sửa lỗi của chuyên gia sinh demo **có** làm ACT tốt lên: trên TEST mới, ACT_W hơn ACT_old ${F.P6.h2Text()} (H2 được ủng hộ), dù trên DEV 20 cảnh không thấy khác; thêm demo L0,5 không giúp rõ. ACT và Diffusion Policy ngang nhau (${F.P6.actVsDp()}).` : "Chuyên gia tốt hơn và demo nhanh hơn không làm ACT tốt hơn trên DEV; ACT và Diffusion Policy ngang nhau (13–16/20).") + (P8.ok ? ` Với các bài báo dựng lại trên cùng máy và chạy trên TEST (P8, mục 4.10): ${P8.sentence()}. Trên lưới DEV (P7), ACT ngang CL0_W, nhưng trên TEST ở 37,5 mm/s CL0_W vẫn hơn (${P8.l025()}).` : F.P7.ok ? ` Trên lưới DEV của benchmark (băng đứng yên và 37,5 mm/s), chạy cùng máy (P7, Bảng 4.9), ACT của đồ án hơn mọi bài báo tái lập (30–62,5%), kể cả bản port ACT gốc (50%), và ${F.P7.slowVsMod()}; trên TEST thì DP_W ngang ACT_W (mô tả).` : " Trên lưới DEV của benchmark, ACT của đồ án (75%) hơn mọi bài báo tái lập (30–62,5%), kể cả bản port ACT gốc (50%). Bảng so cả chín chính sách trên cùng máy: {{điền sau 20/11}}."),
]);
P("**Phương pháp rút ra cho nền tảng giá rẻ.** Với một tay, một camera cố định và GPU 8 GB, chính sách học nên dùng là **ACT với giao diện hệ băng I2, thực hiện trọn chunk 100 khung, học từ demo của một chuyên gia" + (F.P6.ok ? " đã được sửa lỗi bộ thực thi" : "") + "** — " + (P8.ok ? "trên TEST, cấu hình này hơn ACT gốc (P19) và P05 CNS, ngang P07 ViT-VS và P17 ODIL đã dựng lại trên cùng máy." : "cấu hình này mạnh hơn mọi phương pháp đã công bố mà nhóm tái lập được trên cùng arena.") + " Tuy vậy, với một baseline mô-đun được sửa đúng bộ thực thi, ACT chưa vượt được pipeline mô-đun ở bài toán gắp đơn lẻ" + (P8.ok ? ": trên TEST, mô-đun hơn khoảng 18 điểm ở 37,5 mm/s và 32 điểm ở 75 mm/s, và cũng hơn mọi bài báo nhận thức khi dùng chung bộ thực thi" : F.P7.ok && F.P7.slowVsMod() ? ": hai bên ngang nhau khi băng đứng yên hoặc chậm (P7), còn ở 75 mm/s mô-đun hơn rõ" : "") + (F.P6.ok ? ` (TEST mới: ${F.P6.modVsAct()})` : "") + "; lợi thế của ACT nằm ở chỗ không cần nhận thức thủ công và mở rộng sang nhiều kỹ năng trong một mô hình (E18). Bài học phương pháp luận quan trọng nhất là: so sánh “học với mô-đun” chỉ có nghĩa khi bộ thực thi chung đã được kiểm lỗi, và chỉ nên kết luận trên TEST có tiền đăng ký" + (F.P6.ok ? " — DEV 20 cảnh từng bỏ sót một hiệu ứng mà TEST 60 cảnh thấy rõ (H2)" : "") + "." + FLAG_MOD + "");
H2("5.2. Hạn chế");
BL([
    "Toàn bộ kết quả là mô phỏng; chưa có số trên robot thật.",
    "Demo do chuyên gia có đặc quyền sinh ra, không phải người điều khiển.",
    "Phần lớn kết quả học dùng 1–3 hạt giống; E18 chỉ một hạt giống.",
    "W1 mới chỉ áp cho bộ thực thi của CL0/ORACLE, chưa áp cho bộ thực thi I2 của ACT/DP.",
    "Ở 150 mm/s mọi phương pháp thất bại vì tầm với và thời gian; bài toán ở tốc độ này chưa được giải.",
]);
H2("5.3. Hướng phát triển");
BL([
    "**Robot thật:** hiệu chuẩn tay và băng thật, ghi demo bằng tay leader, kiểm lại ACT_I2 và CL0_W trên phần cứng.",
    "**Bộ thực thi cho chính sách học:** áp W1 cho bộ thực thi I2, và thêm kiểm khả thi lúc chọn vật cho băng nhanh (W2).",
    "**Huấn luyện:** sửa độ lệch ngang bằng dữ liệu hoặc hàm mất mát, thử MIP [@mip] và chính sách nhỏ có lập kế hoạch lại nhanh; tăng số hạt giống.",
    P8.ok ? "**Bài báo:** dựng đủ vòng servo của CNS và ViT-VS, phần lặp lại của ODIL; so với mã adapter gốc của benchmark nếu chép được về máy này." : "**Benchmark:** chạy các bài báo tái lập trên cùng máy với đồ án (cần mã adapter và checkpoint từ máy benchmark).",
]);

// ======================================================================= references + appendices
H1("TÀI LIỆU THAM KHẢO", false, "");
L.getRefs().forEach((r, i) => push(new Paragraph({ spacing: { after: 80, line: 300, lineRule: "auto" }, indent: { left: 567, hanging: 567 }, alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 24 }), new TextRun({ text: r.text, font: FONT, size: 24 })] })));

H1("PHỤ LỤC A. ĐƯỜNG DẪN BẰNG CHỨNG VÀ MÃ BĂM", false, "A");
P("Mọi đường dẫn tính từ thư mục `arena/` của repo (nhánh `paper-dev`), trừ khi ghi khác. Kết quả trong mô phỏng ghi `engine=isaac`.", { noIndent: true });
TABLE("Bằng chứng cho các kết quả chính", ["Kết quả", "Bằng chứng"], [
    ["Thiết lập arena, E0–E16", "`ARENA_SETUP_REPORT.md`, `LABEL_RULES.md`"],
    ["E11 ACT_J0", "`runs/act_j0_s1000`, `runs/e11_act_dev`, `logs/2026-11-02_192528_act_j0_s1000.log`"],
    ["E14 ACT_I2", "`runs/act_i2_s1000`, `runs/e14_act_i2_dev`, `runs/e14_act_i2_dev2`, `runs/e14_replay_i2`"],
    ["E15/E16 biến thể", "`runs/e15_*`, `runs/e16_*`, `logs/2026-11-08_175431_e16_pair_final.txt`"],
    ["G2 (TEST đồ án)", "`PREREGISTRATION_G2.md`, `runs/g2_test_*`, `logs/2026-11-10_210822_g2_decision.txt`"],
    ["E18 (40 nhiệm vụ)", "`PREREGISTRATION_E18.md`, `logs/2026-11-12_204650_e18_decision.txt`"],
    ["W1 và DEV sau đóng băng", "`BAO_CAO_PAPER_DEV.md`, `PAPER_NOTES.md`, `arena/wrist_branch.py`, `runs/p1_*` … `runs/p5_*`"],
    ["TEST mới", "`PREREGISTRATION_PAPER.md` (lock_commit 248c7e8), `scripts/p6_test.sh`, `scripts/p6_decide.py`"],
    ["Benchmark 30 bài", "`../../Benmark_Capstone/reports/deadline/latest/`, `results/raw/*/trials.csv`; `scripts/p7_bench_compare.py`"],
    ["Hình trong báo cáo", "`bao_cao_do_an/make_figures.py` (đọc trực tiếp các `trials.csv` ở trên)"],
], [28, 72]);
TABLE("Mã băm SHA-256 đã khóa trong `PREREGISTRATION_PAPER.md` mục 7 (rút gọn 12 ký tự)", ["Thành phần", "SHA-256"], [
    ["Tờ TEST mới `locked/paper/test_C2.csv`", "29aa1c3beb50…"],
    ["Mã arena (`arena/**/*.py` + `configs/*`)", "0603069a3f22…"],
    ["Mã CL0 đóng băng", "006af1c96866…"],
    ["Checkpoint ACT_old s1000 / s2000", "f3f08c7798a3… / e23de118…"],
    ["Checkpoint ACT_W s1000 / s2000 / s3000", "abd7cb0a… / c07a917d… / 37d2e0d9…"],
    ["Checkpoint ACT_W_slow s1000", "97fec903…"],
    ["Checkpoint DP_W s1000 / s2000 / s3000", "737d09cc… / 88b47f6a… / 0ad63bf6…"],
], [55, 45]);

H1("PHỤ LỤC B. CÁCH CHẠY LẠI", false, "B");
BL([
    "**Huấn luyện ACT mặc định (E11):** `lerobot.scripts.lerobot_train --policy.type=act --steps=100000 --batch_size=8 --seed=1000` trên `runs/e6_demos_real/lerobot` (lệnh đầy đủ ở `ARENA_SETUP_REPORT.md`, mục E11).",
    "**Huấn luyện ACT_I2 / ACT_W:** `train_act_i2.py` với cùng đối số của `lerobot-train`, trên bộ dữ liệu I2 (`scripts/e14_act_i2.sh`, `scripts/p2p3_chain.sh`, `scripts/p3_seq_chain.sh`).",
    "**Huấn luyện DP_W:** `train_dp_i2.py` (`scripts/p4_dp_chain.sh`).",
    "**Đánh giá một chính sách học:** chạy máy chủ `remote_server.py --factory arena.methods.act_i2:make_method` rồi `python -m arena.run_arena --objects sim --methods REMOTE --method-arg remote=localhost:<cổng> --cells dev_C2 --speeds L0.5 --n 20`.",
    "**TEST mới và so sánh benchmark:** `scripts/p6_test.sh` (cần lệnh TEST), `scripts/p7_bench_dev.sh`; quyết định bằng `scripts/p6_decide.py test` và `scripts/p7_bench_compare.py`.",
    "**Dựng lại báo cáo này:** `python3 bao_cao_do_an/make_figures.py` rồi `node bao_cao_do_an/build_report.js` (cần gói npm `docx`).",
]);

// ======================================================================= document
const doc = new Document({
    creator: "arena", title: "Báo cáo đồ án: ACT cho gắp vật trên băng chuyền", features: { updateFields: true },
    styles: {
        default: { document: { run: { font: FONT, size: 26 }, paragraph: { spacing: { line: 360, lineRule: "auto" } } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true },
              paragraph: { spacing: { before: 240, after: 360 }, keepNext: true, outlineLevel: 0, alignment: AlignmentType.CENTER } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true },
              paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 1 } },
            { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 26, bold: true, italics: true },
              paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 2 } },
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
L.save(doc, path.join(F.OUT_DIR, "Bao_cao_do_an_ACT.docx"));
