
from  qdrant_client import QdrantClient
from  qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter, FieldCondition, MatchValue
)
COLLECTION_NAME = "hotpot_qa"
VECTOR_SIZE = 384
class CollectionCreationError(Exception):
    pass
class EmbeddingStorageError(Exception):
    pass
class FileDeletionError(Exception):
    pass

class VectorStore:
      
    def __init__(self):
        print("Creating qdrant client")
        self.client = QdrantClient(url="http://localhost:6333")
        print("Qdrant client created")
        self._create_collection()
        print("All components ready")

    def _create_collection(self):
        print("Inside _create_collection")
        try:
            print("Getting existing collections")
            existing=[c.name for c in self.client.get_collections().collections]
            print(f"Existing: {existing}")
            if COLLECTION_NAME not in existing:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE , 
                        distance=Distance.COSINE
                        )
                )
                print(f"Collection {COLLECTION_NAME} created!")
                
            else:
                print(f"Collection {COLLECTION_NAME} already exists!")
        
        except Exception as e:
            print(f"CAUGHT EXCEPTION: {e}")
            raise CollectionCreationError(f" Error in creating Collection {e} ")

        
    def upsert(self,embedded_chunks:list[dict]) -> None:
        try:  
            if embedded_chunks:
                points: list[PointStruct] = []
                for chunk in embedded_chunks:
                    payload={
                        "text":chunk["text"],
                        **chunk["metadata"]
                    }
                    points.append(
                        PointStruct(
                        id=chunk["chunk_id"],
                        vector=chunk["embedding"],
                        payload=payload
                        )
                    )
                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                print(f"Upserted {len(points)} chunks")
            else:
                print("No Chunks Found")
            
        except Exception as e:
            raise EmbeddingStorageError(f"Embeddings not created: {e}")
    
    #Finds total chunks in Collection

    def count(self) -> int:
        result = self.client.count(collection_name=COLLECTION_NAME)
        return result.count