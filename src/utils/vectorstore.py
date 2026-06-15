'''
for embeddings of pdf it is as follows:
[{ "chunk_id":chunk["chunk_id"],
                    "embedding":vector.tolist()
                    if isinstance(vector,np.ndarray)
                    else list(vector),
                    "text":chunk["text"],
                    "metadata":,{
                        "source_type":loaded["File_Type"],
                "source_path":loaded["File_Path"],
                "page_no":page_no,
                "label":label,
                "headings":headings,
                "chunk_index":i
                        }},]
'''
from  qdrant_client import QdrantClient
from  qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter, FieldCondition, MatchValue,
    SparseVectorParams, Modifier, SparseVector
)
from fastembed import SparseTextEmbedding
COLLECTION_NAME = "rag_docs"
VECTOR_SIZE = 1024  # BAAI/bge-m3 embedding dimension
class CollectionCreationError(Exception):
    pass
class EmbeddingStorageError(Exception):
    pass
class FileDeletionError(Exception):
    pass
class SearchHashError(Exception):
    pass
class VectorStore:
    
    def __init__(self):
        self.client = QdrantClient(
            url="http://localhost:6333"
        )
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")  # NEW
        self._create_collection()
    
    def _create_collection(self):

        try:

            collections_obj = self.client.get_collections()

            existing = [c.name for c in collections_obj.collections]

            print(f"VS: existing collections = {existing}", flush=True)

            if COLLECTION_NAME not in existing:

                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE
                    ),
                    sparse_vectors_config={                      # NEW
                        "bm25": SparseVectorParams(modifier=Modifier.IDF)
                    }
                )
                

            else:
                print(f"Collection {COLLECTION_NAME} already exists!", flush=True)

        except BaseException as e:
            import traceback
            print("VS: FAILED", flush=True)
            traceback.print_exc()
            raise


    def upsert(self,embedded_chunks:list[dict]) -> None:
        try:  
            if embedded_chunks:
                points: list[PointStruct] = []
                for chunk in embedded_chunks:
                    payload={
                        "text":chunk["text"],
                        **chunk["metadata"]
                    }
                    sparse_emb = next(self.sparse_model.embed([chunk["text"]]))   # NEW
                    points.append(
                        PointStruct(
                        id=chunk["chunk_id"],
                        vector={
                            "": chunk["embedding"],
                            "bm25": SparseVector(
                                indices=sparse_emb.indices.tolist(),
                                values=sparse_emb.values.tolist()
                            )
                        },
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
            raise EmbeddingStorageError("Embeddings not created: ",e)
    
    # delete chunks of a particular file from qdrant vector db or removing a file from vector db
    def hash_exists(self, file_hash: str) -> bool:
        try:
            # search for any chunk that has this hash in metadata
            #scroll is a qdrant method to search/filter chunks
            results = self.client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="file_hash",
                            match=MatchValue(value=file_hash)
                        )
                    ]
                ),
                limit=1  # we only need to know if even one exists
            )
            # results is a tuple;scroll method returns tuple -> (points, next_page_offset)
            # if points list is non-empty, hash exists
            return len(results[0]) > 0
        except Exception as e:
            raise SearchHashError(f"Error in searching qdrant for hash,{e}")


    def delete(self,source_path:str) -> None:
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source_path",
                            match=MatchValue(value=source_path)
                        )
                    ]       
                )
            )
            print(f"Deleted chunks for source: {source_path}")
        except Exception as e:
            raise FileDeletionError("OOPS!File not deleted!\nPlease try Again!",e)
    
    #Finds total chunks in Collection
    def count(self) -> int:
        result = self.client.count(collection_name=COLLECTION_NAME)
        return result.count
    
    def get_documents(self) -> list[dict]:
        """
        Scrolls through all points and returns one entry per unique file_hash.
        Each entry contains:
            - filename  : basename extracted from source_path
            - source_path: full path as stored
            - file_hash : unique file identifier
        """
        seen_hashes = set()
        documents = []
        offset = None
    #qdrant may have thousand of chunks so we cant fetch them at once .scroll method fetches 100 at once
        while True:
            results, offset = self.client.scroll(
                collection_name=COLLECTION_NAME,
                with_payload=True,
                with_vectors=False,   # skip vectors — we only need payload
                limit=100,
                offset=offset
            )

            for point in results:
                payload = point.payload or {}
                file_hash = payload.get("file_hash")
                source_path = payload.get("source_path", "")

                if file_hash and file_hash not in seen_hashes:
                    seen_hashes.add(file_hash)
                    documents.append({
                        "filename": source_path.split("\\")[-1].split("/")[-1],
                        "source_path": source_path,
                        "file_hash": file_hash,
                    })

            # scroll returns None offset when there are no more pages
            if offset is None:
                break

        return documents