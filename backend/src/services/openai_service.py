import hashlib
import time

from ..cache import LRUCache
from logging import Logger
from openai import OpenAI
from typing import Dict, List, Tuple

from ..model.pineconeQueryResponse import PineconeSearchResult


def fetch_embeddings(
    oai_client: OpenAI, search_query: str, logger: Logger, cache: LRUCache
):
    logger.debug("Fetching query embeddings.")
    start = time.perf_counter()
    hashed_query = hashlib.sha256(search_query.encode("utf-8")).hexdigest()
    cached_embedding = cache.get(hashed_query)
    if cached_embedding:
        embedding = cached_embedding
    else:
        response = oai_client.embeddings.create(
            input=search_query, model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        cache.set(hashed_query, embedding)
    request_time = time.perf_counter() - start
    logger.info("Fetched query embeddings.", extra={"request_time": request_time})

    return embedding, cache


def get_prompt(query: str, results: List[PineconeSearchResult]) -> str:
    def list_out_results(results: List[PineconeSearchResult]) -> str:
        return "\n".join(
            [
                f"""
                Excerpt {i+1}
                    - Speaker(s): {", ".join([f"{sp.name}, {sp.role}" for sp in r.metadata.primary_speakers])}
                    - Company: {r.metadata.company}
                    - Quarter: {r.metadata.quarter}, {r.metadata.year} -- Call occurred at {r.metadata.call_ts}
                    - Section: {"Question & Answer" if r.metadata.section == "qa" else r.metadata.section}
                    - Snippet: {r.metadata.snippet}
                """
                for i, r in enumerate(results)
            ]
        )

    return f"""
    You are an expert financial analyst specializing in summarizing earnings call transcripts. Your goal is to answer the user's query clearly, precisely, and concisely using ONLY the provided excerpts from earnings calls.

    User's Query:
    "{query}"

    Earnings Call Excerpts:
    {list_out_results(results)}

    Using ONLY the excerpts provided above, synthesize a clear and concise summary (1-2 sentences) that directly addresses the user's query. Your summary should:
    - Be factual, capturing key points directly from excerpts.
    - Speakers labeled as Analysts, or anyone asking questions in the Q&A are typically NOT members of the company.
    - Clearly address the query.
    - Avoid speculation or information not supported by excerpts.
    - Maintain professional, neutral, financial analyst tone.
    - Match the scope of the user's query: if it is broad, answer in a similar vein. Likewise narrow scope. For example:
        Query "Who was talking about supply chain disruption" should result in an answer mentioning multiple companies or people discussing supply chain disruption.
        Query "What was Apple's AI chip strategy in 2024" should result in an answer specifically about information/exceprts from 2024 about Apple's AI chip strategy.
    """


def parse_summary(summary: str) -> list[str]:
    bullet_points = summary.strip("- ").split("\n-")
    return [bp.strip() for bp in bullet_points]


def summarize_snippets_with_llm(
    oai_client: OpenAI,
    logger: Logger,
    search_query: str,
    top_k_results: List[PineconeSearchResult],
) -> str:
    prompt = get_prompt(search_query, top_k_results)

    start = time.perf_counter()
    completion = oai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "user", "content": prompt.strip()},
        ],
    )
    request_time = time.perf_counter() - start
    llm_response = completion.choices[0].message.content.strip()
    if "No directly relevant insights found." == llm_response:
        logger.info("Transcript not relevant", extra={"request_time": request_time})
        return None
    logger.info(
        "Transcript successfully summarized",
        extra={"request_time": request_time},
    )
    return llm_response
