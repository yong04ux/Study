"""Integration test for the main post-login user workflow."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import recommendation as recommendation_api
from app.api import reports as reports_api
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.favorites import router as favorites_router
from app.api.plans import router as plans_router
from app.api.reports import router as reports_router
from app.api.recommendation import router as recommendation_router
from app.api.school import router as school_router
from app.db.database import Base, get_db
from app.models.favorite_school import FavoriteSchool
from app.models.plan import Plan, PlanItem
from app.models.user import User
from app.models.user_activity import UserActivity


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(
    bind=engine,
    tables=[
        User.__table__,
        UserActivity.__table__,
        FavoriteSchool.__table__,
        Plan.__table__,
        PlanItem.__table__,
    ],
)


def override_db() -> Generator[Session, None, None]:
    """Provide an isolated SQLite session for workflow tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_client() -> TestClient:
    """Create an isolated FastAPI app for the authenticated workflow."""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(recommendation_router)
    app.include_router(favorites_router)
    app.include_router(plans_router)
    app.include_router(dashboard_router)
    app.include_router(reports_router)
    app.include_router(school_router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def reset_tables() -> None:
    """Reset the workflow tables between test cases."""
    Base.metadata.drop_all(
        bind=engine,
        tables=[
            PlanItem.__table__,
            Plan.__table__,
            FavoriteSchool.__table__,
            UserActivity.__table__,
            User.__table__,
        ],
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            UserActivity.__table__,
            FavoriteSchool.__table__,
            Plan.__table__,
            PlanItem.__table__,
        ],
    )


def test_authenticated_user_workflow(monkeypatch) -> None:
    """Register, log in, and complete the main authenticated business flow."""
    reset_tables()

    async def fake_recommend(*_, **__) -> dict[str, object]:
        return {
            "score_analysis": {
                "level": "稳中有冲",
                "summary": "当前分数适合冲稳保组合填报。",
                "suggestion": "建议重点关注广东省内计算机相关专业。",
            },
            "recommended_choices": {
                "rush": [
                    {
                        "school_id": 900003,
                        "major_id": None,
                        "school_name": "中山大学",
                        "major_name": "软件工程",
                        "province": "广东",
                        "city": "广州",
                        "min_score": 635,
                        "min_rank": 8200,
                        "is_985": True,
                        "is_211": True,
                        "is_double_first_class": True,
                        "reason": "适合作为冲刺目标。",
                    }
                ],
                "stable": [
                    {
                        "school_id": 900004,
                        "major_id": None,
                        "school_name": "华南理工大学",
                        "major_name": "计算机科学与技术",
                        "province": "广东",
                        "city": "广州",
                        "min_score": 628,
                        "min_rank": 10500,
                        "is_985": True,
                        "is_211": True,
                        "is_double_first_class": True,
                        "reason": "适合作为主填方案。",
                    }
                ],
                "safe": [
                    {
                        "school_id": 900005,
                        "major_id": None,
                        "school_name": "暨南大学",
                        "major_name": "人工智能",
                        "province": "广东",
                        "city": "广州",
                        "min_score": 604,
                        "min_rank": 24500,
                        "is_985": False,
                        "is_211": True,
                        "is_double_first_class": True,
                        "reason": "适合作为保底方案。",
                    }
                ],
            },
            "study_plan": "先完成院校筛选，再核对招生章程。",
            "final_answer": "建议采用冲稳保均衡组合。",
        }

    async def fake_publish_report_task(payload: dict[str, object]) -> None:
        assert payload["province"] == "广东"

    def fake_save_report_status(task_id: str, payload: dict[str, object]) -> None:
        assert task_id
        assert payload["status"] == "submitted"

    monkeypatch.setattr(recommendation_api.recommendation_service, "recommend", fake_recommend)
    monkeypatch.setattr(reports_api, "publish_report_task", fake_publish_report_task)
    monkeypatch.setattr(reports_api, "save_report_status", fake_save_report_status)

    client = create_test_client()

    register_response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "alice"

    recommendation_response = client.post(
        "/recommendations/generate",
        json={
            "user_id": "alice",
            "province": "广东",
            "subject_type": "物理类",
            "score": 625,
            "rank": 12000,
            "preferred_provinces": ["广东"],
            "preferred_majors": ["软件工程", "计算机科学与技术"],
        },
        headers=headers,
    )
    assert recommendation_response.status_code == 200
    recommendation_payload = recommendation_response.json()
    assert recommendation_payload["recommended_choices"]["rush"][0]["school_name"] == "中山大学"

    favorite_response = client.post("/favorites/schools/900003", headers=headers)
    assert favorite_response.status_code == 201
    assert favorite_response.json()["school_id"] == 900003

    school_detail_response = client.get("/schools/900003", headers=headers)
    assert school_detail_response.status_code == 200
    assert school_detail_response.json()["is_favorited"] is True

    plan_response = client.post(
        "/plans",
        json={
            "name": "广东物理类方案",
            "province": "广东",
            "subject_type": "物理类",
            "score": 625,
            "rank": 12000,
            "status": "draft",
            "items": [
                {
                    "school_id": 900003,
                    "school_name": "中山大学",
                    "major_name": "软件工程",
                    "province": "广东",
                    "city": "广州",
                    "group_type": "rush",
                    "sort_order": 0,
                    "source_type": "recommendation",
                    "recommend_reason": "适合作为冲刺目标。",
                    "risk_level": "high",
                },
                {
                    "school_id": 900004,
                    "school_name": "华南理工大学",
                    "major_name": "计算机科学与技术",
                    "province": "广东",
                    "city": "广州",
                    "group_type": "stable",
                    "sort_order": 0,
                    "source_type": "recommendation",
                    "recommend_reason": "适合作为主填方案。",
                    "risk_level": "medium",
                },
                {
                    "school_id": 900005,
                    "school_name": "暨南大学",
                    "major_name": "人工智能",
                    "province": "广东",
                    "city": "广州",
                    "group_type": "safe",
                    "sort_order": 0,
                    "source_type": "recommendation",
                    "recommend_reason": "适合作为保底方案。",
                    "risk_level": "low",
                },
            ],
        },
        headers=headers,
    )
    assert plan_response.status_code == 201
    assert plan_response.json()["items_count"] == 3

    report_response = client.post(
        "/reports/submit",
        json={
            "user_id": "alice",
            "province": "广东",
            "subject_type": "物理类",
            "score": 625,
            "rank": 12000,
            "preferred_provinces": ["广东"],
            "preferred_majors": ["软件工程"],
        },
        headers=headers,
    )
    assert report_response.status_code == 200
    assert report_response.json()["status"] == "submitted"

    overview_response = client.get("/dashboard/overview", headers=headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert len(overview["recent_recommendations"]) == 1
    assert len(overview["favorite_schools"]) == 1
    assert len(overview["report_tasks"]) == 1
    assert len(overview["recent_plans"]) == 1
    assert len(overview["recent_school_views"]) == 1

    activities_response = client.get("/dashboard/activities?limit=10", headers=headers)
    assert activities_response.status_code == 200
    activity_types = {item["activity_type"] for item in activities_response.json()}
    assert {"recommendation", "school_view", "report"} <= activity_types
