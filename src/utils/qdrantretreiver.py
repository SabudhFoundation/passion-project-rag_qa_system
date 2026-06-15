"""
will take [{query:"",
            embedding:[]
},{},{}] as input
will take embedd queries
for each query 
search qdrant
collect results
deduplicate
return retreievd chunks
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Prefetch, FusionQuery, Fusion, SparseVector
from fastembed import SparseTextEmbedding
COLLECTION_NAME="rag_docs"
class QdrantRetrieverError(Exception):
    pass

class QdrantRetriever:
    #creating connection to qdrant
    def __init__(self):
        try:
            print("Connecting to Qdrant")
            self.client=QdrantClient(
            host="localhost",
            port=6333
            )
            self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")  # NEW
            #store query embedder object
            print("Qdrant Retriever Ready!")
        except Exception as e:
            raise QdrantRetrieverError(f"Retriever initialization failed: {str(e)}")
        
    def retrieve(self,embedded_queries:list[dict],top_k:int=5) -> list[dict]:
        try:
            
            if not embedded_queries:
                return []
            all_results=[]
            
            for item in embedded_queries:
                query=item["query"]
                embedding=item["embedding"]
                print(f"\nSearching for {query}...")
                sparse_emb = next(self.sparse_model.embed([query]))   # NEW
                search_results=self.client.query_points(
                    collection_name=COLLECTION_NAME,
                    prefetch=[
                        Prefetch(query=embedding, using="", limit=top_k*2),
                        Prefetch(
                            query=SparseVector(
                                indices=sparse_emb.indices.tolist(),
                                values=sparse_emb.values.tolist()
                            ),
                            using="bm25",
                            limit=top_k*2
                        ),
                    ],
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False
                ).points
                for result in search_results:
                    retrieved_chunk={
                        "query":query,
                        "score":result.score,
                        "chunk_id":result.id,
                        "text":result.payload.get("text",""),
                        "metadata":{
                                key: value
                                for key, value
                                in result.payload.items()
                                if key != "text"
                        }
                    }
                    all_results.append(retrieved_chunk)
            
            return all_results
        
        except Exception as e:
            
            raise QdrantRetrieverError(f"Retrieval failed: {str(e)}")
                    
            