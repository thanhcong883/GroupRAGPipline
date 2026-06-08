# Bài Tập Nhóm — Search Engine / RAG Chatbot

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: ✅ Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về pháp luật ma tuý và tin tức liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

### Code mẫu — DeepEval

```python
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
from deepeval.test_case import LLMTestCase

# Tạo test cases từ golden dataset
test_cases = []
for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    test_case = LLMTestCase(
        input=item["question"],
        actual_output=result["answer"],
        expected_output=item["expected_answer"],
        retrieval_context=[c["content"] for c in result["sources"]],
    )
    test_cases.append(test_case)

# Chạy evaluation
metrics = [
    FaithfulnessMetric(threshold=0.7),
    AnswerRelevancyMetric(threshold=0.7),
    ContextualRecallMetric(threshold=0.7),
    ContextualPrecisionMetric(threshold=0.7),
]

results = evaluate(test_cases, metrics)
```

### Code mẫu — RAGAS

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset

# Chuẩn bị data
eval_data = {
    "question": [],
    "answer": [],
    "contexts": [],
    "ground_truth": [],
}

for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    eval_data["question"].append(item["question"])
    eval_data["answer"].append(result["answer"])
    eval_data["contexts"].append([c["content"] for c in result["sources"]])
    eval_data["ground_truth"].append(item["expected_answer"])

dataset = Dataset.from_dict(eval_data)

# Chạy evaluation
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
)
print(result.to_pandas())
```

### Code mẫu — TruLens

```python
from trulens.apps.custom import TruCustomApp, instrument
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as TruOpenAI

provider = TruOpenAI()

# Define feedback functions
f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
f_relevance = Feedback(provider.relevance).on_input_output()
f_context_relevance = Feedback(provider.context_relevance).on_input()

# Wrap RAG pipeline
tru_rag = TruCustomApp(
    rag_pipeline,
    app_name="DrugLaw_RAG",
    feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
)

# Run evaluation
with tru_rag as recording:
    for item in golden_dataset:
        rag_pipeline.generate_with_citation(item["question"])

# View dashboard
from trulens.dashboard import run_dashboard
run_dashboard()
```

### Deliverable Evaluation

- [x] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [x] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [x] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [x] So sánh A/B ít nhất 2 configs

---

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

## Kiến Trúc Hệ Thống

### Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STREAMLIT CHAT UI                                 │
│                        (group_project/app.py)                               │
│                                                                             │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────────────────┐  │
│  │ Chat Input  │───▶│ Query Reformulate│───▶│    Retrieval Pipeline     │  │
│  │ (follow-up) │    │ (conversation    │    │       (Task 9)            │  │
│  │             │    │  memory)         │    │                           │  │
│  └─────────────┘    └──────────────────┘    │  ┌─────────────────────┐  │  │
│                                              │  │ Semantic Search     │  │  │
│                                              │  │ (Task 5, Dense)     │  │  │
│                                              │  ├─────────────────────┤  │  │
│                                              │  │ Lexical Search      │  │  │
│                                              │  │ (Task 6, BM25)      │  │  │
│                                              │  ├─────────────────────┤  │  │
│                                              │  │ RRF Merge + Rerank  │  │  │
│                                              │  │ (Task 7)            │  │  │
│                                              │  ├─────────────────────┤  │  │
│                                              │  │ PageIndex Fallback  │  │  │
│                                              │  │ (Task 8)            │  │  │
│                                              │  └─────────────────────┘  │  │
│                                              └───────────┬───────────────┘  │
│                                                          │                  │
│  ┌─────────────┐    ┌──────────────────┐                │                  │
│  │  Chat       │◀───│ Citation Display │◀───────────────┘                  │
│  │  Response   │    │ + Source Docs    │                                   │
│  └─────────────┘    └──────────────────┘                                   │
│                              │                                              │
│                              ▼                                              │
│                    ┌──────────────────┐                                    │
│                    │ Generation +     │                                    │
│                    │ Citation (Task10)│                                    │
│                    │ GPT-4o-mini /    │                                    │
│                    │ Fallback Rules   │                                    │
│                    └──────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Pipeline (đã hoàn thành ở bài cá nhân)

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Task 1 + 2      │     │  Task 3           │     │  Task 4           │
│  Data Collection │────▶│  Convert to       │────▶│  Chunking +       │
│  Legal PDFs      │     │  Markdown         │     │  Embedding +      │
│  News Crawling   │     │  (MarkItDown)     │     │  Vector Store     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  vector_store.json│
                                                  │  (28 chunks,      │
                                                  │   384-dim)        │
                                                  └──────────────────┘
```

### Luồng xử lý một câu hỏi

```
User Query (có thể là follow-up)
    │
    ▼
┌──────────────────────┐
│ Query Reformulation  │  ← Sử dụng conversation history
│ (GPT-4o-mini hoặc    │    để viết lại thành standalone query
│  keyword fallback)   │
└──────────┬───────────┘
           │ standalone_query
           ▼
┌──────────────────────┐
│ Hybrid Retrieval     │  ← Dense (cosine similarity) + Sparse (BM25)
│ (Task 9)             │    → RRF fusion → Cross-encoder rerank
│                      │    → PageIndex fallback nếu score < threshold
└──────────┬───────────┘
           │ top_k chunks
           ▼
┌──────────────────────┐
│ Reorder + Format     │  ← "Lost in the middle" avoidance
│ (Task 10)            │    Format context với source labels
└──────────┬───────────┘
           │ formatted context
           ▼
┌──────────────────────┐
│ Generation           │  ← GPT-4o-mini (nếu có API key)
│ (Task 10)            │    hoặc rule-based fallback
│                      │    → Answer có citation [source_name]
└──────────┬───────────┘
           │ answer + sources
           ▼
┌──────────────────────┐
│ Streamlit Display    │  ← Highlight citations
│                      │    Hiển thị source documents
│                      │    Cập nhật conversation memory
└──────────────────────┘
```

