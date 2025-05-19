import sys
import types

# stub external deps
sys.modules["openai"] = types.ModuleType("openai")
sys.modules["openai"].OpenAI = object
sys.modules["pinecone"] = types.ModuleType("pinecone")
sys.modules["pinecone"].Pinecone = object
sys.modules["pinecone"].ServerlessSpec = object

from .main import healthz


def test_healthz():
    assert healthz() == {"status": "ok"}
