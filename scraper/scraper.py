import re
import requests
import tiktoken

from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel
from typing import List, Optional, Tuple


class PageFormatNotImplementedException(BaseException):
    "Raised when we have not implemented a page format"

    pass


class Speaker(BaseModel):
    name: str
    type: str  # "executive" | "analyst" | "operator" | "other"
    role: Optional[str] = None  # "CEO", "CFO", etc.


class TranscriptChunk(BaseModel):
    chunk_id: str
    section: str  # "prepared_remarks" | "qa"
    company: str
    quarter: str
    text: str
    snippet: Optional[str] = None
    primary_speakers: List[Speaker]
    participants: List[Speaker]
    start_token: Optional[int] = None
    end_token: Optional[int] = None


call_stages = ["prepared_remarks", "qa"]


def tokenize(text: str) -> List[int]:
    encoding = tiktoken.get_encoding("cl100k_base")
    return encoding.encode(text)


def clean_ads(soup: BeautifulSoup) -> BeautifulSoup:
    ads = soup.find_all("div", {"data-pitch-placement": True})
    [a.decompose() for a in ads]
    return soup


def parse_speaker(t: Tag) -> Speaker:
    name = t.strong.text
    inner_text = t.text.lower()
    _type = ""
    role = ""

    if "chief executive officer" in inner_text:
        role = "CEO"
        _type = "executive"
    elif "chief financial officer" in inner_text:
        role = "CFO"
        _type = "executive"
    elif "senior vice president" in inner_text:
        role = "SVP"
        _type = "executive"
    elif "vice president" in inner_text:
        role = "VP"
        _type = "executive"
    elif "analyst" in inner_text:
        role = "Analyst"
        _type = "analyst"
    elif "operator" in inner_text:
        role = "Operator"
        _type = "operator"
    elif "investor relations" in inner_text:
        role = "Investor Relations"
        _type = "investor relations"
    else:
        if "chief" in inner_text:
            print("NEW SPEAKER TITLE:", inner_text)
        _type = "other"
    return Speaker(name=name, type=_type, role=role if role else None)


def parse_metadata(soup: BeautifulSoup) -> Tuple[str, str]:
    t = soup.find("h1").text
    reg = r".+ \((\w+)\) (Q\d \d{4}) Earnings Call Transcript"
    ticker, quarter = re.search(reg, t).groups()

    return ticker, quarter


def parse_participants(t: Tag) -> dict[str, Speaker]:
    d = {}
    participants = t.find("h2", string="Call participants:").find_next_siblings("p")
    for p in participants:
        if not p.strong:
            continue
        speaker = parse_speaker(p)
        d[speaker.name] = speaker
    return d


def parse_speakers(speakers: List[Speaker], section: str) -> List[Speaker]:
    if len(speakers) == 1:
        return speakers

    return [s for s in speakers if s.type == "executive"]


def chunk_id(company, quarter, section, n: str) -> str:
    q, y = quarter.lower().split(" ")
    return f"{company.lower()}-{q}-{y}-{section}-{n}"


