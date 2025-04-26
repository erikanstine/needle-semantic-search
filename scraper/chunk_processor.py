import os

from openai import OpenAI
from pinecone import Pinecone

from dotenv import load_dotenv
from more_itertools import chunked
from tqdm import tqdm
from typing import Any, Iterable, List

from ingest import get_embeddings, upsert_chunks
from model import TranscriptChunk
from utils.pinecone import get_index
from utils.time_util import now_utc_iso

EMBED_BATCH_TOKEN_LIMIT = 7500
UPSERT_BATCH_SIZE = 100


class ChunkProcessor:
    def __init__(self, chunks: List[TranscriptChunk]):
        self.chunks = chunks
        self.embeddings = []
        self.OAI_client = None
        self.index = None
        self.embeddings = []
        self.report = {}
        self.successful_slugs = set()
        self.failed_slugs = set()
        self.init()

    def init(self):
        load_dotenv()
        self.OAI_client = OpenAI()
        pc = Pinecone(api_key=os.getenv("PINECONE_DEFAULT_API_KEY"))
        self.index = get_index(pc)

    def embed(self, batch_token_limit: int = EMBED_BATCH_TOKEN_LIMIT):
        self.report["embed_started_at"] = now_utc_iso()

        def create_batches_by_token(
            chunks: List[TranscriptChunk], max_tokens
        ) -> Iterable[List[TranscriptChunk]]:
            batch = []
            batch_tokens = 0
            for chunk in chunks:
                num_tokens = (chunk.end_token or 0) - (chunk.start_token or 0)
                if num_tokens > max_tokens:
                    # Special case: chunk is too large even by itself
                    print(
                        f"⚠️ Chunk {chunk.chunk_id} too large ({num_tokens} tokens) — skipping"
                    )
                    self.failed_slugs.add(chunk.transcript_key_slug())
                    continue

                if batch_tokens + num_tokens > max_tokens:
                    if batch:
                        yield batch
                    batch = []
                    batch_tokens = 0
                batch.append(chunk)
                batch_tokens += num_tokens

            if batch:
                yield batch

        with tqdm(desc="🧠 Embedding chunks", total=len(self.chunks)) as pbar:
            for chunk_batch in create_batches_by_token(self.chunks, batch_token_limit):
                texts = [chunk.text for chunk in chunk_batch]
                try:
                    embeddings = get_embeddings(texts, self.OAI_client)
                    self.embeddings.extend(embeddings)
                    for chunk in chunk_batch:
                        self.successful_slugs.add(chunk.transcript_key_slug())
                except Exception as e:
                    print(f"⚠️ Failed to embed batch: {e}")
                    for chunk in chunk_batch:
                        self.failed_slugs.add(chunk.transcript_key_slug())
                pbar.update(len(chunk_batch))

    def upsert(self, batch_size: int = UPSERT_BATCH_SIZE, dry_run: bool = False):
        self.report["upsert_started_at"] = now_utc_iso()
        with tqdm(desc="📦 Upserting vectors", total=len(self.embeddings)) as pbar:
            for chunk_batch, embed_batch in zip(
                chunked(self.chunks, batch_size), chunked(self.embeddings, batch_size)
            ):
                try:
                    if not dry_run:
                        upsert_chunks(chunk_batch, embed_batch, self.index)
                    for chunk in chunk_batch:
                        self.successful_slugs.add(chunk.transcript_key_slug())
                except Exception as e:
                    print(f"⚠️ Failed to upsert batch: {e}")
                    for chunk in chunk_batch:
                        self.failed_slugs.add(chunk.transcript_key_slug())
                pbar.update(len(chunk_batch))

    def get_report(self):
        return {
            "embed_started_at": self.report.get("embed_started_at"),
            "upsert_started_at": self.report.get("upsert_started_at"),
            "successful_slugs": list(self.successful_slugs),
            "failed_slugs": list(self.failed_slugs),
            "total_chunks": len(self.chunks),
        }

    def get_successful_slugs(self):
        """Return the set of successful slugs."""
        return self.successful_slugs

    def get_failed_slugs(self):
        """Return the set of failed slugs."""
        return self.failed_slugs
