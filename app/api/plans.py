"""Authenticated volunteer plan management APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.plan_schema import (
    CreatePlanRequest,
    PlanDetailResponse,
    PlanSummaryResponse,
    UpdatePlanRequest,
)
from app.models.user import User
from app.services.plan_service import PlanService


router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: CreatePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanDetailResponse:
    """Create a new volunteer plan for the current user."""
    return PlanService.create_plan(db, user=current_user, payload=payload)


@router.get("", response_model=list[PlanSummaryResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlanSummaryResponse]:
    """List all plans owned by the current user."""
    return PlanService.list_plans(db, user=current_user)


@router.get("/{plan_id}", response_model=PlanDetailResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanDetailResponse:
    """Get one plan with grouped items."""
    return PlanService.get_plan_detail(db, user=current_user, plan_id=plan_id)


@router.put("/{plan_id}", response_model=PlanDetailResponse)
def update_plan(
    plan_id: int,
    payload: UpdatePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanDetailResponse:
    """Update a plan's metadata."""
    return PlanService.update_plan(db, user=current_user, plan_id=plan_id, payload=payload)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a plan and all nested items."""
    PlanService.delete_plan(db, user=current_user, plan_id=plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{plan_id}/duplicate", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
def duplicate_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanDetailResponse:
    """Duplicate an existing plan for the current user."""
    return PlanService.duplicate_plan(db, user=current_user, plan_id=plan_id)
