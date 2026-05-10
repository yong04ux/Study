"""Pydantic schemas for dashboard APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.favorite_schema import FavoriteSchoolResponse
from app.models.plan_schema import PlanSummaryResponse


class UserActivityResponse(BaseModel):
    """One user activity item shown on the dashboard."""

    id: int
    activity_type: str
    target_id: str | None = None
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    """Lightweight dashboard overview payload."""

    recent_recommendations: list[UserActivityResponse] = Field(default_factory=list)
    recent_school_views: list[UserActivityResponse] = Field(default_factory=list)
    recent_questions: list[UserActivityResponse] = Field(default_factory=list)
    favorite_schools: list[FavoriteSchoolResponse] = Field(default_factory=list)
    report_tasks: list[UserActivityResponse] = Field(default_factory=list)
    recent_plans: list[PlanSummaryResponse] = Field(default_factory=list)
