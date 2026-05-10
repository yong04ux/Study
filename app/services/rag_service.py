"""RAG 检索服务占位实现。

当前完整 RAG 问答逻辑在 rag_qa_service.py 中。
保留本文件是为了让项目结构清楚地区分“检索服务”和“问答编排服务”。
"""


class RagService:
    """封装 Chroma 向量检索逻辑的服务类。"""

    async def retrieve(self, query: str) -> list[str]:
        """
        返回占位检索结果。

        未来可以在这里直接调用 Chroma，根据 query 返回相关知识片段。
        """
        _ = query
        return ["mock_knowledge_chunk"]
