"""Agent 问答业务服务。

这个服务目前是轻量封装，用来演示 API 不直接调用 LangGraph，
而是通过 Service 层统一组织业务流程。
"""

from app.agents.graph import GaokaoAgentGraph
from app.schemas.agent import AgentChatRequest, AgentChatResponse


class AgentService:
    """封装 Agent 工作流，让 API handler 保持简单。"""

    def __init__(self) -> None:
        self.graph = GaokaoAgentGraph()

    async def chat(self, payload: AgentChatRequest) -> AgentChatResponse:
        """
        处理用户问题并调用占位 Agent 工作流。

        后续如果要把成绩分析、院校检索、推荐生成和报告生产统一到聊天入口，
        可以继续在这个方法里扩展编排逻辑。
        """
        result = await self.graph.run(question=payload.question)
        return AgentChatResponse(
            answer=result["answer"],
            workflow=result["workflow"],
            data_source=result["data_source"],
        )
