"""Tests for authenticated volunteer plan APIs."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import router as auth_router
from app.api.plans import router as plans_router
from app.db.database import Base, get_db
from app.models.plan import Plan, PlanItem
from app.models.user import User


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine, tables=[User.__table__, Plan.__table__, PlanItem.__table__])


def override_db() -> Generator[Session, None, None]:
    """Provide an isolated SQLite session for plan tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_client() -> TestClient:
    """Create an isolated FastAPI app for auth + plan API tests."""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(plans_router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def reset_tables() -> None:
    """Reset plan-related tables between test cases."""
    Base.metadata.drop_all(bind=engine, tables=[PlanItem.__table__, Plan.__table__, User.__table__])
    Base.metadata.create_all(bind=engine, tables=[User.__table__, Plan.__table__, PlanItem.__table__])


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


def build_plan_payload(name: str = "广东物理方案") -> dict[str, object]:
    """Return a reusable create-plan payload."""
    return {
        "name": name,
        "province": "广东",
        "subject_type": "物理类",
        "score": 625,
        "rank": 12000,
        "status": "draft",
        "items": [
            {
                "school_name": "中山大学",
                "major_name": "软件工程",
                "province": "广东",
                "city": "广州",
                "group_type": "rush",
                "sort_order": 0,
                "source_type": "recommendation",
                "recommend_reason": "适合作为冲刺志愿。",
                "risk_level": "high",
            },
            {
                "school_name": "暨南大学",
                "major_name": "人工智能",
                "province": "广东",
                "city": "广州",
                "group_type": "stable",
                "sort_order": 0,
                "source_type": "recommendation",
                "recommend_reason": "适合作为稳妥志愿。",
                "risk_level": "medium",
            },
            {
                "school_name": "华南师范大学",
                "major_name": "软件工程",
                "province": "广东",
                "city": "广州",
                "group_type": "safe",
                "sort_order": 0,
                "source_type": "recommendation",
                "recommend_reason": "适合作为保底志愿。",
                "risk_level": "low",
            },
        ],
    }


def test_plan_crud_and_duplicate_flow() -> None:
    """Users should be able to create, inspect, duplicate, list, and delete plans."""
    reset_tables()
    client = create_test_client()
    token = register_and_login(client, "alice")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/plans", json=build_plan_payload(), headers=headers)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "广东物理方案"
    assert created["items_count"] == 3
    assert len(created["grouped_items"]["rush"]) == 1
    assert len(created["grouped_items"]["stable"]) == 1
    assert len(created["grouped_items"]["safe"]) == 1

    plan_id = created["id"]

    detail_response = client.get(f"/plans/{plan_id}", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["items"][0]["school_name"]

    duplicate_response = client.post(f"/plans/{plan_id}/duplicate", headers=headers)
    assert duplicate_response.status_code == 201
    assert "副本" in duplicate_response.json()["name"]

    list_response = client.get("/plans", headers=headers)
    assert list_response.status_code == 200
    plans = list_response.json()
    assert len(plans) == 2

    delete_response = client.delete(f"/plans/{plan_id}", headers=headers)
    assert delete_response.status_code == 204

    deleted_detail_response = client.get(f"/plans/{plan_id}", headers=headers)
    assert deleted_detail_response.status_code == 404


def test_plan_access_is_scoped_to_current_user() -> None:
    """Users must not access each other's plans."""
    reset_tables()
    client = create_test_client()
    alice_token = register_and_login(client, "alice")
    bob_token = register_and_login(client, "bob")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    create_response = client.post("/plans", json=build_plan_payload(), headers=alice_headers)
    assert create_response.status_code == 201
    plan_id = create_response.json()["id"]

    assert client.get(f"/plans/{plan_id}", headers=bob_headers).status_code == 404
    assert client.delete(f"/plans/{plan_id}", headers=bob_headers).status_code == 404


def test_plan_routes_require_authentication() -> None:
    """Plan APIs should reject anonymous access."""
    reset_tables()
    client = create_test_client()

    response = client.get("/plans")
    assert response.status_code == 401
