import streamlit as st
import os
import tempfile
from document_loader import load_document, get_file_summary
from vector_store import add_documents, get_stored_sources, clear_store, document_count
from rag_assistant import rag_chat, generate_document_summary

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinanceBot — RAG Financial Analyst",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    .main-title {
        font-family: 'IBM Plex Serif', serif;
        font-size: 2rem;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .subtitle { color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem; }

    .chat-user {
        background: #0f172a;
        color: white;
        border-radius: 16px 16px 4px 16px;
        padding: 0.75rem 1.1rem;
        margin: 0.4rem 0;
        max-width: 78%;
        margin-left: auto;
        font-size: 0.9rem;
    }
    .chat-bot {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #0f172a;
        border-radius: 16px 16px 16px 4px;
        padding: 0.75rem 1.1rem;
        margin: 0.4rem 0;
        max-width: 85%;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .source-badge {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        margin: 2px;
        border: 1px solid #bfdbfe;
    }
    .stat-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        text-align: center;
    }
    .stat-number { font-size: 1.4rem; font-weight: 600; color: #0f172a; }
    .stat-label { font-size: 0.75rem; color: #64748b; }

    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.87rem;
    }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# ── Layout ─────────────────────────────────────────────────────────────────────
col_main, col_side = st.columns([3, 1])

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Free at aistudio.google.com",
    )
    st.markdown("---")

    # ── Upload section
    st.markdown("### 📂 Upload Documents")
    uploaded_files = st.file_uploader(
        "PDF, CSV, or Excel",
        type=["pdf", "csv", "xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files and api_key:
        if st.button("⚡ Process & Index", use_container_width=True):
            total_added = 0
            with st.spinner("Parsing and embedding documents..."):
                for uploaded_file in uploaded_files:
                    try:
                        # Save to temp file
                        suffix = "." + uploaded_file.name.split(".")[-1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name

                        # Parse into chunks
                        chunks = load_document(tmp_path, uploaded_file.name)
                        os.unlink(tmp_path)

                        # Add to vector store
                        added = add_documents(chunks, api_key)
                        total_added += added
                        st.success(f"✅ {uploaded_file.name}: {added} chunks indexed")

                    except Exception as e:
                        st.error(f"❌ {uploaded_file.name}: {e}")

            if total_added > 0:
                st.info(f"Total {total_added} new chunks added to vector store.")
                st.rerun()

    elif uploaded_files and not api_key:
        st.warning("Enter your API key first.")

    st.markdown("---")

    # ── Vector store stats
    st.markdown("### 🗄️ Vector Store")
    doc_count = document_count()
    sources = get_stored_sources()

    st.markdown(f'<div class="stat-box"><div class="stat-number">{doc_count}</div><div class="stat-label">chunks indexed</div></div>', unsafe_allow_html=True)
    st.markdown("")

    if sources:
        st.markdown("**Indexed files:**")
        for s in sources:
            st.markdown(f"- `{s}`")
    else:
        st.caption("No documents indexed yet.")

    st.markdown("")
    if st.button("🗑️ Clear vector store", use_container_width=True):
        clear_store()
        st.success("Vector store cleared.")
        st.rerun()

    st.markdown("---")
    if st.button("💬 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.last_sources = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Example questions")
    examples = [
        "What was the total revenue last year?",
        "Summarize the key financial highlights",
        "What are the main risk factors mentioned?",
        "Compare revenue across quarters",
        "What is the net profit margin?",
    ]
    for e in examples:
        st.caption(f"_{e}_")


# ══════════════════════════════════════════════════════════════════════
# MAIN PANEL
# ══════════════════════════════════════════════════════════════════════
with col_main:
    st.markdown('<div class="main-title">📊 FinanceBot</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtitle">RAG-powered financial document analyst · {doc_count} chunks in store</div>',
        unsafe_allow_html=True,
    )

    # ── Chat messages
    if not st.session_state.messages:
        if doc_count == 0:
            st.info("👈 Upload a financial document (PDF, CSV, or Excel) in the sidebar to get started.")
        else:
            st.markdown(
                f'<div class="chat-bot">👋 Hello! I\'ve indexed <strong>{doc_count} chunks</strong> from your documents. '
                f'Ask me anything about the financial data — revenues, margins, risks, trends, etc.</div>',
                unsafe_allow_html=True,
            )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bot">{msg["content"]}</div>', unsafe_allow_html=True)

    # ── Source references for last answer
    if st.session_state.last_sources:
        with st.expander("📎 Source chunks used for last answer", expanded=False):
            for chunk in st.session_state.last_sources:
                label = chunk["source"]
                if chunk["page"] != "N/A":
                    label += f" · page {chunk['page']}"
                label += f" · relevance {chunk['score']}"
                st.markdown(f'<span class="source-badge">{label}</span>', unsafe_allow_html=True)
                st.caption(chunk["text"][:300] + "...")
                st.markdown("---")

    # ── Input
    st.markdown("---")
    input_col, btn_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            "Ask",
            placeholder="Ask about the financial documents...",
            label_visibility="collapsed",
            key="user_input",
        )
    with btn_col:
        send = st.button("Send", use_container_width=True)

    if send and user_input.strip():
        if not api_key:
            st.error("⚠️ Please enter your Gemini API key in the sidebar.")
        elif doc_count == 0:
            st.error("⚠️ No documents indexed yet. Upload files in the sidebar first.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input.strip()})
            with st.spinner("Retrieving context and generating answer..."):
                try:
                    answer, updated_history, retrieved = rag_chat(
                        query=user_input.strip(),
                        conversation_history=st.session_state.history,
                        api_key=api_key,
                    )
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.history = updated_history
                    st.session_state.last_sources = retrieved
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════
# RIGHT PANEL — document insights
# ══════════════════════════════════════════════════════════════════════
with col_side:
    st.markdown("### 🔍 Indexed Sources")
    if sources:
        for src in sources:
            ext = src.split(".")[-1].upper()
            color = "#dcfce7" if ext == "PDF" else "#fef9c3"
            st.markdown(
                f'<div style="background:{color};border-radius:8px;padding:6px 10px;'
                f'margin:4px 0;font-size:0.82rem;"><strong>{ext}</strong> {src}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No files indexed yet.")

    st.markdown("---")
    st.markdown("### 🏗️ How RAG Works")
    steps = [
        ("1️⃣", "Upload", "PDF/CSV parsed into text chunks"),
        ("2️⃣", "Embed", "Google embeds chunks → ChromaDB"),
        ("3️⃣", "Query", "Your question is embedded too"),
        ("4️⃣", "Retrieve", "Top-k similar chunks found"),
        ("5️⃣", "Generate", "Gemini answers using context"),
    ]
    for icon, title, desc in steps:
        st.markdown(f"**{icon} {title}**")
        st.caption(desc)
