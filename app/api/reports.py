"""Async report generation APIs."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from redis import Redis as RedisClient
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover - fallback for environments without redis installed
    RedisClient = None  # type: ignore[assignment]

    class RedisError(RuntimeError):
        """Fallback Redis error when redis package is unavailable."""


from app.core.config import settings
from app.core.security import get_optional_current_user
from app.db.database import get_db
from app.models.user import User
from app.mq.kafka_producer import KafkaProducerUnavailable, publish_report_task
from app.services.activity_service import ActivityService


router = APIRouter(prefix="/reports", tags=["reports"])
REPORT_TTL_SECONDS = 24 * 60 * 60


class ReportSubmitRequest(BaseModel):
    """POST /reports/submit request body."""

    user_id: str = Field(..., min_length=1, max_length=64)
    province: str = Field(..., min_length=1, max_length=32)
    subject_type: str = Field(..., min_length=1, max_length=32)
    score: int = Field(..., ge=0, le=750)
    rank: int = Field(..., ge=1)
    preferred_provinces: list[str] = Field(default_factory=list, max_length=10)
    preferred_majors: list[str] = Field(default_factory=list, max_length=10)


class ReportSubmitResponse(BaseModel):
    """Report task submit response."""

    task_id: str
    status: str


class ReportStatusResponse(BaseModel):
    """Report task status response."""

    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


def get_report_redis() -> Any:
    """Create a short-timeout Redis client for report tracking."""
    if RedisClient is None:
        raise RedisError("Redis client is not installed, report status is unavailable.")
    return RedisClient.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


def save_report_status(task_id: str, payload: dict[str, Any]) -> None:
    """Save report task status to Redis with a TTL."""
    redis_client = get_report_redis()
    try:
        redis_client.setex(
            f"report:{task_id}",
            REPORT_TTL_SECONDS,
            json.dumps(payload, ensure_ascii=False, default=str),
        )
    finally:
        redis_client.close()


@router.post("/submit", response_model=ReportSubmitResponse)
async def submit_report(
    payload: ReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReportSubmitResponse:
    """Submit a report generation task to Kafka and return immediately."""
    task_id = str(uuid.uuid4())
    province = payload.province.strip()
    subject_type = payload.subject_type.strip()
    task_payload = {
        "task_id": task_id,
        "user_id": payload.user_id.strip(),
        "province": province,
        "subject_type": subject_type,
        "score": payload.score,
        "rank": payload.rank,
        "preferred_provinces": [item.strip() for item in payload.preferred_provinces if item.strip()],
        "preferred_majors": [item.strip() for item in payload.preferred_majors if item.strip()],
    }

    if not province or not subject_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="province and subject_type cannot be blank.",
        )

    try:
        await publish_report_task(task_payload)
    except KafkaProducerUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    try:
        save_report_status(task_id, {"task_id": task_id, "status": "submitted", "result": None})
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka 已收到任务，但 Redis 不可用，暂时无法追踪报告状态。",
        ) from exc

    ActivityService.record_activity(
        db,
        user=current_user,
        activity_type="report",
        target_id=task_id,
        summary=f"{province}-{subject_type} {payload.score} score report",
        payload={
            "task_id": task_id,
            "province": province,
            "subject_type": subject_type,
            "score": payload.score,
            "rank": payload.rank,
            "status": "submitted",
        },
    )
    return ReportSubmitResponse(task_id=task_id, status="submitted")


@router.get("/{task_id}", response_model=ReportStatusResponse)
def get_report(task_id: str) -> ReportStatusResponse:
    """Read one report task status from Redis."""
    redis_client = get_report_redis()
    try:
        raw_value = redis_client.get(f"report:{task_id}")
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is unavailable, report status cannot be queried right now.",
        ) from exc
    finally:
        redis_client.close()

    if raw_value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report task {task_id} was not found.",
        )

    return ReportStatusResponse(**json.loads(raw_value))
