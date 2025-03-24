from fastapi import HTTPException, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI

from .logger import get_logger
from .services.openai_service import fetch_embeddings, summarize_snippets_with_llm
from .services.pinecone_service import query_index

from .model.searchQuery import SearchQuery
from .model.searchResponse import SearchResponse, SearchResult

from .client.pineconeClient import PineconeClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv

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


@app.post("/search")
def search(request: Request, response: Response, query: SearchQuery) -> SearchResponse:
    logger.info("Semantic search query received", extra={"query": query})
    if not query.query:
        raise HTTPException(status_code=422, detail="Invalid query")
    openai_client = request.app.state.oai_client
    pinecone_client = request.app.state.pinecone_client

    assert pinecone_client is not None, "Pinecone client not initialized"
    assert openai_client is not None, "OpenAI client not initialized"

    embedding = fetch_embeddings(openai_client, query.query, logger)
    grouped_search_results = query_index(
        pinecone_client, logger, embedding, query.filters
    )
    if not grouped_search_results:
        logger.debug("No grouped results.")
        response.status_code = status.HTTP_204_NO_CONTENT
        return SearchResponse(results=[])
    search_results = []
    for result in grouped_search_results:
        r = summarize_snippets_with_llm(openai_client, logger, query.query, result)
        if not r:
            continue
        search_results.append(r)

    logger.info(
        "Returning semantic search results", extra={"result_count": len(search_results)}
    )
    return SearchResponse(results=search_results)
