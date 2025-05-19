import time

from fastapi import HTTPException, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI

from .cache import LRUCache
from .logger import get_logger
from .services.openai_service import fetch_embeddings, generate_llm_response
from .services.pinecone_service import query_index

from .model.searchQuery import SearchQuery
from .model.searchResponse import SearchResponse, Snippet

from .client.pineconeClient import PineconeClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from common.load_tickers import load_ticker_metadata

logger = get_logger("needle-backend")
load_dotenv()
OAI_client = None
pinecone_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.pinecone_client = PineconeClient(logger)
    logger.info(
        "Pinecone client initialized", extra={"client": app.state.pinecone_client}
    )
    app.state.oai_client = OpenAI()
    logger.info("OpenAI client initialized", extra={"client": app.state.oai_client})
    app.state.ticker_metadata = load_ticker_metadata()
    logger.info(
        "Loaded ticker metadata into memory",
        extra={"num_companies": len(app.state.ticker_metadata)},
    )
    app.state.embeddings_cache = LRUCache()
    app.state.llm_response_cache = LRUCache()
    yield
    # Shutdown


app = FastAPI(lifespan=lifespan)

origins = [
    "https://needle-semantic-search.vercel.app",
    "https://needle-semantic-search.vercel.app/",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthz():
    """Health check endpoint used for monitoring."""
    return {"status": "ok"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "Request started", extra={"method": request.method, "url": str(request.url)}
    )
    response = await call_next(request)
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
        },
    )
    return response


@app.get("/metadata")
def metadata():
    companies = dict(
        sorted({v["name"]: k for k, v in app.state.ticker_metadata.items()}.items())
    )
    return {
        "companies": companies,
        "quarters": [],
    }


@app.post("/search")
def search(request: Request, response: Response, query: SearchQuery) -> SearchResponse:
    start = time.perf_counter()
    logger.info("Semantic search query received", extra={"query": query})
    if not query.query:
        raise HTTPException(status_code=422, detail="Invalid query")

    openai_client = request.app.state.oai_client
    pinecone_client = request.app.state.pinecone_client
    assert pinecone_client is not None, "Pinecone client not initialized"
    assert openai_client is not None, "OpenAI client not initialized"

    embeddings_cache = request.app.state.embeddings_cache
    embedding, embeddings_cache = fetch_embeddings(
        openai_client, query.query, logger, embeddings_cache
    )
    app.state.embeddings_cache = embeddings_cache

    # Get 3-5 best results
    top_k_results = query_index(pinecone_client, logger, embedding, query.filters)
    if not top_k_results:
        logger.debug("No grouped results.")
        raise HTTPException(status_code=204, detail="No search results found")

    llm_response_cache = request.app.state.llm_response_cache
    answer, llm_response_cache = generate_llm_response(
        openai_client, logger, query.query, top_k_results, llm_response_cache
    )
    app.state.llm_response_cache = llm_response_cache

    request_time = time.perf_counter() - start
    logger.info(
        "Returning semantic search results",
        extra={"request_time": request_time},
    )
    return SearchResponse(
        answer=answer,
        snippets=[
            Snippet(
                company=sr.metadata.company,
                quarter=sr.metadata.quarter,
                year=sr.metadata.year,
                url=sr.metadata.url,
                participants={
                    sp.name: sp.role if sp.role else sp.type
                    for sp in sr.metadata.participants
                },
                section=sr.metadata.section,
                text=sr.metadata.snippet,
            )
            for sr in top_k_results
        ],
    )
