from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm


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
