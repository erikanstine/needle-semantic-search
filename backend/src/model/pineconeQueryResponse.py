from pydantic import BaseModel
from typing import List, Optional


class Speaker(BaseModel):
    name: str
    type: str  # "executive" | "analyst" | "operator" | "other"
    role: Optional[str] = None  # "CEO", "CFO", etc.


class ChunkMetadata(BaseModel):
    url: str
    section: str  # "prepared_remarks" | "qa"
    company: str
    quarter: str
    year: str
    call_ts: str
    snippet: Optional[str] = None
    primary_speakers: List[Speaker]
    participants: List[Speaker]
    start_token: Optional[int] = None
    end_token: Optional[int] = None


class PineconeSearchResult(BaseModel):
    id: str
    metadata: ChunkMetadata
    score: float


class PineconeQueryResponse(BaseModel):
    matches: list[PineconeSearchResult]
    namespace: str
