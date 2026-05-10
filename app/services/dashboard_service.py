"""Service layer for the lightweight user dashboard."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.dashboard_schema import DashboardOverviewResponse
from app.models.user import User
from app.services.activity_service import ActivityService
from app.services.favorite_service import FavoriteSchoolService
from app.services.plan_service import PlanService


class DashboardService:
    """Build dashboard overview data from activities and plans."""

    @staticmethod
    def get_overview(db: Session, *, user: User) -> DashboardOverviewResponse:
        """Return a compact dashboard overview for the current user."""
        return DashboardOverviewResponse(
            recent_recommendations=ActivityService.list_activities(
                db, user=user, activity_type="recommendation", limit=5
            ),
            recent_school_views=ActivityService.list_activities(
                db, user=user, activity_type="school_view", limit=5
            ),
            recent_questions=ActivityService.list_activities(
                db, user=user, activity_type="qa", limit=5
            ),
            favorite_schools=FavoriteSchoolService.list_favorites(db, user=user, limit=5),
            report_tasks=ActivityService.list_activities(
                db, user=user, activity_type="report", limit=5
            ),
            recent_plans=PlanService.list_plans(db, user=user)[:5],
        )
