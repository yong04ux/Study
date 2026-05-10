"""Tests for recommendation node logic."""

from app.agents.nodes import recommendation_node, score_analysis_node


def test_score_analysis_node_balanced_match() -> None:
    """Score analysis should return the fixed frontend fields."""
    result = score_analysis_node({"score": 625, "rank": 12000})  # type: ignore[arg-type]

    assert result["score_analysis"]["level"] == "均衡匹配型"
    assert result["score_analysis"]["summary"]
    assert result["score_analysis"]["suggestion"]


def test_recommendation_node_buckets_and_reasons() -> None:
    """Recommendation node should split candidates into rush, stable, and safe."""
    state = {
        "score": 625,
        "preferred_provinces": ["广东"],
        "preferred_majors": ["软件工程"],
        "retrieved_schools": [
            {
                "school_name": "冲刺大学",
                "province": "北京",
                "city": "北京",
                "major_name": "软件工程",
                "min_score": 638,
                "min_rank": 9800,
                "is_985": True,
                "is_211": True,
                "is_double_first_class": True,
            },
            {
                "school_name": "稳妥大学",
                "province": "广东",
                "city": "广州",
                "major_name": "软件工程",
                "min_score": 612,
                "min_rank": 14000,
                "is_985": False,
                "is_211": False,
                "is_double_first_class": True,
            },
            {
                "school_name": "保底大学",
                "province": "广东",
                "city": "深圳",
                "major_name": "信息管理",
                "min_score": 585,
                "min_rank": 26000,
                "is_985": False,
                "is_211": False,
                "is_double_first_class": False,
            },
        ],
    }

    result = recommendation_node(state)  # type: ignore[arg-type]
    choices = result["recommended_choices"]

    assert len(choices["rush"]) == 1
    assert len(choices["stable"]) == 1
    assert len(choices["safe"]) == 1
    assert choices["rush"][0]["school_name"] == "冲刺大学"
    assert "冲刺志愿" in choices["rush"][0]["reason"]
    assert "地区偏好" in choices["stable"][0]["reason"]
    assert choices["safe"][0]["city"] == "深圳"