---

## Cấu Trúc Thư Mục

```
Group/
├── src/                              # Bài cá nhân (các task 1-10)
│   ├── task1_collect_legal_docs.py   # Thu thập văn bản pháp luật PDF/DOCX
│   ├── task2_crawl_news.py           # Crawl tin tức về ma tuý
│   ├── task3_convert_markdown.py     # Chuyển đổi → Markdown
│   ├── task4_chunking_indexing.py    # Chunk + Embed + Vector Store
│   ├── task5_semantic_search.py      # Dense Retrieval (cosine similarity)
│   ├── task6_lexical_search.py       # Sparse Retrieval (BM25)
│   ├── task7_reranking.py            # RRF + Cross-encoder + MMR
│   ├── task8_pageindex_vectorless.py # PageIndex fallback
│   ├── task9_retrieval_pipeline.py   # Pipeline hợp nhất
│   └── task10_generation.py          # Generation có citation
│
├── data/
│   ├── landing/                      # Dữ liệu gốc (PDF, DOCX, JSON)
│   │   ├── legal/                    # Văn bản pháp luật
│   │   └── news/                     # Tin tức crawl
│   ├── standardized/                 # Đã convert sang Markdown
│   │   ├── legal/
│   │   └── news/
│   └── vector_store.json             # Vector store (JSON, 28 chunks)
│
├── group_project/                    # Sản phẩm nhóm
│   ├── README.md                     # File này
│   ├── app.py                        # Streamlit Chat UI
│   ├── chatbot.py                    # RAGChatbot class (backend)
│   └── evaluation/                   # Evaluation pipeline
│       ├── golden_dataset.json       # 15+ cặp Q&A
│       ├── eval_pipeline.py          # Script evaluation
│       └── results.md                # Báo cáo kết quả
│
├── tests/
│   └── test_individual.py            # Unit tests
│
├── requirements.txt
├── .env.example
└── README.md                         # README gốc của project
```

---

## Phân Công Công Việc

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| ... | ... | Task 1+2: Thu thập dữ liệu (legal PDFs + crawl news) | ✅ |
| ... | ... | Task 3+4: Convert Markdown + Chunking & Embedding | ✅ |
| ... | ... | Task 5+6: Semantic Search + Lexical Search (BM25) | ✅ |
| ... | ... | Task 7+8: Reranking (RRF/Cross-encoder/MMR) + PageIndex Fallback | ✅ |
| ... | ... | Task 9+10: Retrieval Pipeline + Generation có Citation | ✅ |
| ... | ... | Group: Tích hợp pipeline → Chatbot backend (chatbot.py) | ✅ |
| ... | ... | Group: Streamlit UI (app.py) + README kiến trúc | ✅ |
| ... | ... | Group: Evaluation Pipeline + Golden Dataset + Báo cáo | ✅ |

---

## Hướng Dẫn Chạy

### 1. Cài đặt dependencies

```bash
cd Group
pip install -r requirements.txt
```

### 2. (Tuỳ chọn) Cấu hình API Key

```bash
cp .env.example .env
# Sửa OPENAI_API_KEY=sk-... trong .env
```

Nếu không có API Key, chatbot vẫn hoạt động ở chế độ fallback (trả lời dựa trên trích xuất tài liệu).

### 3. Chạy Streamlit App

```bash
cd Group
streamlit run group_project/app.py
```

Sau đó mở trình duyệt tại **http://localhost:8501**.

### 4. Chạy Evaluation

```bash
cd Group
python group_project/evaluation/eval_pipeline.py
```

---

## Tính Năng Đã Hoàn Thành

| Tính năng | Mô tả | Trạng thái |
|-----------|-------|------------|
| 🔍 Hybrid Search | Dense (cosine similarity) + Sparse (BM25) + RRF fusion | ✅ |
| 🎯 Reranking | Cross-encoder (Jina API) hoặc local fallback | ✅ |
| 📄 Citation | Mỗi câu trả lời đều có citation [source_name] | ✅ |
| 💬 Conversation Memory | Hỗ trợ follow-up questions, query reformulation | ✅ |
| 🖥️ Chat UI | Streamlit interface với citation highlight + source docs | ✅ |
| 📊 Evaluation | Golden dataset 15+ câu, 4 metrics, A/B comparison | ✅ |
| 🔄 Fallback | PageIndex khi hybrid score thấp, rule-based khi không có API | ✅ |

---

## Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` (384 dim) |
| Chunking | `RecursiveCharacterTextSplitter` (500 chars, 50 overlap) |
| Dense Search | Cosine similarity trên vector embeddings |
| Sparse Search | BM25 (`rank-bm25`) |
| Fusion | Reciprocal Rank Fusion (k=60) |
| Reranking | Jina Reranker v2 (multilingual) / Local embedding fallback |
| Generation | GPT-4o-mini (OpenAI) / Rule-based fallback |
| UI | Streamlit 1.35+ |
| Evaluation | DeepEval |

---

## Lưu ý: Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.
