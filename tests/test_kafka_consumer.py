"""Tests for Kafka report consumer task handling."""

from __future__ import annotations

import json

from app.mq import kafka_consumer


class FakeRedis:
    """Minimal Redis stub that records report payloads by key."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def setex(self, key: str, _: int, value: str) -> None:
        self.values[key] = value


class FakeRecommendationService:
    """Async recommendation stub used by the consumer."""

    async def recommend(self, **_: object) -> dict[str, object]:
        return {
            "score_analysis": {
                "level": "稳中有冲",
                "summary": "当前分数适合冲稳保搭配。",
                "suggestion": "优先保留偏好地区中的计算机相关专业。",
            },
            "recommended_choices": {
                "rush": [],
                "stable": [],
                "safe": [],
            },
            "study_plan": "按批次整理志愿顺序，并核对招生章程。",
            "final_answer": "建议按照冲稳保 1:2:2 的思路填报。",
        }


def test_handle_task_writes_completed_report_result() -> None:
    """The consumer should store a completed report with the fixed result schema."""

    redis_client = FakeRedis()
    recommendation_service = FakeRecommendationService()
    task = {
        "task_id": "task-001",
        "user_id": "frontend-user",
        "province": "广东",
        "subject_type": "物理类",
        "score": 625,
        "rank": 12000,
        "preferred_provinces": ["广东", "北京"],
        "preferred_majors": ["计算机科学与技术"],
    }

    import asyncio

    asyncio.run(kafka_consumer.handle_task(redis_client, recommendation_service, task))

    payload = json.loads(redis_client.values["report:task-001"])
    assert payload["task_id"] == "task-001"
    assert payload["status"] == "completed"
    assert payload["result"]["recommended_choices"] == {"rush": [], "stable": [], "safe": []}
    assert payload["result"]["study_plan"] == "按批次整理志愿顺序，并核对招生章程。"
