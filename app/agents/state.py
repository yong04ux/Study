"""LangGraph 志愿推荐流程的共享状态定义。

LangGraph 的核心思想是：每个节点只处理自己的任务，
节点之间不直接传很多参数，而是共同读写一个 State。
GaokaoState 就是整个多 Agent 工作流中的“数据接力棒”。
"""

from typing import Any, TypedDict


class GaokaoState(TypedDict):
    """多 Agent 节点之间传递的统一状态对象。

    字段分为两类：
    - 用户输入：user_id、province、subject_type、score、rank、preferred_*。
    - 节点产出：score_analysis、retrieved_schools、recommended_choices、study_plan、final_answer。
    """

    # 用户基础信息，用于区分请求和生成个性化推荐。
    user_id: str
    # 考生所在省份，不同省份分数线和招生计划不同。
    province: str
    # 科类，例如物理类、历史类、理科、文科。
    subject_type: str
    # 高考分数，是推荐规则中最核心的匹配条件。
    score: int
    # 全省位次，比裸分更稳定，后续可用于更精细推荐。
    rank: int
    # 用户偏好的就读地区，用于排序加权。
    preferred_provinces: list[str]
    # 用户偏好的专业方向，用于筛选和推荐理由生成。
    preferred_majors: list[str]
    # 成绩分析节点输出，例如分数层次、风险建议。
    score_analysis: dict[str, Any]
    # 院校检索节点输出，保存候选院校和专业组合。
    retrieved_schools: list[dict[str, Any]]
    # 推荐节点输出，按 rush/stable/safe 三档组织。
    recommended_choices: dict[str, list[dict[str, Any]]]
    # 学习规划节点输出，给出备考或后续行动建议。
    study_plan: str
    # 最终总结节点输出，用于页面顶部或问答总结展示。
    final_answer: str
