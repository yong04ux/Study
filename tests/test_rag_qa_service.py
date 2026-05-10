"""Tests for the RAG QA service."""

from app.models.qa_schema import QaAskRequest
from app.services.rag_qa_service import (
    MISSING_LLM_CONFIG_ERROR,
    RagQaService,
)


def test_rag_qa_service_uses_fallback_sources_when_vector_store_empty(monkeypatch) -> None:
    """The QA service should still return sources when Chroma is empty."""

    class EmptyVectorStore:
        def count(self) -> int:
            return 0

    service = RagQaService()
    service._vector_store = EmptyVectorStore()  # type: ignore[assignment]
    monkeypatch.setattr(
        RagQaService,
        "_generate_answer",
        lambda self, prompt: "这是基于 fallback 文档生成的回答。",
    )

    response = service.ask(
        QaAskRequest(
            question="平行志愿是什么意思？",
            province="广东",
            subject_type="物理类",
        )
    )

    assert response.answer == "这是基于 fallback 文档生成的回答。"
    assert response.sources
    assert response.sources[0].source and response.sources[0].source.startswith("fallback://")


def test_rag_qa_service_returns_insufficient_message_for_blank_sources() -> None:
    """Blank sources should trigger the insufficient-info answer."""

    class BrokenVectorStore:
        def count(self) -> int:
            return 1

        def similarity_search(self, query: str, top_k: int = 4):
            return [
                {
                    "content": "   ",
                    "metadata": {"filename": "empty.md", "source": "empty.md", "chunk_index": 0},
                    "distance": 0.1,
                }
            ]

    service = RagQaService()
    service._vector_store = BrokenVectorStore()  # type: ignore[assignment]

    response = service.ask(
        QaAskRequest(
            question="这是什么意思？",
            province="广东",
            subject_type="物理类",
        )
    )

    assert "当前知识库暂未收录详细资料" in response.answer


def test_rag_qa_service_returns_clear_error_when_api_key_missing(monkeypatch) -> None:
    """Missing LLM credentials should return a readable configuration error."""

    service = RagQaService()
    monkeypatch.setattr("app.services.rag_qa_service.settings.llm_api_key", "")
    monkeypatch.setattr("app.services.rag_qa_service.settings.openai_api_key", "")

    try:
        service._generate_answer("test prompt")
    except ValueError as exc:
        assert str(exc) == MISSING_LLM_CONFIG_ERROR
    else:
        raise AssertionError("Expected ValueError for missing API key.")


def test_rag_qa_service_supports_retrieval_only_debug_mode() -> None:
    """use_llm=false should skip the LLM call and return retrieval excerpts."""

    class ReadyVectorStore:
        def count(self) -> int:
            return 1

        def similarity_search(self, query: str, top_k: int = 4):
            return [
                {
                    "content": "平行志愿遵循分数优先、遵循志愿的原则。",
                    "metadata": {"filename": "policy.md", "source": "policy.md", "chunk_index": 0},
                    "distance": 0.1,
                }
            ]

    service = RagQaService()
    service._vector_store = ReadyVectorStore()  # type: ignore[assignment]

    response = service.ask(
        QaAskRequest(
            question="平行志愿是什么意思？",
            province="广东",
            subject_type="物理类",
            use_llm=False,
        )
    )

    assert "已关闭 LLM 调用" in response.answer
    assert "平行志愿遵循分数优先" in response.answer
