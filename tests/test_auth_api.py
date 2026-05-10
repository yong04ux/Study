"""Tests for lightweight authentication APIs."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import router
from app.db.database import Base, get_db


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_db() -> Generator[Session, None, None]:
    """Provide an isolated SQLite session for auth tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_client() -> TestClient:
    """Create an isolated FastAPI app for auth API tests."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def reset_tables() -> None:
    """Reset user data between test cases."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_register_login_and_me_flow() -> None:
    """User should be able to register, log in, and read their own profile."""
    reset_tables()
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
    register_body = register_response.json()
    assert register_body["username"] == "alice"
    assert register_body["email"] == "alice@example.com"
    assert "password" not in register_body

    login_response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "alice"


def test_register_rejects_duplicate_username_or_email() -> None:
    """Register endpoint should reject duplicate identities."""
    reset_tables()
    client = create_test_client()

    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    }
    assert client.post("/auth/register", json=payload).status_code == 201

    duplicate_response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice2@example.com",
            "password": "secret123",
        },
    )
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Username or email already exists."


def test_login_rejects_wrong_password() -> None:
    """Login endpoint should reject incorrect passwords."""
    reset_tables()
    client = create_test_client()

    assert client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret123",
        },
    ).status_code == 201

    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username/email or password."
