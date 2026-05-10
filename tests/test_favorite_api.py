"""Tests for authenticated favorite school APIs."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.favorites import router as favorites_router
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
        Plan.__table__,
        PlanItem.__table__,
        UserActivity.__table__,
        FavoriteSchool.__table__,
    ],
)


def override_db() -> Generator[Session, None, None]:
    """Provide an isolated SQLite session for favorite tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_client() -> TestClient:
    """Create an isolated FastAPI app for auth + favorite API tests."""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(favorites_router)
    app.include_router(dashboard_router)
    app.include_router(school_router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def reset_tables() -> None:
    """Reset favorite-related tables between test cases."""
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
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_favorite_school_crud_and_dashboard_overview() -> None:
    """Users should be able to favorite schools and see them on the dashboard."""
    reset_tables()
    client = create_test_client()
    token = register_and_login(client, "alice")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/favorites/schools/900001", headers=headers)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["school_id"] == 900001
    assert created["school_name"]

    status_response = client.get("/favorites/schools/900001/status", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["is_favorited"] is True

    list_response = client.get("/favorites/schools", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get("/schools/900001", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["is_favorited"] is True

    overview_response = client.get("/dashboard/overview", headers=headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert len(overview["favorite_schools"]) == 1
    assert overview["favorite_schools"][0]["school_id"] == 900001

    delete_response = client.delete("/favorites/schools/900001", headers=headers)
    assert delete_response.status_code == 204
    assert client.get("/favorites/schools/900001/status", headers=headers).json()["is_favorited"] is False


def test_favorite_routes_require_authentication() -> None:
    """Favorite APIs should reject anonymous access."""
    reset_tables()
    client = create_test_client()

    assert client.get("/favorites/schools").status_code == 401
    assert client.post("/favorites/schools/900001").status_code == 401
