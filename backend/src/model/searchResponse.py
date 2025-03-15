from pydantic import BaseModel

from .pineconeQueryResponse import SearchResult


class SearchResponse(BaseModel):
    results: list[SearchResult]
