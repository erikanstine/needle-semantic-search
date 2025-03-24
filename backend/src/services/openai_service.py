import time

from logging import Logger
from openai import OpenAI
from typing import Optional

from ..model.searchResponse import SearchResult, SummarizedSearchResult


def fetch_embeddings(oai_client: OpenAI, search_query: str, logger: Logger):
    logger.debug("Fetching query embeddings.")
    start = time.perf_counter()
    response = oai_client.embeddings.create(
        input=search_query, model="text-embedding-3-small"
    )
    request_time = time.perf_counter() - start
    logger.info("Fetched query embeddings.", extra={"request_time": request_time})

    return response.data[0].embedding


def get_prompt(query: str, result: SearchResult) -> str:
    snippets = "\n".join(result.snippets[:5])
    return f"""
    You are an expert financial analyst. Your goal is to concisely summarize key insights from recent earnings calls for {result.company} relevant to the user's query.

    Query:
    "{query}"

    Earnings Call Excerpts:
    - {snippets}

    Instructions:
    - Clearly summarize insights directly related to the query.
    - Use short bullet points.
    - Focus explicitly on financial metrics, guidance, risks, growth indicators, management comments, or strategic shifts mentioned.
    - Omit irrelevant or general information.
    - If no directly relevant information is found, respond clearly with "No directly relevant insights found."
    """


def parse_summary(summary: str) -> list[str]:
    bullet_points = summary.strip("- ").split("\n-")
    return [bp.strip() for bp in bullet_points]


def summarize_snippets_with_llm(
    oai_client: OpenAI, logger: Logger, search_query: str, search_result: SearchResult
) -> Optional[SummarizedSearchResult]:
    prompt = get_prompt(search_query, search_result)

    start = time.perf_counter()
    completion = oai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "user", "content": prompt.strip()},
        ],
    )
    request_time = time.perf_counter() - start
    summarized_text = completion.choices[0].message.content.strip()
    if "No directly relevant insights found." == summarized_text:
        logger.info("Transcript not relevant", extra={"request_time": request_time})
        return None
    logger.info(
        "Transcript successfully summarized",
        extra={"request_time": request_time},
    )
    return SummarizedSearchResult(
        company=search_result.company,
        quarter=search_result.quarter,
        year=search_result.year,
        url=search_result.url,
        summary=parse_summary(summarized_text),
    )
