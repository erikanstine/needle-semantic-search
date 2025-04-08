import os

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from typing import List

from model import TranscriptChunk


load_dotenv()
OAI_client = OpenAI()
pc = Pinecone(api_key=os.getenv("PINECONE_DEFAULT_API_KEY"))


def get_embedding(text):
    response = OAI_client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding


def flatten_speakers(speakers):
    return {
        "names": [s.name for s in speakers],
        "types": [s.type for s in speakers],
        "roles": [s.role if s.role else None for s in speakers],
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


def ingest_chunks(chunks: List[TranscriptChunk]):
    index = get_index(pc)
    for chunk in chunks:
        embedding = get_embedding(chunk.text)
        metadata = {
            "section": chunk.section,
            "company": chunk.company,
            "quarter": chunk.quarter,
            **{  # AI madness
                f"primary_{k}": v
                for k, v in flatten_speakers(chunk.primary_speakers).items()
            },
            **{  # AI madness
                f"participant_{k}": v
                for k, v in flatten_speakers(chunk.participants).items()
            },
        }
        if chunk.snippet:
            metadata["snippet"] = chunk.snippet
        if chunk.start_token:
            metadata["start_token"] = chunk.start_token
        if chunk.end_token:
            metadata["end_token"] = chunk.end_token
        index.upsert([(chunk.chunk_id, embedding, metadata)])
        print("Upserted chunk", chunk.chunk_id)

    return
