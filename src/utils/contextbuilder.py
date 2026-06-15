class ContextBuilderError(Exception):
    pass
class ContextBuilder:
    
    def __init__(self,max_chars:int = 6000):
        self.max_chars=max_chars
    def build(self, original_query:str, reranked_chunks:list[dict]) -> str:
        try:
            if not reranked_chunks:
                raise ContextBuilderError(f"No chunks to build context from!")
            #calling helper function that choose chunks that fit inside context limit 
            selected=self._select_within_budget(reranked_chunks)
            context = self._format(selected)
            return context
        except ContextBuilderError:
            raise ContextBuilderError("Context Limit Exceeded!")
        except Exception as e:
            raise ContextBuilderError(f"Context building failed: {str(e)}")

    def _select_within_budget(self, chunks: list[dict]) -> list[dict]:
        selected=[]
        total_chars=0
        #reranked chunks already sorted by importance
        #reranked chunks already sorted by importance
        for chunk in chunks:
            chunk_len=len(chunk["text"])
            if total_chars + chunk_len > self.max_chars:
                break
            selected.append(chunk)
            total_chars +=chunk_len
        return selected
    
    #convert chunks into clean readable text
    def _format(self, chunks: list[dict]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk["metadata"]
            source  = meta.get("source_path", "unknown").split("\\")[-1]  # just filename
            page    = meta.get("page_no", "?")
            heading = meta.get("headings", [""])[0]
            header = f"[{i}] {source} — page {page}"
            if heading:
                header += f" — {heading}"
            parts.append(f"{header}\n{chunk['text'].strip()}")
        
        return "\n\n---\n\n".join(parts)
            
        