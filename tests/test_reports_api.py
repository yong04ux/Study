"""API tests for asynchronous report submission and querying."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import reports


reports_test_app = FastAPI()
reports_test_app.include_router(reports.router)
client = TestClient(reports_test_app)


def test_submit_report_returns_task_id_and_submitted_status(monkeypatch) -> None:
    """Submitting an async report should enqueue the task and return immediately."""
    captured_task: dict[str, object] = {}
    captured_status: dict[str, object] = {}

    async def fake_publish_report_task(payload: dict[str, object]) -> None:
        captured_task.update(payload)

    def fake_save_report_status(task_id: str, payload: dict[str, object]) -> None:
        captured_status["task_id"] = task_id
        captured_status["payload"] = payload

    monkeypatch.setattr(reports, "publish_report_task", fake_publish_report_task)
    monkeypatch.setattr(reports, "save_report_status", fake_save_report_status)

    response = client.post(
        "/reports/submit",
        json={
            "user_id": "frontend-user",
            "province": "广东",
            "subject_type": "物理类",
            "score": 625,
            "rank": 12000,
            "preferred_provinces": ["广东", "北京"],
            "preferred_majors": ["计算机科学与技术"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "submitted"
    assert isinstance(payload["task_id"], str) and payload["task_id"]
    assert captured_task["task_id"] == payload["task_id"]
    assert captured_status["task_id"] == payload["task_id"]
    assert captured_status["payload"] == {
        "task_id": payload["task_id"],
        "status": "submitted",
        "result": None,
    }


def test_submit_report_returns_clear_error_when_redis_unavailable(monkeypatch) -> None:
    """Redis outages should produce a clear API error for report tracking."""

    async def fake_publish_report_task(_: dict[str, object]) -> None:
        return None

    def fake_save_report_status(_: str, __: dict[str, object]) -> None:
        raise reports.RedisError("redis down")

    monkeypatch.setattr(reports, "publish_report_task", fake_publish_report_task)
    monkeypatch.setattr(reports, "save_report_status", fake_save_report_status)

    response = client.post(
        "/reports/submit",
        json={
            "user_id": "frontend-user",
            "province": "广东",
            "subject_type": "物理类",
            "score": 625,
            "rank": 12000,
            "preferred_provinces": [],
            "preferred_majors": [],
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Kafka 已收到任务，但 Redis 不可用，暂时无法追踪报告状态。"


def test_get_report_returns_completed_result(monkeypatch) -> None:
    """Querying a completed report should return the full recommendation payload."""

    class FakeRedis:
        def get(self, key: str) -> str | None:
            assert key == "report:task-123"
            return json.dumps(
                {
                    "task_id": "task-123",
                    "status": "completed",
                    "result": {
                        "score_analysis": {
                            "level": "稳中有冲",
                            "summary": "分数具备较强竞争力。",
                            "suggestion": "重点关注省内强校与热门工科专业。",
                        },
                        "recommended_choices": {
                            "rush": [],
                            "stable": [],
                            "safe": [],
                        },
                        "study_plan": "先完成院校筛选，再核对招生章程。",
                        "final_answer": "建议采用冲稳保组合填报。",
                    },
                    "error": None,
                },
                ensure_ascii=False,
            )

        def close(self) -> None:
            return None

    monkeypatch.setattr(reports, "get_report_redis", lambda: FakeRedis())

    response = client.get("/reports/task-123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == "task-123"
    assert payload["status"] == "completed"
    assert payload["result"]["recommended_choices"] == {"rush": [], "stable": [], "safe": []}
    assert payload["result"]["study_plan"] == "先完成院校筛选，再核对招生章程。"
