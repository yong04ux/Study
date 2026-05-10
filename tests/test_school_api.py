"""Tests for school query APIs."""

from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.school import router
from app.db.database import get_db
from app.services.school_service import SchoolService


def override_db() -> Generator[object, None, None]:
    """Provide a dummy DB dependency for monkeypatched service methods."""
    yield object()


def create_test_client() -> TestClient:
    """Create an isolated FastAPI app for school API tests."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_school_search_api(monkeypatch) -> None:
    """School search endpoint should return paginated school data."""

    def fake_search_schools(*args, **kwargs):
        return 1, [
            {
                "id": 1,
                "school_name": "Huaxia Tech University",
                "province": "Beijing",
                "city": "Beijing",
                "school_type": "science",
                "school_level": "undergraduate",
                "is_985": True,
                "is_211": True,
                "is_double_first_class": True,
            }
        ]

    monkeypatch.setattr(SchoolService, "search_schools", staticmethod(fake_search_schools))

    client = create_test_client()
    response = client.get("/schools/search", params={"province": "Beijing", "page": 1, "page_size": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["school_name"] == "Huaxia Tech University"


def test_school_detail_api_not_found(monkeypatch) -> None:
    """School detail endpoint should return 404 when service returns None."""
    monkeypatch.setattr(SchoolService, "get_school_detail", staticmethod(lambda db, school_id: None))

    client = create_test_client()
    response = client.get("/schools/999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
