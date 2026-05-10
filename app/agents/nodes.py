"""高考志愿推荐工作流中的单一职责节点。

每个函数就是 LangGraph 中的一个 Agent 节点：
1. 只读取自己需要的 State 字段。
2. 只返回自己负责更新的字段。
3. 不直接调用下一个节点，节点顺序由 graph.py 统一编排。
"""

from __future__ import annotations

from typing import Any

from app.agents.state import GaokaoState

MAX_CHOICES_PER_BUCKET = 5

# 推荐演示兜底数据。
# 只有当数据库没有足够的院校专业候选项时，school_retrieval_node 才会使用它。
FALLBACK_SCHOOL_POOL: list[dict[str, Any]] = [
    {
        "school_name": "华夏科技大学",
        "major_name": "计算机科学与技术",
        "province": "北京",
        "city": "北京",
        "min_score": 638,
        "min_rank": 9600,
        "is_985": True,
        "is_211": True,
        "is_double_first_class": True,
    },
    {
        "school_name": "东海大学",
        "major_name": "软件工程",
        "province": "上海",
        "city": "上海",
        "min_score": 633,
        "min_rank": 10800,
        "is_985": True,
        "is_211": True,
        "is_double_first_class": True,
    },
    {
        "school_name": "南岭信息工程大学",
        "major_name": "软件工程",
        "province": "广东",
        "city": "广州",
        "min_score": 625,
        "min_rank": 12100,
        "is_985": False,
        "is_211": False,
        "is_double_first_class": True,
    },
    {
        "school_name": "珠江理工学院",
        "major_name": "计算机科学与技术",
        "province": "广东",
        "city": "深圳",
        "min_score": 620,
        "min_rank": 14900,
        "is_985": False,
        "is_211": False,
        "is_double_first_class": False,
    },
    {
        "school_name": "岭南财经大学",
        "major_name": "金融学",
        "province": "广东",
        "city": "广州",
        "min_score": 606,
        "min_rank": 21000,
        "is_985": False,
        "is_211": False,
        "is_double_first_class": False,
    },
    {
        "school_name": "西部交通大学",
        "major_name": "土木工程",
        "province": "四川",
        "city": "成都",
        "min_score": 622,
        "min_rank": 13200,
        "is_985": False,
        "is_211": True,
        "is_double_first_class": True,
    },
    {
        "school_name": "江南师范大学",
        "major_name": "数学与应用数学",
        "province": "江苏",
        "city": "南京",
        "min_score": 614,
        "min_rank": 17600,
        "is_985": False,
        "is_211": True,
        "is_double_first_class": False,
    },
    {
        "school_name": "北辰工业大学",
        "major_name": "电气工程及其自动化",
        "province": "天津",
        "city": "天津",
        "min_score": 603,
        "min_rank": 22600,
        "is_985": False,
        "is_211": True,
        "is_double_first_class": False,
    },
    {
        "school_name": "云岭民族大学",
        "major_name": "工商管理",
        "province": "云南",
        "city": "昆明",
        "min_score": 589,
        "min_rank": 28400,
        "is_985": False,
        "is_211": False,
        "is_double_first_class": False,
    },
]


def score_analysis_node(state: GaokaoState) -> dict[str, Any]:
    """成绩分析节点：根据分数判断整体报考层次和风险提示。

    输入：score。
    输出：score_analysis。
    说明：这里先用简单分数段规则，后续可以接入省控线、一分一段表和同位分。
    """
    score = state["score"]

    if score >= 640:
        level = "高分冲刺型"
        summary = "当前分数具备冲击更高层次院校的空间，但需要关注专业冷热和位次波动。"
        suggestion = "建议保持冲稳保结构完整，优先保证稳妥层和保底层的录取确定性。"
    elif score >= 600:
        level = "均衡匹配型"
        summary = "当前分数适合采用冲刺、稳妥、保底相结合的方案，整体以均衡填报为主。"
        suggestion = "建议优先围绕偏好地区和专业做匹配，再根据分差控制风险。"
    else:
        level = "稳妥保底型"
        summary = "当前更适合把录取稳定性放在前面，同时保留少量可尝试的冲刺志愿。"
        suggestion = "建议适度收缩冲刺范围，把更多名额留给稳妥和保底院校。"

    return {
        "score_analysis": {
            "level": level,
            "summary": summary,
            "suggestion": suggestion,
        }
    }


def school_retrieval_node(state: GaokaoState) -> dict[str, Any]:
    """院校检索节点：提供后续推荐节点使用的候选院校专业池。

    输入：retrieved_schools。
    输出：retrieved_schools。
    说明：RecommendationService 会先尝试从 MySQL 放入候选项；
    如果为空，这里使用 mock 数据兜底，保证工作流可运行。
    """
    if state["retrieved_schools"]:
        return {"retrieved_schools": state["retrieved_schools"]}
    return {"retrieved_schools": list(FALLBACK_SCHOOL_POOL)}


