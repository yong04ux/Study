"""Service helpers for favorite school operations."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.favorite_school import FavoriteSchool
from app.models.favorite_schema import FavoriteSchoolResponse
from app.models.user import User
from app.services.school_service import SchoolService


class FavoriteSchoolService:
    """Encapsulate favorite-school persistence and lookup."""

    @staticmethod
    def add_favorite(db: Session, *, user: User, school_id: int) -> FavoriteSchoolResponse:
        """Favorite one school for the current user."""
        existing = FavoriteSchoolService._get_row(db, user_id=user.id, school_id=school_id)
        if existing is not None:
            return FavoriteSchoolService._to_response(existing)

        school = SchoolService.get_school_detail(db, school_id)
        if school is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"School {school_id} was not found.",
            )

        row = FavoriteSchool(
            user_id=user.id,
            school_id=school_id,
            school_name_snapshot=str(school["school_name"]),
            province_snapshot=school.get("province"),
            city_snapshot=school.get("city"),
        )
        try:
            db.add(row)
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = FavoriteSchoolService._get_row(db, user_id=user.id, school_id=school_id)
            if existing is not None:
                return FavoriteSchoolService._to_response(existing)
            raise

        db.refresh(row)
        return FavoriteSchoolService._to_response(row)

    @staticmethod
    def remove_favorite(db: Session, *, user: User, school_id: int) -> None:
        """Remove one favorite school for the current user."""
        row = FavoriteSchoolService._get_row(db, user_id=user.id, school_id=school_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Favorite school {school_id} was not found.",
            )

        db.delete(row)
        db.commit()

    @staticmethod
    def list_favorites(
        db: Session,
        *,
        user: User,
        limit: int | None = None,
    ) -> list[FavoriteSchoolResponse]:
        """List current user's favorite schools."""
        query = (
            select(FavoriteSchool)
            .where(FavoriteSchool.user_id == user.id)
            .order_by(FavoriteSchool.created_at.desc(), FavoriteSchool.id.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        rows = db.execute(query).scalars().all()
        return [FavoriteSchoolService._to_response(row) for row in rows]

    @staticmethod
    def is_favorited(db: Session, *, user: User, school_id: int) -> bool:
        """Return whether one school is favorited by the current user."""
        return FavoriteSchoolService._get_row(db, user_id=user.id, school_id=school_id) is not None

    @staticmethod
    def _get_row(db: Session, *, user_id: int, school_id: int) -> FavoriteSchool | None:
        """Return one favorite row by user and school."""
        return db.execute(
            select(FavoriteSchool).where(
                FavoriteSchool.user_id == user_id,
                FavoriteSchool.school_id == school_id,
            )
        ).scalar_one_or_none()

    @staticmethod
    def _to_response(row: FavoriteSchool) -> FavoriteSchoolResponse:
        """Normalize ORM row into API response."""
        return FavoriteSchoolResponse(
            id=row.id,
            school_id=row.school_id,
            school_name=row.school_name_snapshot,
            province=row.province_snapshot,
            city=row.city_snapshot,
            created_at=row.created_at,
        )
