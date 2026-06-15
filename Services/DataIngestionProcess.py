from src.utils.documentloader import DocumentLoader
from src.utils.documentchunker import DocumentChunker
from src.utils.embeddings import Embedding
from src.utils.vectorstore import VectorStore
import hashlib

class DataIngestionService:
    def __init__(self):
        self.loader=DocumentLoader()
        self.chunker=DocumentChunker()
        self.embedder=Embedding()
        self.vector_store=VectorStore()
    
    def _compute_hash(self, file_path: str) -> str:
        # read file as bytes and compute SHA256
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()   
        
    
    def ingest_document(self, file_path: str,original_filename: str = None):
        file_hash = self._compute_hash(file_path)
        if self.vector_store.hash_exists(file_hash):
            return {
                "status": "duplicate",
                "message": "Document already exists in knowledge base"
            }
        loaded=self.loader.load(file_path)
        if original_filename:
            loaded["File_Path"] = original_filename
        chunks=self.chunker.chunker_type(loaded)
        embedded_chunks = self.embedder.generate_embeddings(chunks)
        for chunk in embedded_chunks:
            chunk["metadata"]["file_hash"] = file_hash
        self.vector_store.upsert(embedded_chunks)
        return {
            "status": "success",
            "chunks_stored": len(embedded_chunks)
        }