def recommendation_node(state: GaokaoState) -> dict[str, Any]:
    """志愿推荐节点：把候选院校专业分成冲刺、稳妥、保底三类。

    输入：score、preferred_provinces、preferred_majors、retrieved_schools。
    输出：recommended_choices。
    推荐规则：
    - 冲刺：最低分比用户高 0 到 15 分。
    - 稳妥：最低分比用户低 0 到 20 分。
    - 保底：最低分比用户低 20 到 50 分。
    """
    preferred_provinces = {item.strip() for item in state["preferred_provinces"] if item.strip()}
    preferred_majors = {item.strip().lower() for item in state["preferred_majors"] if item.strip()}
    user_score = state["score"]

    buckets: dict[str, list[dict[str, Any]]] = {
        "rush": [],
        "stable": [],
        "safe": [],
    }
    scored_candidates: list[tuple[int, int, dict[str, Any], str]] = []

    for school in state["retrieved_schools"]:
        min_score = int(school["min_score"])
        bucket = _classify_bucket(user_score=user_score, min_score=min_score)
        if bucket is None:
            continue

        # 地区和专业偏好不强制过滤，而是用于排序加权：匹配越多，越靠前。
        province_match = not preferred_provinces or school["province"] in preferred_provinces
        major_match = not preferred_majors or _major_matches(str(school["major_name"]), preferred_majors)
        preference_score = int(province_match) + int(major_match)
        score_gap = abs(min_score - user_score)
        scored_candidates.append((preference_score, -score_gap, school, bucket))

    scored_candidates.sort(
        key=lambda item: (
            -item[0],
            -item[1],
            item[2]["school_name"],
            item[2]["major_name"],
        )
    )

    for preference_score, _, school, bucket in scored_candidates:
        if len(buckets[bucket]) >= MAX_CHOICES_PER_BUCKET:
            continue
        buckets[bucket].append(
            {
                "school_id": school.get("school_id"),
                "major_id": school.get("major_id"),
                "school_name": school["school_name"],
                "major_name": school["major_name"],
                "province": school["province"],
                "city": school.get("city"),
                "min_score": int(school["min_score"]),
                "min_rank": int(school["min_rank"]) if school.get("min_rank") is not None else None,
                "is_985": bool(school.get("is_985")),
                "is_211": bool(school.get("is_211")),
                "is_double_first_class": bool(school.get("is_double_first_class")),
                "reason": _build_reason(
                    bucket=bucket,
                    user_score=user_score,
                    min_score=int(school["min_score"]),
                    province_match=bool(
                        not preferred_provinces or school["province"] in preferred_provinces
                    ),
                    major_match=bool(
                        not preferred_majors or _major_matches(str(school["major_name"]), preferred_majors)
                    ),
                    preference_score=preference_score,
                ),
            }
        )

    return {"recommended_choices": buckets}


def study_plan_node(state: GaokaoState) -> dict[str, Any]:
    """学习规划节点：根据推荐结构生成后续行动建议。

    输入：recommended_choices。
    输出：study_plan。
    说明：当前是简化版文本生成，后续可结合薄弱科目、目标专业要求做个性化规划。
    """
    choices = state["recommended_choices"]
    rush_count = len(choices.get("rush", []))
    stable_count = len(choices.get("stable", []))
    safe_count = len(choices.get("safe", []))

    plan = (
        f"建议以“{rush_count} 个冲刺、{stable_count} 个稳妥、{safe_count} 个保底”的结构来准备正式填报。"
        "接下来两周优先复盘高频失分点，保持模拟训练节奏，并同步核对目标院校最新招生计划和选科要求。"
    )
    return {"study_plan": plan}


def final_response_node(state: GaokaoState) -> dict[str, Any]:
    """最终总结节点：把前面节点的结果汇总为一段综合建议。

    输入：score_analysis、recommended_choices。
    输出：final_answer。
    """
    analysis = state["score_analysis"]
    choices = state["recommended_choices"]

    final_answer = (
        f"根据你当前的分数与位次，整体更适合“{analysis['level']}”方案。"
        f"本次共生成 {len(choices['rush'])} 条冲刺、{len(choices['stable'])} 条稳妥、"
        f"{len(choices['safe'])} 条保底推荐。建议正式填报前再次核对院校近年录取波动和最新招生规则。"
    )
    return {"final_answer": final_answer}


def _classify_bucket(*, user_score: int, min_score: int) -> str | None:
    """按用户分数和历年最低分差值，判断属于冲刺/稳妥/保底哪一档。"""
    diff = min_score - user_score
    if 0 <= diff <= 15:
        return "rush"
    if -20 <= diff <= 0:
        return "stable"
    if -50 <= diff < -20:
        return "safe"
    return None


def _major_matches(major_name: str, preferred_majors: set[str]) -> bool:
    """用宽松的子串匹配判断专业偏好，适合“计算机”匹配“计算机科学与技术”。"""
    normalized = major_name.strip().lower()
    return any(
        preferred_major in normalized or normalized in preferred_major
        for preferred_major in preferred_majors
    )


def _build_reason(
    *,
    bucket: str,
    user_score: int,
    min_score: int,
    province_match: bool,
    major_match: bool,
    preference_score: int,
) -> str:
    """为单个院校专业组合生成可解释的推荐理由。"""
    diff = min_score - user_score
    bucket_label = {
        "rush": "适合作为冲刺志愿",
        "stable": "适合作为稳妥志愿",
        "safe": "适合作为保底志愿",
    }[bucket]

    parts = [f"{bucket_label}，该专业近年最低分与当前分数相差 {diff:+d} 分"]
    if province_match:
        parts.append("符合你的地区偏好")
    if major_match:
        parts.append("符合你的专业偏好")
    if preference_score == 0:
        parts.append("可作为补充备选项")
    return "；".join(parts)
