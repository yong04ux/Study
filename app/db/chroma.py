"""Chroma 向量数据库客户端工厂。

Chroma 用于保存 RAG 文档切分后的向量，问答时根据用户问题检索相似片段。
"""

import chromadb
from chromadb.api import ClientAPI

from app.core.config import settings


def get_chroma_client() -> ClientAPI:
    """创建持久化 Chroma 客户端，数据会保存在配置的本地目录中。"""
    return chromadb.PersistentClient(path=settings.chroma_persist_directory)
