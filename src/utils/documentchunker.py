#assuming we recieve dictionary from the loader part
'''
{
            "Text": text,
            "Document": result.document,
            "Is_OCR_Fallback": False,
            "File_Type":file_type(like pdf,csv,txt etc)
            "File_Path":file_path,
            
}

'''

from transformers import AutoTokenizer
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from docling_core.transforms.serializer.markdown import MarkdownTableSerializer
import uuid
MAX_TOKENS=512
EMBED_MODEL_ID="BAAI/bge-m3"
class MDTableSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc) -> ChunkingDocSerializer:
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
        )
class ChunkingError(Exception):
    pass
class DocumentChunker:
    
    def __init__(self):
        self.tokenizer=HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
            max_tokens=MAX_TOKENS                              
            )
        self.doc_chunker=HybridChunker(
            tokenizer=self.tokenizer,
            merge_peers=True,  
            )
        self.csv_chunker=HybridChunker(
            tokenizer=self.tokenizer,
            repeat_table_header=True,
            serializer_provider=MDTableSerializerProvider()
        )
        
    def chunker_type(self,loaded:dict) -> list[dict]:
        if (loaded["File_Type"]=="pdf" or loaded["File_Type"]=="txt"):
            return self.docling_chunker(loaded)
        else:
            return self.chunk_csv(loaded)
    
    def docling_chunker(self,loaded:dict) -> list[dict]:
        chunks=list(self.doc_chunker.chunk(dl_doc=loaded["Document"]))
        results=[]
        for  i,chunk in enumerate(chunks):
            page_no=None
            label=None
            headings=None
            if chunk.meta and chunk.meta.doc_items:
                headings = chunk.meta.headings
                
                for item in chunk.meta.doc_items:
                    label=item.label.value
                    if item.prov:
                        page_no=item.prov[0].page_no
                        break
            results.append({
                "chunk_id":str(uuid.uuid4()),
                "text":chunk.text,
                "source_type":loaded["File_Type"],
                "source_path":loaded["File_Path"],
                "page_no":page_no,
                "label":label,
                "headings":headings,
                "chunk_index":i
            })
        return results  
    
    def chunk_csv(self,loaded:dict) -> list[dict]:
        chunks=list(self.csv_chunker.chunk(loaded["Document"]))
        results = []
        headers=[]
        try:
            first_table = loaded["Document"].tables[0]
            headers=[cell.text.strip()
                    for cell in first_table.data.table_cells
                    if cell.column_header]
        except Exception:
            headers=[]
        
        try:
            for i,chunk in enumerate(chunks):
                if not chunk.text.strip():
                    continue
                results.append({
                    "chunk_id":str(uuid.uuid4()),
                    "text":chunk.text,
                    "source_type":loaded["File_Type"],
                    "source_path":loaded["File_Path"],
                    "chunk_index":i,
                    "headers": headers,
                    "token_count": self.tokenizer.count_tokens(chunk.text)
                })
        except Exception as e:
            raise ChunkingError(f"Chunking not done! Please try again! Original error: {str(e)}")
        return results

                
            
        
        