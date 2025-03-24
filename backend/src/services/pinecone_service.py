from ..client.pineconeClient import PineconeClient
from ..model.pineconeQueryResponse import PineconeSearchResult
from ..model.searchResponse import SearchResult

from logging import Logger


def map_company_name(company: str) -> str:
    c_name_map = {"Amazoncom": "Amazon"}
    if company in c_name_map:
        return c_name_map[company]
    return company


def group_results(
    results: list[PineconeSearchResult], logger: Logger, threshold: float = 0.4
) -> list[SearchResult]:
    groups = {}
    scores = {}
    qualified_results = [res for res in results if res.score > threshold]
    if not qualified_results:
        scores = [r.score for r in results]
        logger.info(
            "No closely matching results",
            extra={"threshold": threshold, "scores": scores},
        )
        return []
    for r in qualified_results:
        document = r.metadata.document
        if document not in groups:
            groups[document] = SearchResult(
                company=map_company_name(r.metadata.company),
                quarter=str(r.metadata.quarter),
                year=str(r.metadata.year),
                url=r.metadata.url,
                document=r.metadata.document,
                snippets=[],
            )
            scores[document] = []
        groups[document].snippets.append(r.metadata.snippet)
        scores[document].append(r.score)
        logger.debug(
            "Parsing result",
            extra={
                "score": r.score,
                "year": r.metadata.year,
                "quarter": r.metadata.quarter,
                "snippet": r.metadata.snippet,
            },
        )

    doc_order = sorted(groups.keys(), key=lambda doc: max(scores[doc]), reverse=True)
    return [groups[doc_id] for doc_id in doc_order]


def query_index(
    pinecone_client: PineconeClient, logger: Logger, query_embedding, filters
) -> list[SearchResult]:
    results = pinecone_client.query_search(query_embedding, filters).to_dict()
    pinecone_matches = [PineconeSearchResult(**sr) for sr in results["matches"]]

    matches = group_results(pinecone_matches, logger)

    return matches
