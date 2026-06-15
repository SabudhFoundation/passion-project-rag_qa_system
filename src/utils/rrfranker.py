"""
Input:  list[dict] from QdrantRetriever
            [{"query":..., "score":..., "chunk_id":..., "text":..., "metadata":...}]
    Output: list[dict] — deduplicated, RRF-scored, sorted
            [{"chunk_id":..., "rrf_score":..., "text":..., "metadata":..., "matched_queries":[...]}]

"""

class RRFRankerError(Exception):
    pass

class RRFRanker:
    
    def __init__(self,k:int=60):
        self.k=k   #RRF Constant, 60 is standard
        
    def fused(self,retrieved_chunks:list[dict]) -> list[dict]:
        
        try:
            if not retrieved_chunks:
                return []
            #Step 1
            #Group chunks by query,preserving rank order(Chunks are already sorted)
            query_buckets : dict[str,list[str]] = {}
            for chunk in retrieved_chunks:
                query=chunk["query"]
                if query not in query_buckets:
                    query_buckets[query]=[]
                query_buckets[query].append(chunk)
            
            #step 2
            #RRF scoring
            #If multiple queries retrieve same chunk,increase that chunk's relative score
            
            fused : dict[str,dict] ={}
            for query,chunks in query_buckets.items():    #will return key-value pairs one by one
                for rank,chunk in enumerate(chunks):
                    cid=chunk["chunk_id"]
                    rrf_score=1/(self.k+rank+1)
                    if cid not in fused:
                        fused[cid] = {
                            "chunk_id": cid,
                            "rrf_score": 0.0,
                            "text": chunk["text"],
                            "metadata": chunk["metadata"],
                            "matched_queries": []
                        }
                    fused[cid]["rrf_score"]+=rrf_score
                    fused[cid]["matched_queries"].append(query)
            
            #step 3
            #sort by rrf value descending order
            #x means current item being examined and othe part means sort by rrf_score(we got a dictionary)
            ranked=sorted(fused.values(), key = lambda x:x["rrf_score"],reverse=True)
            return ranked
        
        except Exception as e:
            raise RRFRankerError(f"RRF fusion failed: {str(e)}")