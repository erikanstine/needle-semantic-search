import os

from dotenv import load_dotenv
from logging import Logger
from pinecone import Pinecone, ServerlessSpec

from ..model.pineconeQueryResponse import PineconeSearchResult

load_dotenv()

HOST_URL = os.getenv("PINECONE_HOST_URL")
# INDEX_NAME = "needle-earnings-transcripts"
INDEX_NAME = "transcripts-v2"


class PineconeClient:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.index = self.init_index()

    def init_index(self, index_name: str = INDEX_NAME) -> Pinecone:
        pc = Pinecone(api_key=os.getenv("PINECONE_DEFAULT_API_KEY"))
        if not pc.has_index(index_name):
            self.logger.info("Pinecone index not found, creating new")
            pc.create_index(
                name=index_name,
                vector_type="dense",
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                deletion_protection="disabled",
                tags={"environment": "development"},
            )
        index = pc.Index(host=HOST_URL)
        self.logger.info(
            "Pinecone index initiated.",
            extra={"index_name": index_name, "index_url": HOST_URL},
        )
        return index

    def query_search(self, query_embedding, filters) -> list[PineconeSearchResult]:
        def build_filter(filters):
            f = {}
            if not filters:
                return f
            if filters.company:
                f["company"] = filters.company
            if filters.quarter:
                quarter, year = filters.quarter.split(" ")
                f["quarter"] = quarter.lstrip("Q")
                f["year"] = year
            if filters.section:
                f["section"] = filters.section
            return f

        result = self.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            include_values=False,
            filter=build_filter(filters),
        )
        self.logger.info(
            "Pinecone query returned", extra={"result_count": len(result.matches)}
        )
        return result
