from src.hotpot_utils.hotpotloader import HotpotLoader
from src.hotpot_utils.fieldextractor import ExtractingField
from src.hotpot_utils.hotpotchunker import HotpotChunker
from src.hotpot_utils.hotpotembedder import Embedder
from src.hotpot_utils.hotpotvectorstore import VectorStore
import time
class HotpotDataIngestionPipeline:
    
    def __init__(self):
        print("Loader init")
        self.loader=HotpotLoader()

        print("Chunker init")
        self.chunker=HotpotChunker()

        print("Extractor init")
        self.extractor=ExtractingField()

        print("Embedder init")
        self.embedder=Embedder()
        time.sleep(2)
        print("Vector store init")
        self.vector_store=VectorStore()
        print("All components ready") 

    def ingest_hotpot(self, file_path: str):
        print("inside ingest_hotpot")
        loaded=self.loader.loader_hotpot(file_path)
        print("after loaded")
        table1,table2=self.extractor.extracting_fields(loaded)
        print("after extracting")
        chunks=self.chunker.chunking(table2)
        print("after chunking")
        embedded_chunks = self.embedder.generate_embeddings(chunks)
        print("after embedinngs generation")
        self.vector_store.upsert(embedded_chunks)
        print("after storing embeddings")
        return {
            "status": "success",
            "chunks_stored": len(embedded_chunks)
        }






