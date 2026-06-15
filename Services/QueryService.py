from src.utils.querydecomposer import QueryDecomposer
from src.utils.embeddings import Embedding
from src.utils.qdrantretreiver import QdrantRetriever
from src.utils.rrfranker import RRFRanker
from src.utils.reranker import ReRanker
from src.utils.groqclient import GroqClient
from src.utils.contextbuilder import ContextBuilder
from src.utils.answergeneration import AnswerGenerator



r"""
from src.utils.querydecomposer import QueryDecomposer
#from src.utils.queryembedder import QueryEmbedder
from src.utils.embeddings import Embedding
from src.utils.qdrantretreiver import QdrantRetriever
from src.utils.rrfranker import RRFRanker
from src.utils.reranker import ReRanker
from src.utils.groqclient import GroqClient
from src.utils.contextbuilder import ContextBuilder
from src.utils.answergeneration import AnswerGenerator
"""
class QueryService:
    def __init__(self):
        self.decomposer = QueryDecomposer()
        #self.embedder = QueryEmbedder()
        self.embedder = Embedding()
        self.retriever = QdrantRetriever()
        self.rrfranker= RRFRanker()
        self.reranker=ReRanker()
        self.context_builder=ContextBuilder()
        self.groq_client = GroqClient()
        self.generator=AnswerGenerator( groq_client=self.groq_client)
        
    def query(self,user_query:str) -> dict:
        
        queries = self.decomposer.decompose(user_query)
        embedded_queries = self.embedder.embed_queries(queries)
        retrieved_chunks = self.retriever.retrieve(embedded_queries=embedded_queries,top_k=5)
        fused_chunks=self.rrfranker.fused(retrieved_chunks)
        reranked_chunks=self.reranker.rerank(user_query,fused_chunks)
        context=self.context_builder.build(user_query,reranked_chunks)
        answer = self.generator.generate_answer(user_query, context)
        sources=[]
        for chunk in reranked_chunks:
            sources.append({
                #get takes two arguments one key and another default value to return if the key doesnt exist
                "file": chunk["metadata"].get("source_path", "").split("\\")[-1],
                "page": chunk["metadata"].get("page_no"),
                "heading": chunk["metadata"].get("headings", [""])[0],
                "text": chunk["text"]
            })
        return {"answer":answer,"sources":sources}