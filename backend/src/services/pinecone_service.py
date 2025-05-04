from ..client.pineconeClient import PineconeClient
from ..model.pineconeQueryResponse import ChunkMetadata, PineconeSearchResult, Speaker
from ..model.searchQuery import Filter
from ..model.searchResponse import SearchResult

from logging import Logger
from typing import List
from pydantic_core import ValidationError


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
                company=r.metadata.company,
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


def normalize_filters(filter: List[Filter]) -> List[Filter]:
    f = Filter()
    if filter.company:
        f.company = filter.company.lower()
    if filter.quarter:
        f.quarter = filter.quarter
    if filter.section:
        f.section = filter.section
    return f


def query_index(
    pinecone_client: PineconeClient, logger: Logger, query_embedding, filters
) -> list[PineconeSearchResult]:
    norm_filter = normalize_filters(filters)
    results = pinecone_client.query_search(query_embedding, norm_filter).to_dict()

    def parse_metadata(m: dict) -> ChunkMetadata:
        filtered_keys = [
            "participant_names",
            "participant_roles",
            "participant_types",
            "primary_names",
            "primary_roles",
            "primary_types",
        ]

        def get_speakers(s: str, m: dict) -> List[Speaker]:
            return [
                Speaker(name=n, type=t, role=r)
                for n, t, r in zip(m[f"{s}_names"], m[f"{s}_roles"], m[f"{s}_types"])
            ]

        chunk_metadata = None
        try:
            participants = get_speakers("participant", m)
            primary_speakers = get_speakers("primary", m)
            chunk_metadata = ChunkMetadata(
                **{k: v for k, v in m.items() if k not in filtered_keys},
                participants=participants,
                primary_speakers=primary_speakers,
            )
        except ValidationError as e:
            print(f"Validation error for {m}:", e)

        return chunk_metadata

    pinecone_matches = [
        PineconeSearchResult(
            id=sr["id"], score=sr["score"], metadata=parse_metadata(sr["metadata"])
        )
        for sr in results["matches"]
    ]

    return pinecone_matches
