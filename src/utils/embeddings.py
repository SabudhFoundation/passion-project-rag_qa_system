r"""
Assuming chunks come from documentchunker file and have format as
for pdf:
[{
                "chunk_id":str(uuid.uuid4()),
                "text":chunk.text,
                "source_type":loaded["File_Type"],
                "source_path":loaded["File_Path"],
                "page_no":page_no,
                "label":label,
                "headings":headings,
                "chunk_index":i
            },{
                "chunk_id":str(uuid.uuid4()),
                "text":chunk.text,
                "source_type":loaded["File_Type"],
                "source_path":loaded["File_Path"],
                "page_no":page_no,
                "label":label,
                "headings":headings,
                "chunk_index":i
            }]
for csv
[
    {
                    "chunk_id":str(uuid.uuid4()),
                    "text":chunk.text,
                    "source_type":loaded["File_Type"],
                    "source_path":loaded["File_Path"],
                    "chunk_index":i,
                    "headers": headers,
                    "token_count": self.tokenizer.count_tokens(chunk.text)
                },
                {
                    "chunk_id":str(uuid.uuid4()),
                    "text":chunk.text,
                    "source_type":loaded["File_Type"],
                    "source_path":loaded["File_Path"],
                    "chunk_index":i,
                    "headers": headers,
                    "token_count": self.tokenizer.count_tokens(chunk.text)
                }
]
"""
r"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
EMBED_MODEL_ID="BAAI/bge-m3"
class EmbeddingError(Exception):
    pass
class Embedding:
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer(
            EMBED_MODEL_ID
            )
        print("Embedding model loaded!")
    def prepare_embedding_text(self,chunk:dict) -> str:
        source_type=chunk.get("source_type","").lower()
        if source_type in ["pdf","txt"]:
            headings=chunk.get("headings")
            if headings:
                heading_text=" > ".join(headings)
                enriched_text=f"{heading_text}\n\n{chunk['text']}"
                return enriched_text
            
            return chunk["text"]
        
        elif source_type=="csv":
            return chunk["text"]
        return chunk["text"]
    
    def generate_embeddings(self,chunks:List[dict],batch_size : int=4) -> list[dict]:
        if not chunks:
            return []
        try:
            #generate text
            filtered = [c for c in chunks if c.get("text", "").strip()]
            texts = [self.prepare_embedding_text(c) for c in filtered]
            
            #generate embeddings
            vectors=self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=True
                )
            
            results=[]
            for chunk,vector in zip(filtered,vectors):
                results.append({
                    "chunk_id":chunk["chunk_id"],
                    "embedding":vector.tolist()
                    if isinstance(vector,np.ndarray)
                    else list(vector),
                    "text":chunk["text"],
                    "metadata":{
                        key:value
                        for key,value in chunk.items()
                        if key not in ["text","chunk_id"]
                    }
                     
                })
            return results

        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {str(e)}")
"""
print("before sentence transfomrs import")
from sentence_transformers import SentenceTransformer
print("after sentence transfomrs import")
print("before typing import")
from typing import List
print("after typing import")
print("before numpy import")
import numpy as np
print("after numpy import")
EMBED_MODEL_ID = "BAAI/bge-m3"

class EmbeddingError(Exception):
    pass

class Embedding:
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer(EMBED_MODEL_ID)
        print("Embedding model loaded!")

    def prepare_embedding_text(self, chunk: dict) -> str:
        source_type = chunk.get("source_type", "").lower()
        if source_type in ["pdf", "txt"]:
            headings = chunk.get("headings")
            if headings:
                heading_text = " > ".join(headings)
                return f"{heading_text}\n\n{chunk['text']}"
            return chunk["text"]
        elif source_type == "csv":
            return chunk["text"]
        return chunk["text"]

    def generate_embeddings(self, chunks: List[dict], batch_size: int = 4) -> list[dict]:
        if not chunks:
            return []
        try:
            filtered = [c for c in chunks if c.get("text", "").strip()]
            texts = [self.prepare_embedding_text(c) for c in filtered]
            vectors = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            results = []
            for chunk, vector in zip(filtered, vectors):
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "embedding": vector.tolist() if isinstance(vector, np.ndarray) else list(vector),
                    "text": chunk["text"],
                    "metadata": {
                        key: value for key, value in chunk.items()
                        if key not in ["text", "chunk_id"]
                    }
                })
            return results
        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {str(e)}")

    def embed_queries(self, queries: list[str]) -> list[dict]:
        try:
            if not queries:
                return []
            vectors = self.model.encode(
                queries,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            results = []
            for query, vector in zip(queries, vectors):
                results.append({
                    "query": query,
                    "embedding": vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
                })
            return results
        except Exception as e:
            raise EmbeddingError(f"Query embedding failed: {str(e)}")