"""Agent 相关接口的请求/响应模型。

Pydantic 模型的作用是：
1. 约束接口入参和出参的数据结构。
2. 自动做基础校验。
3. 让 Swagger 文档更清晰。
"""

from typing import Optional

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Agent 聊天接口的请求体。"""

    question: str = Field(..., description="User's study or application question.")
    student_score: Optional[int] = Field(
        default=None,
        description="Student score, used by future recommendation logic.",
    )
    province: Optional[str] = Field(
        default=None,
        description="Province of the student, used for regional policy lookup.",
    )
    subject_type: Optional[str] = Field(
        default=None,
        description="Exam category such as physics or history track.",
    )


class AgentChatResponse(BaseModel):
    """Agent 聊天接口的响应体。"""

    answer: str = Field(..., description="Natural language answer from the agent.")
    workflow: str = Field(..., description="Workflow name used to process the request.")
    data_source: list[str] = Field(
        default_factory=list,
        description="Knowledge sources consulted by the current workflow.",
    )
