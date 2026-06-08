# B├ío C├ío Nh├│m ΓÇö RAG Chatbot Ph├íp Luß║¡t Ma Tu├╜

## 1. Tß╗òng Quan Dß╗▒ ├ün

| Hß║íng mß╗Ñc | Nß╗Öi dung |
|----------|----------|
| **T├¬n dß╗▒ ├ín** | DrugLaw RAG Chatbot |
| **M├┤n / Ng├áy** | Day 08 ΓÇö RAG Pipeline v2 |
| **Sß║ún phß║⌐m nh├│m** | RAG Chatbot + Evaluation Pipeline (DeepEval) |
| **Phß║ím vi** | Chatbot trß║ú lß╗¥i c├óu hß╗Åi vß╗ü **ph├íp luß║¡t ma tu├╜ Viß╗çt Nam** (kh├┤ng d├╣ng corpus tin tß╗⌐c) |
| **Repository** | `GroupRAGPipline` ΓÇö branch `personal/Hieu` |
| **Th├ánh vi├¬n** | Nguyß╗àn Minh Hiß║┐u, Giang Th├ánh C├┤ng, Phß║ím V─ân C├┤ng |
| **Ng├áy cß║¡p nhß║¡t** | 08/06/2026 |

### Mß╗Ñc ti├¬u

X├óy dß╗▒ng chatbot RAG end-to-end: thu thß║¡p v─ân bß║ún ph├íp luß║¡t ΓåÆ chuß║⌐n h├│a Markdown ΓåÆ chunking/indexing ΓåÆ hybrid retrieval ΓåÆ generation c├│ citation ΓåÆ giao diß╗çn chat + ─æ├ính gi├í chß║Ñt l╞░ß╗úng bß║▒ng DeepEval.

---

## 2. Tiß║┐n ─Éß╗Ö Tß╗òng Thß╗â

| Hß║íng mß╗Ñc | Ghi ch├║ |
|----------|---------|
| Thu thß║¡p v─ân bß║ún ph├íp luß║¡t (Task 1) | 3 PDF trong `data/landing/legal/` |
| Convert Markdown (Task 3) | File `.md` trong `data/standardized/legal/` |
| Crawl tin tß╗⌐c (Task 2) | Bß╗Å qua ΓÇö nh├│m chß╗ë l├ám chatbot ph├íp luß║¡t |
| Chunking + Indexing (Task 4) | Vector store + BM25 |
| Semantic + Lexical Search (Task 5ΓÇô6) | Hybrid search |
| Reranking + PageIndex (Task 7ΓÇô8) | Rerank + vectorless fallback |
| Retrieval Pipeline (Task 9) | Pipeline ho├án chß╗ënh |
| Generation + Citation (Task 10) | Trß║ú lß╗¥i c├│ tr├¡ch dß║½n nguß╗ôn |
| Chatbot UI (`app.py`) | Streamlit / Chainlit |
| Golden dataset (ΓëÑ15 Q&A) | `evaluation/golden_dataset.json` |
| Evaluation pipeline | DeepEval |
| B├ío c├ío eval (`results.md`) | Bß║úng ─æiß╗âm + ph├ón t├¡ch A/B |

---

## 3. Kiß║┐n Tr├║c Hß╗ç Thß╗æng

```mermaid
flowchart LR
    subgraph Data["Data ΓÇö Nguyß╗àn Minh Hiß║┐u"]
        PDF["data/landing/legal/*.pdf"]
        MD["data/standardized/legal/*.md"]
        PDF -->|"Task 3: MarkItDown"| MD
    end

    subgraph Pipeline["RAG Pipeline ΓÇö Giang Th├ánh C├┤ng"]
        Chunk["Task 4: Chunking"]
        Index["Vector Store + BM25"]
        Retrieve["Task 9: Hybrid Retrieval"]
        Rerank["Task 7: Reranking"]
        Generate["Task 10: Generation + Citation"]
        MD --> Chunk --> Index --> Retrieve --> Rerank --> Generate
    end

    subgraph App["Giao diß╗çn ΓÇö Phß║ím V─ân C├┤ng"]
        UI["Streamlit / Chainlit Chatbot"]
        Eval["DeepEval Evaluation"]
        Generate --> UI
        Generate --> Eval
    end
```

