import os
import json
from pathlib import Path

# Thêm root path của project vào sys.path để import các module src
import sys
PROJECT_DIR = Path(__file__).parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

try:
    from src.task9_retrieval_pipeline import retrieve
    from src.task10_generation import reorder_for_llm, format_context, generate_fallback_answer
except ImportError:
    # Fallback dự phòng trong trường hợp path chưa cập nhật chính xác
    from Group.src.task9_retrieval_pipeline import retrieve
    from Group.src.task10_generation import reorder_for_llm, format_context, generate_fallback_answer

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

CHAT_SYSTEM_PROMPT = """Answer the user's question comprehensively in Vietnamese using only the provided context.
For every statement of fact or claim, immediately insert a bracketed citation linking to the specific source document (e.g. [luat-phong-chong-ma-tuy-2021] or [article_01]).

If the information is not explicitly stated in the provided context, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than guessing.

Rules:
- Only use information from the provided context
- Every factual claim MUST have a citation
- If context is insufficient, say so clearly
- Structure your answer with clear paragraphs"""

REFORMULATE_SYSTEM_PROMPT = """Given a conversation history and a follow-up question, rewrite the follow-up question to be a standalone, self-contained question in Vietnamese that includes all necessary context from the conversation history.
Do NOT answer the question. Only output the reformulated question and nothing else.
If the follow-up question is already self-contained or does not relate to the history, output the original follow-up question exactly as is."""


class RAGChatbot:
    def __init__(self):
        self.history: list[dict] = []
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.use_llm = bool(self.api_key and self.api_key.startswith("sk-"))

    def clear_history(self):
        """Xóa sạch lịch sử hội thoại (memory)."""
        self.history = []
        print("✓ Đã xóa lịch sử hội thoại.")

    def _get_openai_client(self):
        if self.use_llm:
            from openai import OpenAI
            return OpenAI(api_key=self.api_key)
        return None

    def reformulate_query(self, query: str) -> str:
        """
        Sử dụng LLM để viết lại câu hỏi tiếp nối (follow-up question)
        thành câu hỏi độc lập dựa trên ngữ cảnh lịch sử hội thoại.
        """
        if not self.history:
            return query

        if not self.use_llm:
            # Fallback thủ công nếu không có API Key
            print("⚠ (Fallback) Đang ghép từ khóa thủ công cho truy vấn tiếp nối...")
            last_user_query = ""
            for msg in reversed(self.history):
                if msg["role"] == "user":
                    last_user_query = msg["content"]
                    break
            # Trích xuất một số từ khóa chính để bổ trợ cho truy vấn
            keywords = last_user_query.lower().replace("?", "").split()
            important_keywords = [w for w in keywords if len(w) > 3 and w not in ("như", "thế", "nào", "làm", "sao", "bao", "nhiêu")]
            keyword_context = " ".join(important_keywords[:3])
            return f"{query} {keyword_context}".strip()

        client = self._get_openai_client()
        try:
            # Xây dựng lịch sử hội thoại dạng text để gửi LLM
            history_text = ""
            for msg in self.history:
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role_label}: {msg['content']}\n"
            
            user_prompt = f"Lịch sử hội thoại:\n{history_text}\nCâu hỏi tiếp nối: {query}"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": REFORMULATE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
            )
            reformulated = response.choices[0].message.content.strip()
            print(f"  → Standalone Query: {reformulated}")
            return reformulated
        except Exception as e:
            print(f"Error reformulating query with LLM: {e}. Falling back to original query.")
            return query

    def chat(self, query: str) -> dict:
        """
        Xử lý lượt chat hiện tại của người dùng.
        
        Args:
            query: Câu hỏi của người dùng (có thể là câu hỏi tiếp nối)
            
        Returns:
            {
                'answer': str,                  # Câu trả lời có citation
                'sources': list[dict],          # Các chunks tài liệu đã dùng làm căn cứ
                'reformulated_query': str       # Câu hỏi độc lập sau khi viết lại
            }
        """
        # Bước 1: Viết lại câu hỏi nếu có lịch sử
        standalone_query = self.reformulate_query(query)

        # Bước 2: Truy xuất tài liệu liên quan bằng pipeline Task 9
        chunks = retrieve(standalone_query, top_k=5)

        # Bước 3: Sắp xếp tài liệu tránh "lost in the middle"
        reordered_chunks = reorder_for_llm(chunks)

        # Bước 4: Định dạng tài liệu thành context string
        context = format_context(reordered_chunks)

        # Bước 5: Sinh câu trả lời (LLM hoặc Fallback)
        if self.use_llm:
            client = self._get_openai_client()
            try:
                # Xây dựng prompt chứa context và câu hỏi độc lập
                user_message = f"Context:\n{context}\n\n---\n\nQuestion: {standalone_query}"
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3,
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error generating answer with OpenAI: {e}. Using rule-based fallback.")
                answer = generate_fallback_answer(standalone_query, reordered_chunks)
        else:
            answer = generate_fallback_answer(standalone_query, reordered_chunks)

        # Bước 6: Cập nhật lịch sử hội thoại
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": answer})

        return {
            "answer": answer,
            "sources": chunks,
            "reformulated_query": standalone_query
        }
