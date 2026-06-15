import streamlit as st
import requests
from components.chunks import render_retrieved_chunks

API_URL = "http://localhost:8000"


def render_user_message(message, time=""):
    st.markdown(f"""
    <div class="user-message-wrapper">
        <div class="user-message">
            {message}
            <span class="message-time">{time}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_assistant_message(answer, sources):
    st.markdown(f"""
    <div class="assistant-wrapper">
        <div class="assistant-icon">🧠</div>
        <div class="assistant-card">
            <div class="assistant-text">{answer}</div>
            <div class="sources-wrapper">
                {"".join([f'<div class="source-chip">{i+1} {s["file"]}</div>' for i, s in enumerate(sources)])}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_retrieved_chunks(sources)


def call_query_api(question):
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": question},
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "sources": []}


def render_chat_section():

    # initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "loading" not in st.session_state:
        st.session_state["loading"] = False

    # render existing messages
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            render_user_message(msg["content"])
        else:
            render_assistant_message(msg["answer"], msg["sources"])

    # loading indicator
    if st.session_state["loading"]:
        st.markdown("""
        <div class="assistant-wrapper">
            <div class="assistant-icon">🧠</div>
            <div class="assistant-card">
                <div class="assistant-text" style="color:#64748b;">
                    ⏳ Thinking...
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # input box
    question = st.chat_input("Type your question here...")

    if question and not st.session_state["loading"]:
        # add user message
        st.session_state["messages"].append({
            "role": "user",
            "content": question
        })
        st.session_state["loading"] = True
        st.rerun()

    # if loading, call API
    if st.session_state["loading"]:
        last_user_msg = st.session_state["messages"][-1]["content"]
        result = call_query_api(last_user_msg)
        st.session_state["messages"].append({
            "role": "assistant",
            "answer": result.get("answer", ""),
            "sources": result.get("sources", [])
        })
        st.session_state["loading"] = False
        st.rerun()