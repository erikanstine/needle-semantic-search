from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI

from .model.searchQuery import SearchQuery
from .model.searchResponse import SearchResponse
from .model.pineconeQueryResponse import SearchResult

from .client.pineconeClient import PineconeClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()
OAI_client = None
pinecone_client = None


@asynccontextmanager
async def lifesppan(app: FastAPI):
    # Startup
    pinecone_client = PineconeClient()
    OAI_client = OpenAI()
    print("startup")

    yield
    # Shutdown


app = FastAPI()

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


@app.post("/search")
def search(query: SearchQuery) -> SearchResponse:
    embedding = fetch_embeddings(query.query)
    search_results = query_index(embedding, query.filters)
    return SearchResponse(results=search_results)


def fetch_embeddings(search_query: str):
    response = OAI_client.embeddings.create(
        input=search_query, model="text-embedding-3-small"
    )
    return response.data[0].embedding


def query_index(query_embedding, filters) -> list[SearchResult]:
    result = pinecone_client.query_search(query_embedding, filters).to_dict()
    matches = [SearchResult(**sr) for sr in result["matches"]]

    return matches
