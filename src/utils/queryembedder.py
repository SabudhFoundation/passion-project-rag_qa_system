from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
EMBED_MODEL_ID = "BAAI/bge-m3"
class QueryEmbeddingError(Exception):
    pass


class QueryEmbedder:
    
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer(
            EMBED_MODEL_ID
            )
        print("Embedding model loaded!")
    
    def embed_queries(self,queries:list[str]) -> list[dict]:
        
        try:
            if not queries:
                return []
            vectors = self.model.encode(
                queries,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            results = []
            
            for query,vector in zip(queries,vectors):
                
                results.append({
                    "query":query,
                    "embedding": (
                        vector.tolist()
                        if isinstance(vector, np.ndarray)
                        else list(vector)
                    )
                })
            return results
        except Exception as e:
            raise QueryEmbeddingError( f"Query embedding failed: {str(e)}")
        