import os

from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

HOST_URL = "https://needle-earnings-transcripts-e38g0na.svc.aped-4627-b74a.pinecone.io"
INDEX_NAME = "needle-earnings-transcripts"

load_dotenv()


class PineconeClient:
    def __init__(self):
        self.index = self.init_index()

    def init_index(self, index_name=INDEX_NAME):
        pc = Pinecone(api_key=os.getenv("PINECONE_DEFAULT_API_KEY"))
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
            host="https://needle-earnings-transcripts-e38g0na.svc.aped-4627-b74a.pinecone.io"
        )
        return index

    def query_search(self, query_embedding):
        result = self.index.query(
            vector=query_embedding, top_k=5, include_metadata=True, include_values=False
        )
        return result
