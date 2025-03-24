from pydantic import BaseModel


class SearchResult(BaseModel):
    company: str
    quarter: str
    year: str
    url: str
    document: str
    snippets: list[str]


class SummarizedSearchResult(BaseModel):
    company: str
    quarter: str
    year: str
    url: str
    summary: list[str]


class SearchResponse(BaseModel):
    results: list[SummarizedSearchResult]
