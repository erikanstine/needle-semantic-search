from pydantic import BaseModel
from typing import List, Optional


class PageFormatNotImplementedException(Exception):
    "Raised when we have not implemented a page format"

    pass


class Speaker(BaseModel):
    name: str
    type: str  # "executive" | "analyst" | "operator" | "other"
    role: Optional[str] = None  # "CEO", "CFO", etc.


class TranscriptChunk(BaseModel):
    chunk_id: str
    url: str
    section: str  # "prepared_remarks" | "qa"
    company: str
    quarter: str
    call_ts: str
    text: str
    snippet: Optional[str] = None
    primary_speakers: List[Speaker]
    participants: List[Speaker]
    start_token: Optional[int] = None
    end_token: Optional[int] = None