def iterate_elements(url: str) -> list[TranscriptChunk]:
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    soup = clean_ads(soup)

    company, quarter = parse_metadata(soup)
    article_body = soup.find("div", class_="article-body")
    participant_map = parse_participants(article_body)
    elements = article_body.find("h2", string="Prepared Remarks:").find_next_siblings()
    chunks = []
    current_step = 0
    current_speakers = None
    current_text = ""
    chunk_count = 0

    """
    Start no 'current step'
    Switch on h2: None -> Prepared remarks -> Q&A, different behavior
    """
    if not any(
        article_body.find("h2", string="Questions & Answers:")
        or article_body.find("h2", string="Questions and Answers:")
    ):
        raise PageFormatNotImplementedException

    for ele in elements:
        match call_stages[current_step]:
            case "prepared_remarks":
                if ele.name == "h2":
                    if "call participants" in ele.text.lower():
                        break
                    if current_speakers:
                        chunks.append(
                            TranscriptChunk(
                                chunk_id=chunk_id(
                                    company,
                                    quarter,
                                    call_stages[current_step],
                                    chunk_count,
                                ),
                                section=call_stages[current_step],
                                company=company,
                                quarter=quarter,
                                primary_speakers=parse_speakers(
                                    current_speakers, call_stages[current_step]
                                ),
                                participants=current_speakers,
                                text=current_text,
                            )
                        )
                        chunk_count += 1
                        current_text = ""
                        current_speakers = []

                    current_step += 1
                    continue
                if ele.name == "p":
                    if ele.find("strong"):
                        # Change in speaker
                        # Save off chunk
                        if current_speakers:
                            chunks.append(
                                TranscriptChunk(
                                    chunk_id=chunk_id(
                                        company,
                                        quarter,
                                        call_stages[current_step],
                                        chunk_count,
                                    ),
                                    section=call_stages[current_step],
                                    company=company,
                                    quarter=quarter,
                                    primary_speakers=parse_speakers(
                                        current_speakers, call_stages[current_step]
                                    ),
                                    participants=current_speakers,
                                    text=current_text,
                                )
                            )
                            chunk_count += 1
                            current_text = ""
                            current_speakers = []

                        # Get new speaker
                        current_speaker = parse_speaker(ele)
                        if current_speaker.type in ["operator", "investor relations"]:
                            current_speaker = None
                            current_speakers = []
                        else:
                            current_speakers.append(current_speaker)
                        continue

                    if not current_speakers:
                        continue

                    current_text = current_text + " " + ele.text
            case "qa":
                if ele.name == "h2":
                    if "call participants" in ele.text.lower():
                        if current_speakers:
                            chunks.append(
                                TranscriptChunk(
                                    chunk_id=chunk_id(
                                        company,
                                        quarter,
                                        call_stages[current_step],
                                        chunk_count,
                                    ),
                                    section=call_stages[current_step],
                                    company=company,
                                    quarter=quarter,
                                    primary_speakers=parse_speakers(
                                        current_speakers, call_stages[current_step]
                                    ),
                                    participants=current_speakers,
                                    text=current_text,
                                )
                            )
                        break
                    print("Unexpected <h2>:", ele.text)
                """
                Split into full Q/A exchanges, add participants as they happen
                """
                if ele.name == "p":
                    if ele.find("strong"):
                        current_speaker = parse_speaker(ele)
                        if "Duration:" in current_speaker.name:
                            current_speaker = None
                            continue
                        if current_speaker.type in ["operator", "investor relations"]:
                            # If operator AND current_speakers, save off chunk
                            if current_speakers:
                                chunks.append(
                                    TranscriptChunk(
                                        chunk_id=chunk_id(
                                            company,
                                            quarter,
                                            call_stages[current_step],
                                            chunk_count,
                                        ),
                                        section=call_stages[current_step],
                                        company=company,
                                        quarter=quarter,
                                        primary_speakers=parse_speakers(
                                            current_speakers, call_stages[current_step]
                                        ),
                                        participants=current_speakers,
                                        text=current_text,
                                    )
                                )

                            current_speaker = None
                            current_speakers = []
                            chunk_count += 1
                            current_text = ""
                        else:
                            if current_speaker.name not in [
                                cs.name for cs in current_speakers
                            ]:
                                current_speakers.append(current_speaker)
                            continue

                    if not current_speakers:
                        continue
                    current_text = current_text + " " + ele.text

    tokens_so_far = 0
    for c in chunks:
        token_ids = tokenize(c.text)
        chunk_start = tokens_so_far
        chunk_end = tokens_so_far + len(token_ids)
        tokens_so_far = chunk_end
        c.start_token = chunk_start
        c.end_token = chunk_end
    return chunks


if __name__ == "__main__":
    # url = "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/"
    url = "https://www.fool.com/earnings/call-transcripts/2019/10/30/apple-inc-aapl-q4-2019-earnings-call-transcript.aspx"
    # url = "https://www.fool.com/earnings/call-transcripts/2023/01/26/tesla-tsla-q4-2022-earnings-call-transcript/"
    chunks = iterate_elements(url)
    # for chunk in chunks:
    #     print("Chunk:", chunk.chunk_id)
    #     print("Primary Speakers:", chunk.primary_speakers)
    #     print("Participants:", chunk.participants)
    #     print(chunk.text[:500], "\n")
    print(chunks)
