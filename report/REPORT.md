# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Đoan
**MSSV:** 2A202600795
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity (độ tương đồng cosine cao, gần bằng 1.0) nghĩa là hai vector biểu diễn văn bản có hướng rất gần nhau trong không gian vector đa chiều, chỉ ra rằng hai văn bản đó có sự tương đồng lớn về mặt ngữ nghĩa và nội dung.

**Ví dụ HIGH similarity:**
- Sentence A: "Lập trình Python rất dễ học đối với người mới bắt đầu."
- Sentence B: "Python là một ngôn ngữ lập trình thân thiện với người mới học."
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một ý chính là ngôn ngữ Python thích hợp và dễ tiếp cận cho người mới bắt đầu học lập trình, dù cấu trúc câu chữ có khác nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Lập trình Python rất dễ học đối với người mới bắt đầu."
- Sentence B: "Vũ trụ đang giãn nở với tốc độ ngày càng nhanh."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn độc lập và không liên quan gì đến nhau (một bên là công nghệ thông tin/ngôn ngữ lập trình, một bên là vật lý thiên văn).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings vì nó chỉ quan tâm đến hướng (chủ đề, ý nghĩa) của hai vector mà không bị ảnh hưởng bởi độ dài của văn bản (magnitude). Nếu dùng Euclidean distance, hai tài liệu có nội dung giống nhau nhưng một bên rất dài và một bên rất ngắn sẽ có khoảng cách rất lớn, dẫn đến việc đánh giá sai lệch.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> Sử dụng công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> Thay số: `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Nếu overlap tăng lên 100, số lượng chunk sẽ tăng lên: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks.
> Chúng ta muốn tăng overlap nhiều hơn để đảm bảo bảo toàn ngữ cảnh ở ranh giới giữa các chunk liền kề, giúp thông tin không bị đứt đoạn hay mất mát khi hệ thống truy xuất (retrieval) riêng lẻ từng chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Tin tức Khoa học & Công nghệ năm 2026.

**Tại sao nhóm chọn domain này?**
> Nhóm chọn tập tài liệu về tin tức công nghệ và sự kiện khoa học trong năm 2026. Đây là lĩnh vực chứa nhiều tên gọi kỹ thuật phức tạp, các số liệu định lượng (như dung lượng pin, số lượng tham số LLM) và các thực thể đặc thù (như NASA, Apple, Xiaomi, Microsoft). Sử dụng RAG sẽ giúp người dùng tra cứu nhanh thông tin chính xác từ các nguồn bài báo tin tức này.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | 07_iPhone 18 Pro lộ dung lượng pin.md | Tin tức công nghệ | 2315 | department: tech, lang: vi |
| 2 | 08_Tai nghe chụp tai đầu tiên của Xiaomi giá 2,09 triệu đồng.md | Tin tức thiết bị | 9069 | department: device, lang: vi |
| 3 | 11_Mô hình ngôn ngữ lớn tiếng Việt với 120 tỷ tham số.md | Tin tức AI | 4791 | department: ai, lang: vi |
| 4 | 13_Tàu quỹ đạo Sao Hỏa của NASA dừng hoạt động sau 11 năm.md | Tin tức khoa học vũ trụ | 3281 | department: space, lang: vi |
| 5 | 19_Microsoft ra tác nhân tự chủ tương tự OpenClaw.md | Tin tức phần mềm | 4414 | department: tech, lang: vi |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | space | Phân nhóm tài liệu theo lĩnh vực lớn như khoa học vũ trụ (space), công nghệ (tech), trí tuệ nhân tạo (ai). |
| lang | string | vi | Xác định ngôn ngữ của bài viết để phục vụ lọc ngôn ngữ hiển thị tương ứng của người dùng. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu `data/vi_retrieval_notes.md`:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| vi_retrieval_notes.md | FixedSizeChunker (`fixed_size`) | 11 | 197.0 | Trung bình (cắt cứng ký tự có thể ngắt câu giữa ý) |
| vi_retrieval_notes.md | SentenceChunker (`by_sentences`) | 5 | 331.6 | Tốt (cắt theo ranh giới câu, nhưng độ dài trung bình vượt quá 200) |
| vi_retrieval_notes.md | RecursiveChunker (`recursive`) | 12 | 137.0 | Rất tốt (chia nhỏ đệ quy theo đoạn văn và câu, giữ trọn ý nghĩa và đảm bảo giới hạn kích thước) |

### Strategy Của Tôi

**Loại:** RecursiveChunker (`recursive`)

**Mô tả cách hoạt động:**
> Chiến lược sử dụng đệ quy để tách văn bản dựa trên một danh sách các ký tự phân tách có độ ưu tiên giảm dần (mặc định là `\n\n` $\rightarrow$ `\n` $\rightarrow$ `. ` $\rightarrow$ ` ` $\rightarrow$ `""`). Hệ thống sẽ thử phân tách bằng ký tự đầu tiên, nếu phần nào vượt quá kích thước `chunk_size` quy định thì tiếp tục gọi đệ quy phân tách bằng các ký tự tiếp theo. Sau khi phân tách xong, các phần liền kề sẽ được ghép lại với nhau sao cho tiệm cận với kích thước giới hạn tối đa mà không bao giờ vượt quá nó.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tài liệu tin tức báo chí thường phân cấp rõ ràng theo các đoạn văn (`\n\n`) và câu hoàn chỉnh. `RecursiveChunker` giúp giữ nguyên các đoạn văn bản có mối liên kết chặt chẽ trong cùng một chunk để bảo toàn nội dung bài báo tốt nhất.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| vi_retrieval_notes.md | best baseline (by_sentences) | 5 | 331.6 | Tốt, nhưng kích thước chunk không ổn định |
| vi_retrieval_notes.md | **của tôi (recursive)** | 12 | 137.0 | Rất tốt, các đoạn cắt đều đặn, giữ nguyên ý và không bị vượt quá giới hạn ký tự |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | RecursiveChunker | 8 / 10 | Giữ ngữ cảnh đoạn tốt, kích thước đều đặn | Không cấu hình overlap đệ quy |
| Thành viên A | FixedSizeChunker | 6 / 10 | Đơn giản, số chunk ổn định | Dễ cắt đứt câu giữa chừng làm mất ý |
| Thành viên B | SentenceChunker | 7 / 10 | Bảo đảm câu trọn vẹn | Kích thước chunk không ổn định, dễ quá giới hạn |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Strategy `RecursiveChunker` là tốt nhất cho domain này vì bài báo tin tức có nhiều phân cấp. Việc chia đệ quy giúp giữ cấu trúc nguyên vẹn nhất có thể mà vẫn đảm bảo độ dài vector đồng đều.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex lookbehind `(?<=\. |\! |\? |\.\n)` để phát hiện ranh giới câu dựa trên các dấu chấm, chấm hỏi, chấm than có khoảng trắng đi kèm hoặc dấu chấm xuống dòng. Loại bỏ các câu trống và khoảng trắng thừa, sau đó gom các câu thành từng nhóm tối đa `max_sentences_per_chunk` câu.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy kiểm tra base case: nếu văn bản ngắn hơn `chunk_size` thì giữ nguyên. Nếu dài hơn, phân tách bằng separator đầu tiên. Chạy đệ quy xử lý các phần tử con vượt giới hạn bằng các separator còn lại. Cuối cùng, ghép các mảnh nhỏ lại với nhau một cách thông minh sao cho kích thước tiệm cận `chunk_size`.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Lưu trữ văn bản và vector tương ứng của nó. Hỗ trợ song song cả cơ chế in-memory (lưu trữ trong list `self._store`) lẫn ChromaDB Client thực tế. Khi tìm kiếm (`search`), thực hiện tính độ tương đồng cosine giữa vector câu hỏi và toàn bộ vector trong cơ sở dữ liệu bằng hàm `compute_similarity`, sắp xếp giảm dần theo điểm số để lấy ra `top_k` kết quả.

**`search_with_filter` + `delete_document`** — approach:
> Với `search_with_filter`, thực hiện lọc thô trước (pre-filtering) để chọn ra các chunk thỏa mãn hoàn toàn `metadata_filter` trước, sau đó mới tính độ tương đồng ngữ nghĩa. Với `delete_document`, tìm kiếm tất cả các bản ghi có `id` hoặc `metadata['doc_id']` khớp với mã tài liệu cần xóa để loại bỏ chúng khỏi danh sách lưu trữ.

### KnowledgeBaseAgent

**`answer`** — approach:
> Thực hiện tìm kiếm `top_k` đoạn ngữ cảnh liên quan nhất từ vector store, ghép nối chúng bằng dấu xuống dòng để làm context. Sau đó định dạng prompt theo cấu trúc truyền ngữ cảnh cho LLM rồi gọi hàm callback `llm_fn` để tổng hợp câu trả lời.

### Test Results

```
============================= 42 passed in 0.15s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Lập trình Python rất dễ học đối với người mới bắt đầu. | Python là một ngôn ngữ lập trình thân thiện với người mới học. | high | -0.0697 | Sai |
| 2 | Hôm nay trời mưa to và có giông bão. | Thời tiết hôm nay rất xấu, mưa lớn kéo dài. | high | -0.2346 | Sai |
| 3 | Tôi rất thích ăn phở bò Hà Nội. | Phở bò là một món ăn truyền thống nổi tiếng của Việt Nam. | high | -0.0148 | Sai |
| 4 | Lập trình Python rất dễ học đối với người mới bắt đầu. | Vũ trụ đang giãn nở với tốc độ ngày càng nhanh. | low | -0.1605 | Đúng |
| 5 | Quả táo này rất ngọt và giòn. | Điện thoại iPhone của hãng Apple có thiết kế đẹp. | low | 0.1053 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Điểm số thực tế của các cặp câu có ý nghĩa giống nhau (như Cặp 1 và Cặp 2) lại rất thấp và gần bằng 0 hoặc âm. Điều này cực kỳ bất ngờ nhưng lý do là vì hệ thống đang sử dụng `MockEmbedder` (chỉ sinh vector ngẫu nhiên dựa trên mã băm MD5 của chuỗi chữ). Nó chứng minh rằng các biểu diễn vector ngẫu nhiên hoặc các phương pháp băm không thể giữ lại ngữ nghĩa thực sự của văn bản, mà chúng ta cần sử dụng các mô hình học máy thực tế (như sentence-transformers) để chuyển đổi từ ngữ thành vector đặc trưng ngữ nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Trong bộ tài liệu, Microsoft đang phát triển hoặc công bố những sản phẩm AI nào và mục tiêu của chúng là gì? | Microsoft Scout - trợ lý giữ chân người dùng (bài 01); chip lượng tử mới 'với sự trợ giúp của AI' (bài 16); tác nhân tự chủ tương tự OpenClaw (bài 19). |
| 2 | Những tổ chức hoặc doanh nghiệp nào đang đầu tư mạnh vào AI, và họ tập trung vào những lĩnh vực hoặc ứng dụng nào? | Apple (App Store tích hợp AI - bài 06); Google X (AI thay lối làm cũ - bài 02); Microsoft (Scout, chip lượng tử, tác nhân tự chủ - bài 01/16/19); công ty châu Âu dùng AI mở rộng sang Mỹ (bài 20); Việt Nam phát triển LLM 120 tỷ tham số (bài 11). |
| 3 | Những dự án liên quan đến không gian vũ trụ trong tập tài liệu đang đối mặt với những cơ hội hoặc thách thức gì? | Blue Origin muốn phóng lại tên lửa trước cuối năm (bài 09); tàu quỹ đạo Sao Hỏa của NASA dừng hoạt động sau 11 năm (bài 13); tham vọng trung tâm dữ liệu vũ trụ của Musk khó thành (bài 15); rủi ro nước sạch khi SpaceX IPO (bài 18). |
| 4 | Những đột phá khoa học hoặc công nghệ mới nào được đề cập trong bộ tài liệu, và chúng có thể tạo ra những tác động gì trong tương lai? | Lần đầu chỉnh sửa chính xác gene phôi người (bài 05); chip lượng tử mới của Microsoft (bài 16); LLM tiếng Việt 120 tỷ tham số (bài 11); lắp đặt lò phản ứng hạt nhân bằng cần cẩu lớn nhất thế giới (bài 14). |
| 5 | Những bài viết nào cho thấy AI đang tác động đến cách con người học tập, làm việc hoặc vận hành tổ chức? Hãy tổng hợp các tác động chính. | Sinh viên hào hứng với AI nhưng bất định về tương lai (bài 17); Google X - không thể theo lối cũ khi AI làm tốt hơn (bài 02); ứng dụng mô hình 4 lớp trong chuyển đổi số cấp xã/phường (bài 10); AI giúp công ty châu Âu mở rộng sang Mỹ (bài 20). |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Trong bộ tài liệu, Microsoft đang phát triển... | 15_Tham vọng xây trung tâm dữ liệu... | 0.1390 | Không | [DEMO LLM] Generated answer from prompt preview: Context: "SpaceX đã dẫn đầu cuộc cách mạng... |
| 2 | Những tổ chức hoặc doanh nghiệp nào đang... | 12_Giá tiền ảo Pi lại 'sập' mạnh.md | 0.2002 | Không | [DEMO LLM] Generated answer from prompt preview: Context: Theo dữ liệu từ sàn tiền số Bitget... |
| 3 | Những dự án liên quan đến không gian vũ... | 18_Nước sạch có thể là rủi ro...SpaceX... | 0.0324 | Có | [DEMO LLM] Generated answer from prompt preview: Context: Theo TechCrunch, trong bản sửa đổi... |
| 4 | Những đột phá khoa học hoặc công nghệ mới... | 13_Tàu quỹ đạo Sao Hỏa của NASA... | 0.2639 | Không | [DEMO LLM] Generated answer from prompt preview: Context: Lần cuối cùng Mạng lưới Không gian Sâu... |
| 5 | Những bài viết nào cho thấy AI đang tác... | 01_Microsoft lộ 'kế hoạch khiến... | 0.1951 | Có | [DEMO LLM] Generated answer from prompt preview: Context: Theo tài liệu có tên ClawPilot... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 2 / 5 (Mặc dù sử dụng MockEmbedder với vector ngẫu nhiên, nhờ áp dụng Metadata Pre-filtering ở Query 3 giới hạn tập tìm kiếm chỉ trong các bài viết thuộc `category: space`, hệ thống đã lấy được chunk liên quan. Query 5 lấy được chunk về tài liệu Scout hỗ trợ văn phòng có độ tương ứng ngữ nghĩa phù hợp).

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được từ các thành viên khác cách cấu hình các tham số `chunk_size` và `overlap` linh hoạt tương ứng với cấu trúc của từng file tài liệu tiếng Việt để tăng khả năng truy xuất thông tin ngữ cảnh.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm bạn đã thử tích hợp model embedding thực tế `all-MiniLM-L6-v2` và đạt được độ chính xác truy xuất cao hơn hẳn, đồng thời sử dụng metadata filter cho thuộc tính `date` để lọc bỏ các tài liệu kỹ thuật đã lỗi thời.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ thiết kế metadata schema chi tiết hơn (như phân cấp danh mục sâu hơn, gắn nhãn độ ưu tiên) và chuyển hẳn sang sử dụng mô hình `LocalEmbedder` thực tế để điểm số tương đồng phản ánh đúng quan hệ ngữ nghĩa.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **100 / 100** |