**Luß╗ông xß╗¡ l├╜ c├óu hß╗Åi:**

```
User question ΓåÆ Embed query ΓåÆ Hybrid search (dense + BM25)
            ΓåÆ Rerank top-k ΓåÆ LLM generate answer + citations ΓåÆ Hiß╗ân thß╗ï UI
```

---

## 4. Dß╗» Liß╗çu (Corpus Ph├íp Luß║¡t)

### 4.1. File gß╗æc ΓÇö `data/landing/legal/`

| File | V─ân bß║ún | K├¡ch th╞░ß╗¢c |
|------|---------|------------|
| `luat-phong-chong-ma-tuy-2021.pdf` | Luß║¡t sß╗æ 73/2021/QH15 ΓÇö Luß║¡t Ph├▓ng, chß╗æng ma t├║y | ~525 KB |
| `bo-luat-hinh-su-2015.pdf` | Bß╗Ö luß║¡t H├¼nh sß╗▒ 2015 (sß╗¡a ─æß╗òi 2017) ΓÇö Ch╞░╞íng XX: Tß╗Öi phß║ím vß╗ü ma t├║y | ~2.6 MB |
| `quy-dinh-danh-muc-chat-ma-tuy-va-tien-chat.pdf` | Danh mß╗Ñc chß║Ñt ma tu├╜ v├á tiß╗ün chß║Ñt | ~1.6 MB |

**Nguß╗ôn tham khß║úo:** thuvienphapluat.vn, vanban.chinhphu.vn

### 4.2. File chuß║⌐n h├│a ΓÇö `data/standardized/legal/`

| File Markdown | Nguß╗ôn PDF | K├¡ch th╞░ß╗¢c |
|---------------|-----------|------------|
| `luat-phong-chong-ma-tuy-2021.md` | Luß║¡t PCMT 2021 | ~79 KB |
| `bo-luat-hinh-su-2015.md` | BLHS 2015 | ~834 KB |
| `quy-dinh-danh-muc-chat-ma-tuy-va-tien-chat.md` | Danh mß╗Ñc chß║Ñt MT | ~0.2 KB |

### 4.3. Chß╗º ─æß╗ü corpus hß╗ù trß╗ú

- H├¼nh phß║ít tß╗Öi phß║ím ma t├║y (─Éiß╗üu 249, 250, 251 BLHS)
- H├¼nh thß╗⌐c cai nghiß╗çn (Luß║¡t PCMT 2021, Ch╞░╞íng V)
- Quy ─æß╗ïnh chung vß╗ü ph├▓ng, chß╗æng ma t├║y
- Danh mß╗Ñc chß║Ñt ma tu├╜ nh├│m I, II, III

### 4.4. Chß║íy convert Markdown

```bash
cd Group
pip install markitdown
python src/task3_convert_markdown.py
```

---

## 5. Ph├ón C├┤ng C├┤ng Viß╗çc

| Th├ánh vi├¬n | MSSV | Nhiß╗çm vß╗Ñ | Task / Deliverable |
|-----------|------|----------|-------------------|
| **Nguyß╗àn Minh Hiß║┐u** | 705 | **B├ío c├ío nh├│m & dß╗» liß╗çu:** t├¼m/thu thß║¡p v─ân bß║ún ph├íp luß║¡t, convert Markdown, viß║┐t README nh├│m, chß║íy pytest kiß╗âm tra data, mß╗ƒ rß╗Öng golden dataset, viß║┐t `results.md` | 1, 3; `README.md`; `golden_dataset.json`; `results.md` |
| **Giang Th├ánh C├┤ng** | 544 | **Code pipeline:** implement to├án bß╗Ö task RAG ΓÇö chunking, indexing, semantic/lexical search, reranking, PageIndex, retrieval pipeline, generation + citation, script evaluation | 4ΓÇô10; `eval_pipeline.py` |
| **Phß║ím V─ân C├┤ng** | 753 | **Giao diß╗çn:** x├óy dß╗▒ng chatbot UI (Streamlit/Chainlit), t├¡ch hß╗úp pipeline, hiß╗ân thß╗ï citation & source documents, conversation memory | `app.py`; demo tr├¼nh b├áy |

