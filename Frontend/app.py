import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat_section
from components.documents import render_documents_page

st.set_page_config(
    page_title="CosmicQuery",
    page_icon="🤖",
    layout="wide"
)

with open("frontend/styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_sidebar()

if st.session_state.get("page", "chat") == "documents":
    render_documents_page()
else:
    render_chat_section()