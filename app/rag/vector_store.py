"""Chroma 向量库封装。

该模块负责把切分后的文本块写入 Chroma，并在问答时做相似度检索。
EmbeddingBackend 把“远程 OpenAI 兼容接口”和“本地 embedding 模型”统一起来。
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.rag.embedding_backend import EmbeddingBackend
from app.rag.text_splitter import TextChunk


class ChromaVectorStore:
    """管理本地持久化 Chroma collection，支持写入和相似度搜索。"""

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_model = embedding_model or settings.resolved_embedding_model
        # 将 embedding 生成封装在适配器后面，方便在远程 API 和本地免费模型之间切换。
        self.embedding_backend = EmbeddingBackend(model_name=self.embedding_model)
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection: Collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Gaokao knowledge base for RAG."},
        )

    def count(self) -> int:
        """返回当前 collection 中已经存储的文本块数量。"""
        return int(self.collection.count())

    def add_documents(self, chunks: list[TextChunk]) -> int:
        """
        添加或更新文本块到 Chroma。

        使用 upsert 可以让构建向量库脚本重复执行：
        相同来源、相同序号、相同内容会得到相同 ID，因此会覆盖而不是重复插入。
        """
        if not chunks:
            return 0

        documents = [chunk.content for chunk in chunks]
        metadatas = [dict(chunk.metadata) for chunk in chunks]
        ids = [self._build_chunk_id(chunk) for chunk in chunks]
        embeddings = self._embed_texts(documents)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return len(chunks)

    def reset_collection(self) -> None:
        """删除并重建当前配置的 Chroma collection，用于全量重建向量库。"""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Gaokao knowledge base for RAG."},
        )

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """根据用户问题做向量相似度检索，返回最相关的 top_k 个文本块。"""
        if not query.strip():
            raise ValueError("query cannot be blank.")
        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_embedding = self._embed_texts([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matches: list[dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            matches.append(
                {
                    "content": document,
                    "metadata": metadata,
                    "distance": distance,
                }
            )
        return matches

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量调用当前配置的 embedding 后端，把文本转换成向量。"""
        return self.embedding_backend.embed_texts(texts)

    @staticmethod
    def _build_chunk_id(chunk: TextChunk) -> str:
        """根据来源、chunk 序号和内容生成稳定 ID，保证重复入库可覆盖。"""
        source = chunk.metadata.get("source", "unknown")
        chunk_index = chunk.metadata.get("chunk_index", "0")
        raw_id = f"{source}:{chunk_index}:{chunk.content}"
        return hashlib.sha1(raw_id.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def get_shared_vector_store() -> ChromaVectorStore:
    """复用同一个 ChromaVectorStore 实例，避免每次问答都重新初始化。"""
    return ChromaVectorStore()
