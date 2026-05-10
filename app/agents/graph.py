"""LangGraph 多 Agent 志愿推荐工作流。

本文件只负责编排顺序，不写具体业务规则。
每个节点的职责在 nodes.py 中实现，这样方便面试时说明“编排”和“业务”分离。
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    final_response_node,
    recommendation_node,
    school_retrieval_node,
    score_analysis_node,
    study_plan_node,
)
from app.agents.state import GaokaoState


class GaokaoAgentGraph:
    """编译并运行高考志愿推荐多 Agent 工作流。"""

    def __init__(self) -> None:
        # StateGraph 表示所有节点共享同一个 GaokaoState。
        workflow = StateGraph(GaokaoState)
        # 每个节点都是一个单一职责 Agent：成绩分析、院校检索、推荐、规划、总结。
        workflow.add_node("score_analysis_agent", score_analysis_node)
        workflow.add_node("school_retrieval_agent", school_retrieval_node)
        workflow.add_node("recommendation_agent", recommendation_node)
        workflow.add_node("study_plan_agent", study_plan_node)
        workflow.add_node("final_response_agent", final_response_node)

        # 固定顺序：START -> 成绩分析 -> 院校检索 -> 推荐 -> 学习规划 -> 总结 -> END。
        workflow.add_edge(START, "score_analysis_agent")
        workflow.add_edge("score_analysis_agent", "school_retrieval_agent")
        workflow.add_edge("school_retrieval_agent", "recommendation_agent")
        workflow.add_edge("recommendation_agent", "study_plan_agent")
        workflow.add_edge("study_plan_agent", "final_response_agent")
        workflow.add_edge("final_response_agent", END)

        self.app = workflow.compile()

    async def generate_recommendation(self, state: GaokaoState) -> GaokaoState:
        """运行完整推荐图，输入初始 State，输出被各节点补全后的 State。"""
        return await self.app.ainvoke(state)

    async def run(self, question: str) -> dict[str, Any]:
        """兼容旧版占位聊天接口，提示调用正式推荐接口。"""
        return {
            "answer": (
                "Recommendation workflow is ready. "
                "Use POST /recommendations/generate for multi-agent recommendation."
            ),
            "workflow": "recommendation_graph_ready",
            "data_source": ["langgraph_recommendation_workflow"],
            "question": question,
        }
