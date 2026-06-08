"""
Streamlit Chat UI — RAG Chatbot về Pháp luật Ma tuý.

Chạy:
    cd Group
    streamlit run group_project/app.py

Yêu cầu:
    - Vector store đã được tạo (chạy task4 trước)
    - (Tuỳ chọn) OPENAI_API_KEY để dùng GPT-4o-mini thay vì fallback
"""

import os
import sys
from pathlib import Path

# Đảm bảo root project nằm trong sys.path
PROJECT_DIR = Path(__file__).parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(PROJECT_DIR / ".env")

# Import RAGChatbot
from group_project.chatbot import RAGChatbot

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Chatbot Pháp luật Ma tuý",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# STYLING
# =============================================================================

st.markdown("""
<style>
    /* Citation highlighting */
    .citation {
        background-color: #e8f4fd;
        color: #0366d6;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 500;
        white-space: nowrap;
    }
    /* Source card in sidebar */
    .source-card {
        background-color: #f6f8fa;
        border-left: 3px solid #0366d6;
        padding: 8px 12px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 0.85em;
    }
    /* Assistant message */
    .assistant-msg {
        background-color: #f0f7ff;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    /* User message */
    .user-msg {
        background-color: #e8f0fe;
        border-radius: 12px;
        padding: 10px 14px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INIT
# =============================================================================

def init_session():
    """Khởi tạo session state."""
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_key_set" not in st.session_state:
        st.session_state.api_key_set = False


def create_chatbot(api_key: str) -> RAGChatbot:
    """Tạo instance RAGChatbot với API key được cấu hình."""
    if api_key and api_key.strip() and api_key != "sk-xxx":
        os.environ["OPENAI_API_KEY"] = api_key.strip()
        st.session_state.api_key_set = True
    else:
        os.environ.pop("OPENAI_API_KEY", None)
        st.session_state.api_key_set = False

    chatbot = RAGChatbot()
    chatbot.api_key = api_key.strip() if api_key else ""
    # Fix: valid OpenAI key starts with "sk-"
    chatbot.use_llm = bool(chatbot.api_key and chatbot.api_key.startswith("sk-"))
    return chatbot


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Render sidebar với cấu hình và thông tin."""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/scales--v1.png", width=64)
        st.title("⚖️ RAG Chatbot")
        st.caption("Pháp luật Ma tuý & Tin tức")

        st.divider()

        # API Key
        st.subheader("🔑 Cấu hình API")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            placeholder="sk-...",
            help="Để trống để dùng chế độ fallback (không cần API)"
        )

        if st.button("🔄 Kết nối / Làm mới", use_container_width=True):
            st.session_state.chatbot = create_chatbot(api_key)
            if st.session_state.api_key_set:
                st.success("✅ Đã kết nối OpenAI GPT-4o-mini")
            else:
                st.info("ℹ️ Chế độ Fallback — trả lời dựa trên trích xuất tài liệu")

        # Auto-init chatbot on first load
        if st.session_state.chatbot is None:
            st.session_state.chatbot = create_chatbot(api_key)

        st.divider()

        # Status
        st.subheader("📊 Trạng thái")
        if st.session_state.api_key_set:
            st.success("LLM: GPT-4o-mini")
        else:
            st.warning("LLM: Fallback mode")

        # Check vector store
        vs_path = PROJECT_DIR / "data" / "vector_store.json"
        if vs_path.exists():
            import json
            try:
                with open(vs_path) as f:
                    chunks = json.load(f)
                st.success(f"Vector Store: {len(chunks)} chunks")
            except Exception:
                st.error("Vector Store: Lỗi đọc")
        else:
            st.error("Vector Store: Chưa có")

        # Conversation memory
        history_len = len(st.session_state.get("messages", []))
        st.metric("Lượt hội thoại", history_len // 2)

        st.divider()

        # Clear chat
        if st.button("🗑️ Xoá lịch sử chat", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.chatbot:
                st.session_state.chatbot.clear_history()
            st.rerun()

        st.divider()

        # About
        st.subheader("📖 Về Chatbot")
        st.markdown("""
        **Nguồn dữ liệu:**
        - Luật Phòng chống Ma tuý 2021
        - Bộ luật Hình sự 2015 (sửa đổi 2017)
        - Nghị định 105/2021/NĐ-CP
        - Tin tức về ma tuý

        **Pipeline:**
        1. Query Reformulation
        2. Hybrid Search (Dense + BM25)
        3. RRF Fusion + Reranking
        4. Generation + Citation
        """)

        st.caption("© 2026 — Group Project RAG Pipeline")


# =============================================================================
# MAIN CHAT AREA
# =============================================================================

def highlight_citations(text: str) -> str:
    """
    Tô màu các citation trong câu trả lời.
    Tìm pattern [source_name] và bọc trong span.
    """
    import re
    # Match [something] patterns — citations
    highlighted = re.sub(
        r'\[([^\]]+)\]',
        r'<span class="citation">[\1]</span>',
        text
    )
    return highlighted


def render_chat_message(role: str, content: str, sources: list[dict] | None = None):
    """Render một tin nhắn trong chat."""
    avatar = "🧑‍💻" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        if role == "assistant":
            # Highlight citations
            html_content = highlight_citations(content)
            # Replace newlines with <br> for HTML rendering
            html_content = html_content.replace("\n", "<br>")
            st.markdown(f'<div class="assistant-msg">{html_content}</div>', unsafe_allow_html=True)

            # Show sources in expander
            if sources:
                with st.expander(f"📚 Xem {len(sources)} tài liệu tham khảo", expanded=False):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", f"Source {i}")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>📄 [{source_name}]</strong>
                            <span style="color:#666"> — {doc_type} · score: {score:.3f}</span>
                            <br><small>{src['content'][:300]}{'...' if len(src.get('content', '')) > 300 else ''}</small>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="user-msg">{content}</div>', unsafe_allow_html=True)


def render_empty_state():
    """Hiển thị gợi ý câu hỏi khi chưa có tin nhắn nào."""
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <h2>⚖️ Chatbot Pháp luật Ma tuý</h2>
        <p style="color: #666; font-size: 1.1em;">
            Hỏi đáp về pháp luật ma tuý Việt Nam — có trích dẫn nguồn chính xác
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 Hình phạt tội tàng trữ ma tuý?", use_container_width=True):
            st.session_state.pending_query = "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam là gì?"
    with col2:
        if st.button("📋 Quy định về cai nghiện?", use_container_width=True):
            st.session_state.pending_query = "Luật Phòng chống ma tuý 2021 quy định như thế nào về các biện pháp cai nghiện?"
    with col3:
        if st.button("⚖️ Các tội danh về ma tuý?", use_container_width=True):
            st.session_state.pending_query = "Bộ luật Hình sự quy định những tội danh nào liên quan đến ma tuý?"

    # Process pending query
    if "pending_query" in st.session_state and st.session_state.pending_query:
        query = st.session_state.pending_query
        st.session_state.pending_query = None
        process_query(query)


def process_query(query: str):
    """Xử lý câu hỏi và hiển thị câu trả lời."""
    if not query.strip():
        return

    chatbot = st.session_state.chatbot
    if chatbot is None:
        st.error("Chatbot chưa được khởi tạo. Vui lòng nhập API Key ở sidebar.")
        return

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    # Get response
    with st.spinner("🔄 Đang tìm kiếm tài liệu và sinh câu trả lời..."):
        try:
            result = chatbot.chat(query)
        except Exception as e:
            st.error(f"Lỗi: {e}")
            result = {
                "answer": f"Đã xảy ra lỗi khi xử lý câu hỏi: {e}",
                "sources": [],
                "reformulated_query": query
            }

    # Add assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result.get("sources", [])
    })

    # Show reformulated query if different
    if result.get("reformulated_query") != query:
        st.caption(f"🔄 Truy vấn đã viết lại: *{result['reformulated_query']}*")


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    init_session()
    render_sidebar()

    # Chat container
    chat_container = st.container()

    with chat_container:
        # Render existing messages
        for msg in st.session_state.messages:
            render_chat_message(
                msg["role"],
                msg["content"],
                msg.get("sources")
            )

        # Show empty state if no messages
        if not st.session_state.messages:
            render_empty_state()

    # Chat input (always at bottom)
    st.divider()
    query = st.chat_input(
        "Đặt câu hỏi về pháp luật ma tuý...",
        key="chat_input"
    )

    if query:
        process_query(query)
        st.rerun()


if __name__ == "__main__":
    main()
