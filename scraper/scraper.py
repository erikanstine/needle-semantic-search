import re
import requests
import tiktoken

from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import List, Tuple
from model import Speaker, TranscriptChunk, PageFormatNotImplementedException
from dateutil import parser
from dateutil.tz import gettz


def tokenize(text: str) -> List[int]:
    encoding = tiktoken.get_encoding("cl100k_base")
    return encoding.encode(text)


class Scraper:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.company = None
        self.quarter = None
        self.timestamp = None
        self.participant_map = {}
        self.current_step = 0
        self.call_stages = ["prepared_remarks", "qa"]
        self.chunk_count = 0
        self.chunks = []
        self.init()

    def init(self):
        resp = requests.get(self.url)
        soup = BeautifulSoup(resp.text, "html.parser")
        self.soup = self.clean_ads(soup)
        self.company, self.quarter, self.timestamp = self.parse_metadata()

    @staticmethod
    def clean_ads(soup: BeautifulSoup) -> BeautifulSoup:
        ads = soup.find_all("div", {"data-pitch-placement": True})
        [a.decompose() for a in ads]
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

    @staticmethod
    def get_chunk_id(company, quarter, section, n: str) -> str:
        q, y = quarter.lower().split(" ")
        return f"{company.lower()}-{q}-{y}-{section}-{n}"

    def parse_metadata(self) -> Tuple[str, str]:
        t = self.soup.find("h1").text
        reg = r".+ \((\w+)\) (Q\d \d{4}) Earnings Call Transcript"
        ticker, quarter = re.search(reg, t).groups()
        d = self.soup.find("span", id="date").text
        tm = self.soup.find("em", id="time").text
        tzinfos = {"ET": gettz("America/New_York")}
        dt = parser.parse(d + ", " + tm, tzinfos=tzinfos)
        timestamp = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        return ticker, quarter, timestamp

    def populate_participant_map(self, t: Tag):
        d = {}
        participants = t.find("h2", string="Call participants:").find_next_siblings("p")
        for p in participants:
            if not p.strong:
                continue
            speaker = self.parse_speaker(p)
            d[speaker.name] = speaker
        self.participant_map = d

    def parse_speakers(self, speakers: List[Speaker], curr_stage: str) -> List[Speaker]:
        if len(speakers) == 1:
            return speakers

        return [s for s in speakers if s.type == "executive"]

    def save_chunk(
        self, current_speakers: List[Speaker], current_text: str
    ) -> TranscriptChunk:
        self.chunks.append(
            TranscriptChunk(
                chunk_id=self.get_chunk_id(
                    self.company,
                    self.quarter,
                    self.call_stages[self.current_step],
                    len(self.chunks),
                ),
                url=self.url,
                section=self.call_stages[self.current_step],
                company=self.company,
                quarter=self.quarter,
                primary_speakers=self.parse_speakers(
                    current_speakers, self.call_stages[self.current_step]
                ),
                participants=current_speakers,
                text=current_text,
                call_ts=self.timestamp,
            )
        )

    def add_token_counts(self):
        tokens_so_far = 0
        for c in self.chunks:
            token_ids = tokenize(c.text)
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

    def scrape(self) -> Tuple[List[TranscriptChunk], dict]:
        self.iterate_elements()
        self.add_token_counts()
        call_metadata = {"company": self.company, "quarter": self.quarter}
        return self.chunks, call_metadata


if __name__ == "__main__":
    # url = "https://www.fool.com/earnings/call-transcripts/2024/11/20/nvidia-nvda-q3-2025-earnings-call-transcript/"
    # url = "https://www.fool.com/earnings/call-transcripts/2019/10/30/apple-inc-aapl-q4-2019-earnings-call-transcript.aspx"
    url = "https://www.fool.com/earnings/call-transcripts/2023/01/26/tesla-tsla-q4-2022-earnings-call-transcript/"

    scraper = Scraper(url)

    chunks, _ = scraper.scrape()
    for chunk in chunks:
        print("Chunk:", chunk.chunk_id)
        print("Primary Speakers:", chunk.primary_speakers)
        print("Participants:", chunk.participants)
        print(chunk.text[:500], "\n")
    # print(chunks)
