import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from models.schemas import QueryRequest,CountResponse
#from models.schemas import CountResponse
from fastapi.middleware.cors import CORSMiddleware
from Services.QueryService import QueryService
from Services.DataIngestionProcess import DataIngestionService
from src.utils.vectorstore import VectorStore
print("Entered main file")
r"""
print("Program started")

from Services.HotpotDataIngestionPipeline import HotpotDataIngestionPipeline

print("Imports done")

try:
    hotpot_service = HotpotDataIngestionPipeline()
    print("Pipeline initialized")

    result = hotpot_service.ingest_hotpot(
        r"C:\Users\DELL\Downloads\hotpot_train_v1.1.json"
    )
    print(result)

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
"""
#import api
#from Services.DataIngestionProcess import DataIngestionService
#from Services.HotpotDataIngestionPipeline import HotpotDataIngestionPipeline
#hotpot_service= HotpotDataIngestionPipeline()
#service = DataIngestionService()

#result=hotpot_service.ingest_hotpot(r"E:\Rag_Project\passion-project-rag_qa_system\hotpot_qa.json")

#result=service.ingest_document(r"C:\Users\DELL\Downloads\NIPS-2017-attention-is-all-you-need-Paper.pdf")

try:
    print("Before VectorStore", flush=True)
    vector_store = VectorStore()
    print("After VectorStore", flush=True)

except BaseException as e:
    import traceback
    print("VectorStore failed:")
    traceback.print_exc()
    raise
app=FastAPI()
query_service = QueryService()
print("QueryService OK")
ingestion_service = DataIngestionService()
print("DataIngestionService OK")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message":"RAG Pipeline is running "}
@app.post("/query")
def query_rag(request:QueryRequest):
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    try:
        result = query_service.query(request.query)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
#the file is uploaded from user's system and travels through internet as bytes to reach the server and gets stored in RAM,and sibce my ingest query expects a pth so we need to save it temporarilt in server disk for processing it

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):

    # 1. validate file type
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}"
        )

    # 2. save to a safe temp file (auto-named, no collision risk)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name          # e.g. /tmp/tmpXYZ123.pdf

    # 3. process,look for duplicate  and always delete temp file after
    try:
        result = ingestion_service.ingest_document(temp_path,original_filename=file.filename)
        if result["status"] == "duplicate":
            raise HTTPException(status_code=409, detail=result["message"])
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_stored": result["chunks_stored"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(temp_path)          # always runs — even if exception occurs


@app.get("/count", response_model=CountResponse)
def count_chunks():

    try:
        total = vector_store.count()

        return {
            "total_chunks": total
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ── NEW: list all unique documents stored in Qdrant ───────────────────────────
@app.get("/documents")
def list_documents():
    try:
        docs = vector_store.get_documents()
        return {"documents": docs, "total": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
# ── NEW: delete a document by source_path ─────────────────────────────────────
@app.delete("/documents")
def delete_document(source_path: str):
    try:
        vector_store.delete(source_path)
        return {"status": "deleted", "source_path": source_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app, host="0.0.0.0", port=8000)
