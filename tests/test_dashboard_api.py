"""Tests for authenticated dashboard overview and activity APIs."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.db.database import Base, get_db
from app.models.favorite_school import FavoriteSchool
from app.models.plan import Plan, PlanItem
from app.models.user import User
from app.models.user_activity import UserActivity
from app.services.activity_service import ActivityService


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
        Plan.__table__,
        PlanItem.__table__,
        UserActivity.__table__,
        FavoriteSchool.__table__,
    ],
)


def override_db() -> Generator[Session, None, None]:
    """Provide an isolated SQLite session for dashboard tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_client() -> TestClient:
    """Create an isolated FastAPI app for auth + dashboard API tests."""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def reset_tables() -> None:
    """Reset dashboard-related tables between test cases."""
    Base.metadata.drop_all(
        bind=engine,
        tables=[
            FavoriteSchool.__table__,
            UserActivity.__table__,
            PlanItem.__table__,
            Plan.__table__,
            User.__table__,
        ],
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Plan.__table__,
            PlanItem.__table__,
            UserActivity.__table__,
            FavoriteSchool.__table__,
        ],
    )


def register_and_login(client: TestClient, username: str) -> str:
    """Create a user and return a bearer token."""
    email = f"{username}@example.com"
    password = "secret123"
    assert client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    ).status_code == 201
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_dashboard_overview_and_activities_are_scoped_to_current_user() -> None:
    """Dashboard endpoints should only return the current user's data."""
    reset_tables()
    client = create_test_client()
    alice_token = register_and_login(client, "alice")
    bob_token = register_and_login(client, "bob")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    with TestingSessionLocal() as db:
        alice = db.query(User).filter(User.username == "alice").one()
        bob = db.query(User).filter(User.username == "bob").one()
        ActivityService.record_activity(
            db,
            user=alice,
            activity_type="recommendation",
            summary="广东-物理类 625分推荐",
            payload={"score": 625},
        )
        ActivityService.record_activity(
            db,
            user=alice,
            activity_type="qa",
            summary="软件工程值得报考吗？",
            payload={"question": "软件工程值得报考吗？"},
        )
        ActivityService.record_activity(
            db,
            user=bob,
            activity_type="school_view",
            summary="北京大学",
            payload={"school_name": "北京大学"},
        )

    overview_response = client.get("/dashboard/overview", headers=alice_headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert len(overview["recent_recommendations"]) == 1
    assert overview["recent_recommendations"][0]["summary"] == "广东-物理类 625分推荐"
    assert len(overview["recent_questions"]) == 1
    assert overview["recent_school_views"] == []
    assert overview["favorite_schools"] == []
    assert overview["recent_plans"] == []

    activities_response = client.get("/dashboard/activities", headers=alice_headers)
    assert activities_response.status_code == 200
    activities = activities_response.json()
    assert len(activities) == 2
    assert all(item["summary"] != "北京大学" for item in activities)

    filtered_response = client.get("/dashboard/activities?activity_type=qa", headers=alice_headers)
    assert filtered_response.status_code == 200
    filtered = filtered_response.json()
    assert len(filtered) == 1
    assert filtered[0]["activity_type"] == "qa"

    assert client.get("/dashboard/overview", headers=bob_headers).status_code == 200


def test_dashboard_routes_require_authentication() -> None:
    """Dashboard APIs should reject anonymous access."""
    reset_tables()
    client = create_test_client()

    assert client.get("/dashboard/overview").status_code == 401
    assert client.get("/dashboard/activities").status_code == 401
