from ..client.pineconeClient import PineconeClient
from ..model.searchResponse import SearchResult


def query_index(
    pinecone_client: PineconeClient, query_embedding, filters
) -> list[SearchResult]:
    result = pinecone_client.query_search(query_embedding, filters).to_dict()
    matches = [SearchResult(**sr) for sr in result["matches"]]

    return matches
