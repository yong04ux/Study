"""Service helpers for recording and querying user activity."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.dashboard_schema import UserActivityResponse
from app.models.user import User
from app.models.user_activity import UserActivity


class ActivityService:
    """Encapsulate lightweight activity stream operations."""

    @staticmethod
    def record_activity(
        db: Session,
        *,
        user: User | None,
        activity_type: str,
        summary: str,
        target_id: str | int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Best-effort activity logging that must never break main business flow."""
        if user is None:
            return

        try:
            db.add(
                UserActivity(
                    user_id=user.id,
                    activity_type=activity_type,
                    target_id=str(target_id) if target_id is not None else None,
                    summary=summary[:255],
                    payload_json=json.dumps(payload or {}, ensure_ascii=False),
                )
            )
            db.commit()
        except SQLAlchemyError:
            db.rollback()

    @staticmethod
    def list_activities(
        db: Session,
        *,
        user: User,
        activity_type: str | None = None,
        limit: int = 20,
    ) -> list[UserActivityResponse]:
        """Return recent user activities, optionally filtered by type."""
        query = (
            select(UserActivity)
            .where(UserActivity.user_id == user.id)
            .order_by(UserActivity.created_at.desc(), UserActivity.id.desc())
            .limit(limit)
        )
        if activity_type:
            query = query.where(UserActivity.activity_type == activity_type)

        rows = db.execute(query).scalars().all()
        return [ActivityService._to_response(item) for item in rows]

    @staticmethod
    def _to_response(item: UserActivity) -> UserActivityResponse:
        """Normalize one activity row into response payload."""
        try:
            payload = json.loads(item.payload_json) if item.payload_json else {}
        except json.JSONDecodeError:
            payload = {}

        return UserActivityResponse(
            id=item.id,
            activity_type=item.activity_type,
            target_id=item.target_id,
            summary=item.summary,
            payload=payload,
            created_at=item.created_at,
        )
