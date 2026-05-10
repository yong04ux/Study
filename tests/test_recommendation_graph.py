"""Smoke test for the full recommendation graph."""

import asyncio

from app.agents.graph import GaokaoAgentGraph


def test_recommendation_graph_generates_all_sections() -> None:
    """Full graph should produce analysis, choices, plan, and final answer."""
    state = {
        "user_id": "u001",
        "province": "广东",
        "subject_type": "物理类",
        "score": 625,
        "rank": 12000,
        "preferred_provinces": ["广东", "北京", "上海"],
        "preferred_majors": ["计算机科学与技术", "软件工程"],
        "score_analysis": {},
        "retrieved_schools": [],
        "recommended_choices": {"rush": [], "stable": [], "safe": []},
        "study_plan": "",
        "final_answer": "",
    }

    result = asyncio.run(GaokaoAgentGraph().generate_recommendation(state))

    assert set(result["score_analysis"].keys()) == {"level", "summary", "suggestion"}
    assert isinstance(result["recommended_choices"]["rush"], list)
    assert isinstance(result["recommended_choices"]["stable"], list)
    assert isinstance(result["recommended_choices"]["safe"], list)
    assert isinstance(result["study_plan"], str)
    assert isinstance(result["final_answer"], str)
