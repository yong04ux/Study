"""大模型客户端工厂函数。

这里不直接在模块导入时创建客户端，而是按需构建。
这样可以减少应用启动时的副作用，也方便后续替换不同模型提供商。
"""

from openai import OpenAI

from app.core.config import settings


def build_llm_client() -> OpenAI:
    """创建聊天模型客户端。"""
    return OpenAI(
        api_key=settings.resolved_llm_api_key,
        base_url=settings.resolved_llm_base_url,
        timeout=settings.llm_timeout_seconds,
    )


def build_embedding_client() -> OpenAI:
    """创建 embedding 模型客户端。"""
    return OpenAI(
        api_key=settings.resolved_embedding_api_key,
        base_url=settings.resolved_embedding_base_url,
    )
