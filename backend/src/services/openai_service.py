from openai import OpenAI


def fetch_embeddings(oai_client: OpenAI, search_query: str):
    response = oai_client.embeddings.create(
        input=search_query, model="text-embedding-3-small"
    )
    return response.data[0].embedding
