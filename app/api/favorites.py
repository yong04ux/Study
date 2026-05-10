"""Authenticated favorite school APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.favorite_schema import FavoriteSchoolResponse, FavoriteSchoolStatusResponse
from app.models.user import User
from app.services.favorite_service import FavoriteSchoolService


router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/schools", response_model=list[FavoriteSchoolResponse])
def list_favorite_schools(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FavoriteSchoolResponse]:
    """Return the current user's favorite schools."""
    return FavoriteSchoolService.list_favorites(db, user=current_user)


@router.post("/schools/{school_id}", response_model=FavoriteSchoolResponse, status_code=status.HTTP_201_CREATED)
def add_favorite_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteSchoolResponse:
    """Favorite one school."""
    return FavoriteSchoolService.add_favorite(db, user=current_user, school_id=school_id)


@router.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Unfavorite one school."""
    FavoriteSchoolService.remove_favorite(db, user=current_user, school_id=school_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/schools/{school_id}/status", response_model=FavoriteSchoolStatusResponse)
def get_favorite_school_status(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteSchoolStatusResponse:
    """Return whether one school is favorited by the current user."""
    return FavoriteSchoolStatusResponse(
        school_id=school_id,
        is_favorited=FavoriteSchoolService.is_favorited(db, user=current_user, school_id=school_id),
    )
