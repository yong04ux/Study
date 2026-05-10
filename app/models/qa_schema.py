"""RAG 智能问答 API 的 Pydantic 模型。"""

from pydantic import BaseModel, Field


class QaAskRequest(BaseModel):
    """POST /qa/ask 的请求体。"""

    question: str = Field(..., min_length=2, max_length=500, description="User question.")
    province: str = Field(..., min_length=1, max_length=32, description="Candidate province.")
    subject_type: str = Field(..., min_length=1, max_length=32, description="Subject type.")
    use_llm: bool = Field(default=True, description="Whether to call the LLM after retrieval.")
    conversation_id: str | None = Field(
        default=None, max_length=64, description="Optional conversation ID for multi-turn context."
    )


class QaSource(BaseModel):
    """回答引用的一个检索片段，前端可用它展示来源。"""

    title: str | None = Field(default=None, description="Display title for the source.")
    content: str = Field(..., description="Retrieved document chunk.")
    filename: str | None = Field(default=None, description="Source file name.")
    source: str | None = Field(default=None, description="Source file path.")
    chunk_index: int | None = Field(default=None, description="Chunk index in the source file.")
    distance: float | None = Field(default=None, description="Vector distance returned by Chroma.")
    score: float | None = Field(default=None, description="Optional relevance score.")


class QaAskResponse(BaseModel):
    """POST /qa/ask 的响应结构：答案 + 引用来源。"""

    answer: str = Field(..., description="Generated answer.")
    sources: list[QaSource] = Field(default_factory=list, description="Retrieved document chunks.")
