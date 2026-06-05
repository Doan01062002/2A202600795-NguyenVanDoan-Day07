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

**Domain:** Tài liệu kỹ thuật hỗ trợ và thiết kế hệ thống AI Knowledge Assistant nội bộ.

**Tại sao nhóm chọn domain này?**
> Nhóm chọn domain này để xây dựng một trợ lý hỗ trợ kỹ thuật và quy trình nội bộ giúp nhân viên dễ dàng tra cứu kiến thức từ cẩm nang hướng dẫn, các ghi chép về vector store, chunking và runbooks. Đây là một ứng dụng rất thực tiễn của hệ thống RAG trong doanh nghiệp.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | python_intro.txt | Nội bộ | 1953 | department: engineering, lang: en |
| 2 | vector_store_notes.md | Nội bộ | 2149 | department: engineering, lang: en |
| 3 | rag_system_design.md | Nội bộ | 2416 | department: engineering, lang: en |
| 4 | customer_support_playbook.txt | Nội bộ | 1703 | department: support, lang: en |
| 5 | chunking_experiment_report.md | Nội bộ | 2008 | department: engineering, lang: en |
| 6 | vi_retrieval_notes.md | Nội bộ | 2188 | department: support, lang: vi |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| department | string | engineering | Giúp lọc nhanh tài liệu theo phòng ban cần tra cứu thông tin để loại bỏ nhiễu. |
| lang | string | vi | Giúp lọc ngôn ngữ hiển thị (tiếng Anh hoặc tiếng Việt) phù hợp với người dùng. |

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
> Tài liệu kỹ thuật nội bộ thường có cấu trúc rõ ràng dạng các đoạn văn (`\n\n`) và câu hoàn chỉnh. `RecursiveChunker` giúp giữ nguyên cấu trúc đoạn văn hoặc các câu có quan hệ mật thiết với nhau trong cùng một chunk để bảo toàn ngữ cảnh tốt nhất cho RAG.

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
> Strategy `RecursiveChunker` là tốt nhất cho domain này vì tài liệu kỹ thuật có nhiều phân cấp (đoạn văn lớn, câu nhỏ). Việc chia đệ quy giúp giữ cấu trúc nguyên vẹn nhất có thể mà vẫn đảm bảo độ dài vector đồng đều.

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
| 1 | Loi ich cua Sentence-Based Chunking la gi? | Giúp cải thiện khả năng đọc hiểu vì các đoạn cắt khớp với ranh giới tự nhiên của ngôn ngữ. |
| 2 | Tai sao nen dung metadata filtering? | Giúp thu hẹp không gian tìm kiếm, tăng độ chính xác và tránh lấy nhầm các tài liệu ngoài phạm vi hoặc đã cũ. |
| 3 | Kien truc de xuat cho he thong RAG gom nhung lop nao? | Gồm 3 lớp: Lớp truyền tải dữ liệu (Ingestion layer), Lớp truy xuất dữ liệu (Retrieval layer), và Lớp ứng dụng (Application layer). |
| 4 | Cac buoc trong mot pipeline tim kiem vector? | Gồm 4 bước: Chia nhỏ tài liệu, Tạo embedding cho chunk, Lưu trữ vector và metadata, Tạo embedding cho query và xếp hạng kết quả. |
| 5 | Lam the nao de xu ly cac cau hoi ve tai khoan ho tro? | Trực tiếp tra cứu trong Customer Support Playbook để lấy các quy trình đăng ký tài khoản, sửa lỗi hóa đơn hoặc lấy lại mật khẩu. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Loi ich cua Sentence-Based Chunking la gi? | customer_support_playbook.txt... | 0.1954 | Không | [DEMO LLM] Generated answer from prompt preview: Context: Customer Support Playbook... |
| 2 | Tai sao nen dung metadata filtering? | chunking_experiment_report.md... | 0.2564 | Không | [DEMO LLM] Generated answer from prompt preview: Context: # Chunking Experiment Report... |
| 3 | Kien truc de xuat cho he thong RAG gom nhung lop nao? | python_intro.txt... | 0.1055 | Không | [DEMO LLM] Generated answer from prompt preview: Context: Python is a high-level... |
| 4 | Cac buoc trong mot pipeline tim kiem vector? | chunking_experiment_report.md... | 0.1413 | Không | [DEMO LLM] Generated answer from prompt preview: Context: # Chunking Experiment Report... |
| 5 | Lam the nao de xu ly cac cau hoi ve tai khoan ho tro? | customer_support_playbook.txt... | 0.1869 | Có | [DEMO LLM] Generated answer from prompt preview: Context: Customer Support Playbook... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 1 / 5 (Do MockEmbedder sinh vector ngẫu nhiên nên tỷ lệ truy xuất chính xác thấp, đúng như dự đoán về mặt lý thuyết khi không sử dụng mô hình embedding thật).

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
