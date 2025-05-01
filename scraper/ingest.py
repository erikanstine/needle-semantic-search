import os

from openai import OpenAI
from pinecone import Index, Pinecone, ServerlessSpec
from dotenv import load_dotenv
from typing import Any, Dict, List

from model import TranscriptChunk
from more_itertools import chunked
from utils.time_util import time_block


load_dotenv()
OAI_client = OpenAI()
pc = Pinecone(api_key=os.getenv("PINECONE_DEFAULT_API_KEY"))


def get_embeddings(
    texts: List[str], oai_client: OpenAI = OAI_client
) -> List[List[float]]:
    if not texts:
        return []
    response = oai_client.embeddings.create(input=texts, model="text-embedding-3-small")
    sorted_embeddings = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_embeddings]


def upsert_chunks(
    chunks: List[TranscriptChunk], embeddings: list[list[float]], index: Index
):
    index.upsert(
        [
            {"id": chunk.chunk_id, "values": emb, "metadata": get_chunk_metadata(chunk)}
            for chunk, emb in zip(chunks, embeddings)
        ]
    )


def upsert_chunks_in_batches(
    chunks: List[TranscriptChunk],
    embeddings: List[List[float]],
    index: Index,
    batch_size: int = 100,
):
    pairs = list(zip(chunks, embeddings))
    for batch in chunked(pairs, batch_size):
        index.upsert(
            [
                {
                    "id": chunk.chunk_id,
                    "values": emb,
                    "metadata": get_chunk_metadata(chunk),
                }
                for chunk, emb in batch
            ]
        )


def flatten_speakers(speakers):
    return {
        "names": [s.name for s in speakers],
        "types": [s.type for s in speakers],
        "roles": [s.role for s in speakers if s.role],
    }


def get_index(pc: Pinecone):
    index_name = "transcripts-v2"
    if not pc.has_index(index_name):
        print("Index not found, creating new")
        pc.create_index(
            name=index_name,
            vector_type="dense",
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            deletion_protection="disabled",
            tags={"environment": "development"},
        )
    index = pc.Index(
        host="https://transcripts-v2-e38g0na.svc.aped-4627-b74a.pinecone.io"
    )
    return index


def get_chunk_metadata(chunk: TranscriptChunk) -> dict[str, Any]:
    metadata = {
        "url": chunk.url,
        "section": chunk.section,
        "company": chunk.company,
        "quarter": chunk.quarter,
        "year": chunk.year,
        "snippet": chunk.snippet,
        "call_ts": chunk.call_ts,
        **{  # AI madness
            f"primary_{k}": v
            for k, v in flatten_speakers(chunk.primary_speakers).items()
        },
        **{  # AI madness
            f"participant_{k}": v
            for k, v in flatten_speakers(chunk.participants).items()
        },
    }
    if chunk.start_token:
        metadata["start_token"] = chunk.start_token
    if chunk.end_token:
        metadata["end_token"] = chunk.end_token
    return metadata


def ingest_chunks(chunks: List[TranscriptChunk]) -> Dict[str, Any]:
    index = get_index(pc)
    texts = [chunk.text for chunk in chunks]
    embeddings = get_embeddings(texts)
    upsert_chunks(chunks, embeddings, index)

    chunk = chunks[0]
    metadata = {
        "company": chunk.company,
        "quarter": chunk.quarter,
        "call_ts": chunk.call_ts,
        "processed": True,
    }
    print("Upserted embeddings for", chunk.company, chunk.quarter)
    return metadata
