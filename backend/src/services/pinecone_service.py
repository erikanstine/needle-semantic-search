from ..client.pineconeClient import PineconeClient
from ..model.pineconeQueryResponse import PineconeSearchResult
from ..model.searchResponse import SearchResult


def group_results(results: list[PineconeSearchResult]) -> list[SearchResult]:
    groups = {}
    scores = {}
    for r in results:
        document = r.metadata.document
        if document not in groups:
            groups[document] = SearchResult(
                company=r.metadata.company,
                quarter=str(r.metadata.quarter),
                url=r.metadata.url,
                document=r.metadata.document,
                snippets=[],
            )
            scores[document] = []
        groups[document].snippets.append(r.metadata.snippet)
        scores[document].append(r.score)

    doc_order = sorted(groups.keys(), key=lambda doc: max(scores[doc]), reverse=True)
    return [groups[doc_id] for doc_id in doc_order]


def query_index(
    pinecone_client: PineconeClient, query_embedding, filters
) -> list[SearchResult]:
    results = pinecone_client.query_search(query_embedding, filters).to_dict()

    pinecone_matches = [PineconeSearchResult(**sr) for sr in results["matches"]]
    matches = group_results(pinecone_matches)

    return matches
