import streamlit as st
import html


def render_retrieved_chunks(sources=None):

    if not sources:
        return

    chips = ""
    for i, s in enumerate(sources):
        rank = i + 1
        text_preview = html.escape(s.get("text", "")[:200])
        file_name = html.escape(s.get("file", ""))
        page = s.get("page", "")
        chips += f'<div class="chunk-card"><div class="chunk-score high">{rank}</div><div class="chunk-content"><div class="chunk-title">{file_name}<span class="chunk-page">· Page {page}</span></div><div class="chunk-text">{text_preview}...</div></div></div>'

    st.markdown(f'<div class="chunks-section"><div class="chunks-heading">RETRIEVED CHUNKS</div>{chips}</div>', unsafe_allow_html=True)

    # NEW: functional "View All Chunks" toggle
    show_key = f"show_all_chunks_{id(sources)}"
    if show_key not in st.session_state:
        st.session_state[show_key] = False

    if st.button("View All Chunks ↗", key=f"btn_{show_key}"):
        st.session_state[show_key] = not st.session_state[show_key]

    if st.session_state[show_key]:
        full_chips = ""
        for i, s in enumerate(sources):
            rank = i + 1
            full_text = html.escape(s.get("text", ""))
            file_name = html.escape(s.get("file", ""))
            page = s.get("page", "")
            full_chips += f'<div class="chunk-card"><div class="chunk-score high">{rank}</div><div class="chunk-content"><div class="chunk-title">{file_name}<span class="chunk-page">· Page {page}</span></div><div class="chunk-text">{full_text}</div></div></div>'

        st.markdown(f'<div class="chunks-section">{full_chips}</div>', unsafe_allow_html=True)