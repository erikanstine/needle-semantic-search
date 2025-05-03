from pydantic import BaseModel


class Filter(BaseModel):
    company: str | None = None
    quarter: str | None = None
    section: str | None = None


class SearchQuery(BaseModel):
    query: str
    filters: Filter | None = None
