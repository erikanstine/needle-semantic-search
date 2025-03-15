import json

from fastapi import FastAPI
from openai import OpenAI

from model.searchResponse import SearchResponse
from model.pineconeQueryResponse import PineconeQueryResponse, SearchResult

from client.pineconeClient import PineconeClient
from dotenv import load_dotenv

load_dotenv()
OAI_client = OpenAI()
pinecone_client = PineconeClient()

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello world"}


@app.get("/search")
def search(q: str) -> SearchResponse:
    embedding = fetch_embeddings(q)
    search_results = query_index(embedding)
    return SearchResponse(results=search_results)


def fetch_embeddings(search_query: str):
    response = OAI_client.embeddings.create(
        input=search_query, model="text-embedding-3-small"
    )
    return response.data[0].embedding


def query_index(query_embedding) -> list[SearchResult]:
    result = pinecone_client.query_search(query_embedding).to_dict()
    matches = [SearchResult(**sr) for sr in result["matches"]]

    return matches
