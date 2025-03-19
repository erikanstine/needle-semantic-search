from pydantic import BaseModel


class SearchResult(BaseModel):
    company: str
    quarter: str
    url: str
    document: str
    snippets: list[str]


class SearchResponse(BaseModel):
    results: list[SearchResult]
