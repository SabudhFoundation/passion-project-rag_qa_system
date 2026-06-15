from sentence_transformers import CrossEncoder

class ReRankerError(Exception):
    pass

class ReRanker:
    
    def __init__(self,top_n:int=5):
        print("loading reranker model")
        self.model=CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.top_n=top_n
        print("Reranker model loaded")
    
    def rerank(self,original_query:str,fused_chunks:list[dict]) -> list[dict]:
        try:
            if not fused_chunks:
                return []
            
            #build (query,chunk_text) pairs -> one per chunk
            pairs=[(original_query,chunk["text"])for chunk in fused_chunks]
            #corss encode scores of all pairs in one batch
            scores=self.model.predict(pairs)
            #attach score to each chunk
            for chunk,score in zip(fused_chunks,scores):
                chunk["rerank_score"]=float(score)
            #sort by rerank order,descending
            reranked=sorted(fused_chunks,key=lambda x:x["rerank_score"],reverse=True)
            return reranked[:self.top_n]
        
        except Exception as e:
            raise ReRankerError(f"Reranking failed: {str(e)}")