### Phß╗æi hß╗úp giß╗»a c├íc th├ánh vi├¬n

```
Hiß║┐u (data + b├ío c├ío)  ΓåÆ  cung cß║Ñp .md trong data/standardized/
        Γåô
Giang (code task)      ΓåÆ  implement src/task4ΓÇôtask10, eval_pipeline.py
        Γåô
C├┤ng (giao diß╗çn)       ΓåÆ  gß╗ìi pipeline trong app.py, hiß╗ân thß╗ï kß║┐t quß║ú cho user
```

---

## 6. Sß║ún Phß║⌐m Nh├│m

### 6.1. RAG Chatbot (Y├¬u cß║ºu ch├¡nh)

- Giao diß╗çn chat: **Streamlit** (gß╗úi ├╜)
- Trß║ú lß╗¥i c├│ **citation** (Task 10)
- Hß╗ù trß╗ú **follow-up questions** (conversation memory)
- Hiß╗ân thß╗ï **source documents** ─æ├ú d├╣ng

```
Streamlit ΓåÆ Retrieval (Task 9) ΓåÆ Generation (Task 10) ΓåÆ Display
```

### 6.2. Evaluation Pipeline (DeepEval)

| Deliverable | ─É╞░ß╗¥ng dß║½n |
|-------------|-----------|
| Golden dataset (ΓëÑ15 Q&A) | `evaluation/golden_dataset.json` |
| Script evaluation | `evaluation/eval_pipeline.py` |
| B├ío c├ío kß║┐t quß║ú + A/B | `evaluation/results.md` |

**Metrics:** Faithfulness, Answer Relevance, Context Recall, Context Precision

**A/B so s├ính:** hybrid search vs dense-only, hoß║╖c c├│ reranking vs kh├┤ng reranking

---

## 7. H╞░ß╗¢ng Dß║½n Chß║íy

```bash
# 1. C├ái ─æß║╖t
cd Group
pip install -r requirements.txt
cp .env.example .env   # ─æiß╗ün OPENAI_API_KEY, WEAVIATE_URL, ...

# 2. Convert data
python src/task3_convert_markdown.py

# 3. Chß║íy chatbot
streamlit run app.py
# hoß║╖c
chainlit run app.py

# 4. Chß║íy evaluation
python group_project/evaluation/eval_pipeline.py
```

### Kiß╗âm tra data

```bash
pytest tests/test_individual.py::TestTask1 -v   # legal PDF
pytest tests/test_individual.py::TestTask3 -v   # markdown
```

---

## 8. Tham Khß║úo Y├¬u Cß║ºu B├ái Tß║¡p

Chi tiß║┐t ─æß║ºy ─æß╗º vß╗ü Task 1ΓÇô10, chß║Ñm ─æiß╗âm v├á code mß║½u evaluation: xem [`../README.md`](../README.md).

### Checklist nß╗Öp b├ái nh├│m

- [x] RAG Chatbot demo hoß║ít ─æß╗Öng ─æ╞░ß╗úc
- [x] T├¡ch hß╗úp pipeline c├íc th├ánh vi├¬n
- [x] README m├┤ tß║ú kiß║┐n tr├║c + ph├ón c├┤ng *(file n├áy)*
- [x] Golden dataset ΓëÑ15 Q&A
- [x] Evaluation chß║íy ─æ╞░ß╗úc vß╗¢i ΓëÑ4 metrics
- [x] So s├ính A/B ΓëÑ2 configs + ph├ón t├¡ch worst performers
- [x] Code push l├¬n repository chung

---

## L╞░u ├╜

Giß╗» lß║íi repo n├áy nß║┐u hß╗ìc track 3 giai ─æoß║ín 2 ΓÇö dß╗▒ ├ín sß║╜ ph├ít triß╗ân tiß║┐p l├¬n **knowledge graph** ─æß╗â xß╗¡ l├╜ c├íc c├óu hß╗Åi phß╗⌐c tß║íp h╞ín.
