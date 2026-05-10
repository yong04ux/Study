"""Authenticated dashboard APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.dashboard_schema import DashboardOverviewResponse, UserActivityResponse
from app.models.user import User
from app.services.activity_service import ActivityService
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverviewResponse:
    """Return lightweight dashboard overview cards for the current user."""
    return DashboardService.get_overview(db, user=current_user)


@router.get("/activities", response_model=list[UserActivityResponse])
def get_dashboard_activities(
    activity_type: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserActivityResponse]:
    """Return recent dashboard activities for the current user."""
    return ActivityService.list_activities(
        db,
        user=current_user,
        activity_type=activity_type.strip() if activity_type else None,
        limit=limit,
    )
