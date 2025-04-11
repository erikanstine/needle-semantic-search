import os

from openai import OpenAI
from pinecone import Pinecone

from dotenv import load_dotenv
from more_itertools import chunked
from typing import Any, List

from ingest import get_embeddings, upsert_chunks
from model import TranscriptChunk
from utils.pinecone import get_index

EMBED_BATCH_SIZE = 512
UPSERT_BATCH_SIZE = 100


class ChunkProcessor:
    def __init__(self, chunks: List[TranscriptChunk]):
        self.chunks = chunks
        self.embeddings = []
        self.OAI_client = None
        self.index = None
        self.embeddings = []

        self.init()

    def init(self):
        load_dotenv()
        self.OAI_client = OpenAI()
        pc = Pinecone(api_key=os.getenv("PINECONE_DEFAULT_API_KEY"))
        self.index = get_index(pc)

    def embed(self, batch_size: int = EMBED_BATCH_SIZE):
        for chunk_batch in chunked(self.chunks, batch_size):
            texts = [chunk.text for chunk in chunk_batch]
            embeddings = get_embeddings(texts, self.OAI_client)
            self.embeddings.extend(embeddings)

    def upsert(self, batch_size: int = UPSERT_BATCH_SIZE):
        for chunk_batch, embed_batch in zip(
            chunked(self.chunks, batch_size), chunked(self.embeddings, batch_size)
        ):
            upsert_chunks(chunk_batch, embed_batch, self.index)

    def report(self):
        pass
