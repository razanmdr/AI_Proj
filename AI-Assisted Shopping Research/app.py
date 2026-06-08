import streamlit as st
import os
from data_loader import load_dataset, get_product_catalog
from assistant import chat

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopBot — AI Shopping Assistant",
    page_icon="🛍️",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.4rem;
        color: #1a1a2e;
        margin-bottom: 0;
    }

    .subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }

    .chat-user {
        background: #1a1a2e;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 0.75rem 1.1rem;
        margin: 0.4rem 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 0.93rem;
    }

    .chat-bot {
        background: #f3f4f6;
        color: #1a1a2e;
        border-radius: 18px 18px 18px 4px;
        padding: 0.75rem 1.1rem;
        margin: 0.4rem 0;
        max-width: 85%;
        font-size: 0.93rem;
    }

    .suggestion-btn {
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 0.4rem 0.9rem;
        font-size: 0.82rem;
        cursor: pointer;
        color: #374151;
    }

    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1.5px solid #e5e7eb;
        padding: 0.6rem 1rem;
        font-size: 0.93rem;
    }

    .stButton > button {
        border-radius: 12px;
        background: #1a1a2e;
        color: white;
        border: none;
        padding: 0.55rem 1.4rem;
        font-weight: 500;
    }

    .stButton > button:hover {
        background: #2d2d4e;
    }

    .product-chip {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        border-radius: 8px;
        padding: 2px 8px;
        font-size: 0.78rem;
        margin: 2px;
    }

    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "catalog" not in st.session_state:
    with st.spinner("Loading product catalog..."):
        df = load_dataset()
        st.session_state.catalog = get_product_catalog(df)
        st.session_state.product_count = len(st.session_state.catalog)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🛍️ ShopBot</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtitle">AI-powered shopping assistant · {st.session_state.product_count:,} products loaded</div>',
    unsafe_allow_html=True,
)

# ── API Key input (sidebar) ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Get your free key at aistudio.google.com",
    )
    st.markdown("---")
    st.markdown("### 💡 Try asking:")
    suggestions = [
        "What are your bestsellers?",
        "Show me gifts under £10",
        "I need something for the kitchen",
        "Cheap items under £3?",
        "Show me candles or lights",
    ]
    for s in suggestions:
        st.markdown(f"- *{s}*")
    st.markdown("---")
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

    # Dataset info
    st.markdown("### 📦 Dataset")
    st.caption("UCI Online Retail II · UK giftware & homeware")
    st.caption("Place `online_retail_II.xlsx` in `data/` folder for full dataset.")


# ── Chat display ───────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown(
            '<div class="chat-bot">👋 Hi! I\'m ShopBot, your AI shopping assistant. '
            'Ask me about products, gift ideas, or deals — I\'m here to help!</div>',
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bot">{msg["content"]}</div>', unsafe_allow_html=True)


# ── Input area ─────────────────────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "Message",
        placeholder="Ask me anything about our products...",
        label_visibility="collapsed",
        key="user_input",
    )

with col2:
    send = st.button("Send", use_container_width=True)

# ── Handle send ────────────────────────────────────────────────────────────────
if send and user_input.strip():
    if not api_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar.")
    else:
        # Add user message to display
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        with st.spinner("ShopBot is thinking..."):
            try:
                reply, updated_history = chat(
                    catalog=st.session_state.catalog,
                    user_message=user_input.strip(),
                    conversation_history=st.session_state.history,
                    api_key=api_key,
                )
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.history = updated_history
            except Exception as e:
                err_msg = str(e)
                if "api_key" in err_msg.lower() or "invalid" in err_msg.lower() or "permission" in err_msg.lower():
                    st.error("❌ Invalid API key. Please check your Gemini API key at aistudio.google.com")
                else:
                    st.error(f"❌ Error: {err_msg}")

        st.rerun()
