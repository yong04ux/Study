"""Tests for RAG vector retrieval."""

from app.rag.text_splitter import TextChunk
from app.rag.vector_store import ChromaVectorStore


def test_chroma_similarity_search_with_fake_embeddings(monkeypatch, tmp_path) -> None:
    """Vector store should retrieve the most semantically similar chunk."""

    def fake_embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            if "parallel volunteer" in text.lower():
                embeddings.append([1.0, 0.0, 0.0])
            elif "computer science" in text.lower():
                embeddings.append([0.0, 1.0, 0.0])
            else:
                embeddings.append([0.0, 0.0, 1.0])
        return embeddings

    monkeypatch.setattr(ChromaVectorStore, "_embed_texts", fake_embed_texts)

    store = ChromaVectorStore(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_gaokao_rag",
        embedding_model="fake-model",
    )
    store.add_documents(
        [
            TextChunk(
                content="Parallel volunteer admission follows score priority and ordered choices.",
                metadata={"source": "policy.md", "filename": "policy.md", "chunk_index": 0},
            ),
            TextChunk(
                content="Computer science focuses on programming, systems, data, and algorithms.",
                metadata={"source": "major.md", "filename": "major.md", "chunk_index": 0},
            ),
        ]
    )

    results = store.similarity_search("What does parallel volunteer mean?", top_k=1)

    assert len(results) == 1
    assert "Parallel volunteer" in results[0]["content"]
    assert results[0]["metadata"]["filename"] == "policy.md"
