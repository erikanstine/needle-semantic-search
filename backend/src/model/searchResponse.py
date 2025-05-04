from pydantic import BaseModel


class SearchResult(BaseModel):
    company: str
    quarter: str
    year: str
    url: str
    document: str
    snippets: list[str]


class Snippet(BaseModel):
    company: str
    quarter: str
    year: str
    url: str
    participants: dict[str, str]
    section: str
    text: str


class SearchResponse(BaseModel):
    answer: str
    snippets: list[Snippet]
