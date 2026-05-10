"""API tests for the recommendation endpoint."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.recommendation import router as recommendation_router


recommendation_test_app = FastAPI()
recommendation_test_app.include_router(recommendation_router)
client = TestClient(recommendation_test_app)


def test_generate_recommendation_returns_fixed_payload() -> None:
    """The endpoint should return the fixed frontend contract."""
    response = client.post(
        "/recommendations/generate",
        json={
            "user_id": "frontend-user",
            "province": "广东",
            "subject_type": "物理类",
            "score": 625,
            "rank": 12000,
            "preferred_provinces": ["广东", "北京", "上海"],
            "preferred_majors": ["计算机科学与技术", "软件工程"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "score_analysis",
        "recommended_choices",
        "study_plan",
        "final_answer",
    }
    assert set(payload["score_analysis"].keys()) == {"level", "summary", "suggestion"}
    assert set(payload["recommended_choices"].keys()) == {"rush", "stable", "safe"}
    assert isinstance(payload["study_plan"], str)
    assert isinstance(payload["final_answer"], str)
