import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI

from model.searchQuery import SearchQuery
from model.searchResponse import SearchResponse
from model.pineconeQueryResponse import PineconeQueryResponse, SearchResult

from client.pineconeClient import PineconeClient
from dotenv import load_dotenv

load_dotenv()
OAI_client = OpenAI()
pinecone_client = PineconeClient()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
