import streamlit as st
import requests

API_BASE="http://localhost:8000"

def fetch_documents()->list[dict]:
    try:
        resp=requests.get(f"{API_BASE}/documents",timeout=5)
        resp.raise_for_status()
        return resp.json().get("documents",[])
    except Exception as e:
        st.error(f"Could not load documents: {e}")
        return []

def ingest_document(uploaded_file)->dict:
    try:
        resp=requests.post(
            f"{API_BASE}/ingest",
            files={
                "file":(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            },
            timeout=600
        )
        if resp.status_code==409:
            return{
                "status":"duplicate",
                "message":resp.json().get(
                    "detail",
                    "Duplicate file."
                )
            }
        resp.raise_for_status()
        return{
            "status":"success",
            **resp.json()
        }
    except requests.exceptions.Timeout:
        return{
            "status":"error",
            "message":"Request timed out."
        }
    except Exception as e:
        return{
            "status":"error",
            "message":str(e)
        }

def delete_document(source_path:str)->bool:
    try:
        resp=requests.delete(
            f"{API_BASE}/documents",
            params={"source_path":source_path},
            timeout=5
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Could not delete document: {e}")
        return False

def render_documents_page():
    st.markdown("""
    <style>
    .docs-title{
        font-size:42px;
        font-weight:700;
        color:white;
        margin-bottom:8px;
    }
    .docs-subtitle{
        color:#64748b;
        font-size:15px;
        margin-bottom:32px;
    }
    .upload-card{
        background:#071028;
        border:1px solid rgba(109,93,252,.18);
        border-radius:20px;
        padding:28px;
        margin-bottom:28px;
    }
    .section-title{
        color:white;
        font-size:22px;
        font-weight:600;
        margin-bottom:18px;
    }
    .uploaded-file{
        margin-top:18px;
        padding:14px 16px;
        border-radius:12px;
        background:rgba(109,93,252,.12);
        color:#dbe4ff;
        border:1px solid rgba(109,93,252,.18);
    }
    .docs-list{
        background:#071028;
        border:1px solid rgba(109,93,252,.18);
        border-radius:20px;
        padding:24px;
    }
    .doc-row{
        display:flex;
        justify-content:space-between;
        align-items:center;
        padding:14px 0;
        border-bottom:1px solid rgba(255,255,255,.06);
    }
    .doc-row:last-child{
        border-bottom:none;
    }
    .doc-name{
        color:#e2e8f0;
        font-size:15px;
    }
    .empty-docs{
        color:#64748b;
        text-align:center;
        padding:18px 0;
    }
    [data-testid="stFileUploader"]{
        background:transparent!important;
        border:none!important;
    }
    [data-testid="stFileUploader"] section{
        border:none!important;
        background:transparent!important;
        padding:0!important;
    }
    [data-testid="stFileUploaderDropzone"]{
        border:none!important;
        background:transparent!important;
        padding:0!important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"]{
        display:none!important;
    }
    button[kind="secondary"]{
        background:linear-gradient(90deg,#6d5dfc,#8b5cf6)!important;
        color:white!important;
        border:none!important;
        border-radius:12px!important;
    }
    </style>
    """,unsafe_allow_html=True)

    st.markdown("""
    <div class="docs-title">
        Documents
    </div>
    <div class="docs-subtitle">
        Upload and manage your documents for retrieval augmented generation.
    </div>
    """,unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-card">
        <div class="section-title">
            Upload PDF
        </div>
    </div>
    """,unsafe_allow_html=True)

    uploaded_file=st.file_uploader(
        "📎 Upload PDF",
        type=["pdf"],
        label_visibility="visible"
    )

    if "uploaded_filename" not in st.session_state:
        st.session_state.uploaded_filename=None

    if uploaded_file is not None:
        st.session_state.uploaded_filename=uploaded_file.name

    if st.session_state.uploaded_filename:
        st.markdown(
            f"""
            <div class="uploaded-file">
                📄 {st.session_state.uploaded_filename}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)

        if st.button(
            "⚙️ Process PDF",
            type="primary",
            use_container_width=True
        ):
            with st.spinner("Processing PDF..."):
                result=ingest_document(uploaded_file)

            if result["status"]=="success":
                st.success("PDF processed successfully.")
                st.session_state.uploaded_filename=None
                st.rerun()

            elif result["status"]=="duplicate":
                st.warning(result["message"])

            else:
                st.error(result["message"])

    docs=fetch_documents()

    st.markdown("""
    <div class="docs-list">
        <div class="section-title">
            Stored Documents
        </div>
    """,unsafe_allow_html=True)

    if docs:
        for doc in docs:
            filename=(doc.get("original_filename") or doc.get("filename") or doc.get("source_path","Unknown").split("/")[-1])
            source_path=doc.get("source_path","")

            col1,col2=st.columns([8,1])

            with col1:
                st.markdown(
                    f"""
                    <div class="doc-row">
                        <div class="doc-name">
                            📄 {filename}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                if st.button("🗑",key=f"del_{source_path}"):
                    if delete_document(source_path):
                        st.success(f"Deleted {filename}")
                        st.rerun()
    else:
        st.markdown("""
        <div class="empty-docs">
            No documents stored yet.
        </div>
        """,unsafe_allow_html=True)

    st.markdown("</div>",unsafe_allow_html=True)