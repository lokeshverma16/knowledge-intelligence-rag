"""
Unit-test the RAG engine in isolation by stubbing out the retriever and the
LLM. No network calls, no OpenAI key needed.
"""
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.services import rag_engine as rag_engine_module


class _FakeRetriever:
    def __init__(self, docs):
        self._docs = docs

    def invoke(self, _query):
        return self._docs


def _fake_llm(reply: str):
    """Build a Runnable that pretends to be ChatOpenAI."""
    return RunnableLambda(lambda prompt: AIMessage(content=reply))


def test_query_returns_citations(app, monkeypatch):
    docs = [
        Document(
            page_content="Remote work is allowed up to 3 days a week.",
            metadata={"source_url": "s3://bucket/handbook.pdf", "page": 14},
        ),
        Document(
            page_content="Core hours are 10am-3pm.",
            metadata={"source_url": "s3://bucket/handbook.pdf", "page": 15},
        ),
    ]
    monkeypatch.setattr(
        rag_engine_module.vector_db_service,
        "get_retriever",
        lambda **_: _FakeRetriever(docs),
    )

    engine = rag_engine_module.RAGEngine()
    engine._llm = _fake_llm(
        "Remote work is allowed 3 days a week "
        "(Source: s3://bucket/handbook.pdf, Page: 14)."
    )

    with app.app_context():
        result = engine.query("What is the remote work policy?")

    assert "Remote work" in result["answer"]
    assert len(result["citations"]) == 2
    assert result["citations"][0]["source"] == "s3://bucket/handbook.pdf"
    assert result["citations"][0]["page"] == 14


def test_query_handles_empty_retrieval(app, monkeypatch):
    monkeypatch.setattr(
        rag_engine_module.vector_db_service,
        "get_retriever",
        lambda **_: _FakeRetriever([]),
    )

    engine = rag_engine_module.RAGEngine()
    with app.app_context():
        result = engine.query("anything")

    assert result["citations"] == []
    assert "don't have enough information" in result["answer"]
