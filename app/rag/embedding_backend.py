"""Embedding 后端适配器。

RAG 检索依赖 embedding 向量，本模块支持两种方式：
1. 远程 OpenAI 兼容 embedding API。
2. 本地 sentence-transformers 模型。
"""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from app.core.config import settings
from app.core.llm import build_embedding_client


@lru_cache(maxsize=4)
def _load_sentence_transformer(model_name: str, device: str):
    """
    懒加载本地 embedding 模型，并在进程内缓存。

    本地模型通常较大，因此只在真正使用 local provider 时导入和加载，
    避免影响普通 API 启动速度。
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Local embeddings require sentence-transformers. Run `pip install -r requirements.txt` first."
        ) from exc

    resolved_device = device.strip() or "cpu"
    return SentenceTransformer(model_name_or_path=model_name, device=resolved_device)


class EmbeddingBackend:
    """统一封装远程 API 和本地模型两种 embedding 生成方式。"""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.provider = settings.resolved_embedding_provider
        self._remote_client: OpenAI | None = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """根据配置把 embedding 请求路由到本地模型或远程 API。"""
        if self.provider == "local":
            return self._embed_with_local_model(texts)
        return self._embed_with_remote_api(texts)

    def _embed_with_local_model(self, texts: list[str]) -> list[list[float]]:
        """使用本地 sentence-transformer 模型编码文本。"""
        model = _load_sentence_transformer(
            model_name=self.model_name,
            device=settings.local_embedding_device,
        )
        embeddings = model.encode(
            texts,
            normalize_embeddings=settings.local_embedding_normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def _embed_with_remote_api(self, texts: list[str]) -> list[list[float]]:
        """调用远程 OpenAI 兼容 embedding API 生成向量。"""
        api_key = settings.resolved_embedding_api_key
        if not api_key or api_key == "your-openai-api-key":
            raise ValueError(
                "EMBEDDING_API_KEY or OPENAI_API_KEY is required before building or querying the vector database."
            )

        if self._remote_client is None:
            self._remote_client = build_embedding_client()

        response = self._remote_client.embeddings.create(
            model=self.model_name,
            input=texts,
        )
        return [item.embedding for item in response.data]
