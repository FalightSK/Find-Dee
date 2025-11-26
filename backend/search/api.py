from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from tagger import TagGenerator
from deduplicator import TagDeduplicator
from search import TagSearch

load_dotenv()

app = FastAPI(title="Tag Generation and Search API")

# Initialize services
try:
    tagger = TagGenerator()
    deduplicator = TagDeduplicator()
    searcher = TagSearch()
except ValueError as e:
    print(f"Error initializing services: {e}")
    # In a real app, we might want to handle this more gracefully or fail startup
    pass

class GenerateRequest(BaseModel):
    text: str

class GenerateResponse(BaseModel):
    tags: List[str]

class DeduplicateRequest(BaseModel):
    tags: List[str]

class DeduplicateResponse(BaseModel):
    unique_tags: List[str]

class SearchRequest(BaseModel):
    query: str
    tag_pool: List[str]

class SearchResponse(BaseModel):
    match_score: float
    query_tags: List[str]

@app.post("/tags/generate", response_model=GenerateResponse)
async def generate_tags(request: GenerateRequest):
    try:
        tags = tagger.generate_tags(request.text)
        return GenerateResponse(tags=tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tags/deduplicate", response_model=DeduplicateResponse)
async def deduplicate_tags(request: DeduplicateRequest):
    try:
        unique_tags = deduplicator.deduplicate(request.tags)
        return DeduplicateResponse(unique_tags=unique_tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    try:
        query_tags = searcher.extract_query_tags(request.query, tag_pool=request.tag_pool)
        score = searcher.match(query_tags, request.tag_pool)
        return SearchResponse(match_score=score, query_tags=query_tags)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
