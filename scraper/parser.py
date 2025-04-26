import re
import tiktoken

from bs4 import BeautifulSoup, Tag
from dateutil import parser as dateutil_parser
from dateutil.tz import gettz
from typing import List, Tuple

from exceptions import PageFormatNotImplementedException, ParserInitializationError
from utils.storage import TranscriptKey
from storage import save_unhandled_title
from model import Speaker, TranscriptChunk


class Parser:
    def __init__(self, soup: BeautifulSoup, key: TranscriptKey, url: str):
        self.soup = soup
        self.url = url
        self.key = key
        self.participant_map = {}
        self.current_step = 0
        self.call_stages = ["prepared_remarks", "qa"]
        self.chunk_count = 0
        self.chunks: List[TranscriptChunk] = []
        self.company = key.company
        self.quarter = key.quarter
        self.year = key.year
        self.timestamp = None
        self.init()

    def init(self):
        self.timestamp = self.parse_timestamp()

    @classmethod
    def from_html(cls, html: str, key: TranscriptKey, url: str) -> "Parser":
        try:
            soup = BeautifulSoup(html, "html.parser")
            soup = cls.clean_ads(soup)
            if not soup.find("div", class_="article-body"):
                raise ParserInitializationError(
                    f"Missing expected article body block for {key.slug()}", key=key
                )
            return cls(soup, key, url)
        except Exception as e:
            raise ParserInitializationError(f"Error parsing {key.slug()}: {e}", key=key)

    @staticmethod
    def tokenize(text: str) -> List[int]:
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode(text)

    @staticmethod
    def clean_ads(soup: BeautifulSoup) -> BeautifulSoup:
        for a in soup.find_all("div", {"data-pitch-placement": True}):
            a.decompose()
        return soup

    @staticmethod
    def parse_speaker(t: Tag) -> Speaker:
        name = t.strong.text
        inner_text = t.text.lower()
        _type = ""
        role = ""

        if "president and chief executive officer" in inner_text:
            role = "President"
            _type = "executive"
        elif "chief executive officer" in inner_text:
            role = "CEO"
            _type = "executive"
        elif "chief technology officer" in inner_text:
            role = "CTO"
            _type = "executive"
        elif "chief financial officer" in inner_text:
            role = "CFO"
            _type = "executive"
        elif "chief operating officer" in inner_text:
            role = "COO"
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
            if "chief" in inner_text and "officer" in inner_text:
                title = t.em.text.strip()
                print(f"NEW SPEAKER TITLE: {inner_text}\nParsed title: {title}")
                save_unhandled_title(inner_text)
                role = title
                _type = "executive"
            else:
                _type = "other"
        return Speaker(name=name, type=_type, role=role if role else "")

    def parse_speakers(self, speakers: List[Speaker]) -> List[Speaker]:
        if len(speakers) == 1:
            return speakers

        return [s for s in speakers if s.type == "executive"]

    def get_chunk_id(self, section, n: str) -> str:
        return f"{self.key.company.lower()}-{self.key.quarter}-{self.key.year}-{section}-{n}"

    def parse_timestamp(self) -> Tuple[str, str]:
        d = self.soup.find("span", id="date").text
        tm = self.soup.find("em", id="time").text
        tzinfos = {"ET": gettz("America/New_York")}
        dt = dateutil_parser.parse(d + ", " + tm, tzinfos=tzinfos)
        return dt.isoformat()

    def populate_participant_map(self, t: Tag):
        d = {}
        participants = t.find("h2", string="Call participants:").find_next_siblings("p")
        for p in participants:
            if not p.strong:
                continue
            speaker = self.parse_speaker(p)
            d[speaker.name] = speaker
        self.participant_map = d

    def save_chunk(
        self, current_speakers: List[Speaker], current_text: str
    ) -> TranscriptChunk:
        self.chunks.append(
            TranscriptChunk(
                chunk_id=self.get_chunk_id(
                    self.call_stages[self.current_step],
                    len(self.chunks),
                ),
                url=self.url,
                section=self.call_stages[self.current_step],
                company=self.company,
                quarter=self.quarter,
                year=str(self.year),
                primary_speakers=self.parse_speakers(current_speakers),
                participants=current_speakers,
                text=current_text,
                call_ts=self.timestamp,
            )
        )

    def add_token_counts(self):
        tokens_so_far = 0
        for c in self.chunks:
            token_ids = self.tokenize(c.text)
            chunk_start = tokens_so_far
            chunk_end = tokens_so_far + len(token_ids)
            tokens_so_far = chunk_end
            c.start_token = chunk_start
            c.end_token = chunk_end

    def iterate_elements(self):
        article_body = self.soup.find("div", class_="article-body")
        self.populate_participant_map(article_body)
        current_speakers = []
        current_text = ""

        """
        Start no 'current step'
        Switch on h2: None -> Prepared remarks -> Q&A, different behavior
        """
        if not any(
            [
                article_body.find("h2", string="Questions & Answers:")
                or article_body.find("h2", string="Questions and Answers:")
            ]
        ):
            raise PageFormatNotImplementedException("Format not implemented")

        for ele in article_body.find(
            "h2", string="Prepared Remarks:"
        ).find_next_siblings():
            match self.call_stages[self.current_step]:
                case "prepared_remarks":
                    if ele.name == "h2":
                        if "call participants" in ele.text.lower():
                            break
                        if current_speakers:
                            self.save_chunk(current_speakers, current_text)
                            current_text = ""
                            current_speakers = []

                        self.current_step += 1
                        continue

                    if ele.name == "p":
                        if ele.find("strong"):
                            # Change in speaker
                            # Save off chunk
                            if current_speakers:
                                self.save_chunk(current_speakers, current_text)
                                current_text = ""
                                current_speakers = []

                            # Get new speaker
                            current_speaker = self.parse_speaker(ele)
                            if current_speaker.type in [
                                "operator",
                                "investor relations",
                            ]:
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
                                self.save_chunk(current_speakers, current_text)
                            break
                        print("Unexpected <h2>:", ele.text)
                    """
                    Split into full Q/A exchanges, add participants as they happen
                    """
                    if ele.name == "p":
                        if ele.find("strong"):
                            current_speaker = self.parse_speaker(ele)
                            if "Duration:" in current_speaker.name:
                                current_speaker = None
                                continue
                            if current_speaker.type in [
                                "operator",
                                "investor relations",
                            ]:
                                # If operator AND current_speakers, save off chunk
                                if current_speakers:
                                    self.save_chunk(current_speakers, current_text)

                                current_speaker = None
                                current_speakers = []
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

    def parse_html(self) -> List[TranscriptChunk]:
        self.iterate_elements()
        self.add_token_counts()
        return self.chunks


# parse sequence
#   - Read in HTML from filesystem
#   - Parse HTML
#   - Produce Chunks, push to pipeline

# ingest sequence
#   - "Chunkify" into optimal /embedding requests
#   - Retrieve embeddings from OAI /embedding
#   - Zip together
#   - "Chunkify" into optimal size for indexing
