"""Agent 问答占位 API。

该接口用于演示 API -> Service -> AgentGraph 的调用层次。
完整志愿推荐逻辑目前由 /recommendations/generate 承担。
"""

from fastapi import APIRouter

from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(payload: AgentChatRequest) -> AgentChatResponse:
    """
    POST /api/v1/agent/chat：接收用户问题，并委托 AgentService 处理。

    当前主要用于保留项目骨架，方便后续把更多 Agent 能力接入统一聊天入口。
    """
    return await agent_service.chat(payload)
