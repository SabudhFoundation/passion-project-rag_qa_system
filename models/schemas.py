from pydantic import BaseModel
from typing import Optional
#pydantic helps us define the strcture of data inside response and request
#it basically helps in validating data 
#it helps us define what fields should exist,what type of fields are these what response format should look like

#defines input for POST/Query
class QueryRequest(BaseModel):
    query:str

#defines one source chunk returned by rag system
class SourceChunk(BaseModel):
    file: str
    page: Optional[int]
    heading: Optional[str]
    text: str

#defines full api response from our rag system
class QueryResponse(BaseModel):
    answer:str
    sources:list[SourceChunk]

#defines what to return after ingesting
class IngestResponse(BaseModel):
    status: str
    filename: str
    chunks_stored: int

class DeleteRequest(BaseModel):
    file_path: str
    
class DeleteResponse(BaseModel):
    status: str
    message: str
class CountResponse(BaseModel):
    total_chunks: int
    
    