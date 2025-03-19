from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    company: str
    date: str
    document: str
    quarter: int
    year: int
    snippet: str
    symbol: str
    url: str


class PineconeSearchResult(BaseModel):
    id: str
    metadata: ChunkMetadata
    score: float


class PineconeQueryResponse(BaseModel):
    matches: list[PineconeSearchResult]
    namespace: str
