import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"  # CHANGE if your backend runs elsewhere


def get_knowledge_summary():
    """Fetch live stats from backend. Falls back to defaults on failure."""
    documents_count = 0
    total_chunks = 0

    try:
        docs_resp = requests.get(f"{API_BASE_URL}/documents", timeout=3)
        if docs_resp.status_code == 200:
            documents_count = docs_resp.json().get("total", 0)
    except Exception:
        pass  # keep default 0

    try:
        count_resp = requests.get(f"{API_BASE_URL}/count", timeout=3)
        if count_resp.status_code == 200:
            total_chunks = count_resp.json().get("total_chunks", 0)
    except Exception:
        pass  # keep default 0

    return documents_count, total_chunks


def render_sidebar():

    with st.sidebar:
        st.markdown("""
        <div class="logo-section">
            <div class="logo-icon">🤖</div>
            <div class="logo-text">CosmicQuery</div>
        </div>
        """, unsafe_allow_html=True)

        # NEW CHAT button
        if st.button("+ New Chat", use_container_width=True, key="new_chat_btn"):
            st.session_state["page"] = "chat"
            st.rerun()

        # DOCUMENTS button
        if st.button("📄  Documents", use_container_width=True, key="docs_btn"):
            st.session_state["page"] = "documents"
            st.rerun()

        st.markdown("---")

        # NEW: fetch live values
        documents_count, total_chunks = get_knowledge_summary()

        st.markdown(f"""
        <div class="knowledge-card">
            <div class="card-title">KNOWLEDGE SUMMARY</div>
            <div class="stat-row">
                <span>📄 Documents</span>
                <span>{documents_count}</span>
            </div>
            <div class="stat-row">
                <span>🧩 Total Chunks</span>
                <span>{total_chunks:,}</span>
            </div>
            <div class="stat-row">
                <span>🗂️ Vector Store</span>
                <span>Qdrant</span>
            </div>
        </div>
        """, unsafe_allow_html=True)