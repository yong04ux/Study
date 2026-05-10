"""School search and detail APIs."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import get_optional_current_user
from app.db.database import get_db
from app.models.school_schema import SchoolDetail, SchoolScoreLine, SchoolSearchResponse
from app.models.user import User
from app.services.activity_service import ActivityService
from app.services.favorite_service import FavoriteSchoolService
from app.services.school_service import SchoolService


router = APIRouter(prefix="/schools", tags=["schools"])


def clean_optional(value: str | None) -> str | None:
    """Trim optional string parameters and normalize blanks to None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@router.get("/search", response_model=SchoolSearchResponse)
def search_schools(
    school_name: str | None = Query(default=None, min_length=1, max_length=128),
    province: str | None = Query(default=None, min_length=1, max_length=32),
    school_level: str | None = Query(default=None, min_length=1, max_length=32),
    is_985: bool | None = Query(default=None),
    is_211: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SchoolSearchResponse:
    """Search schools with optional filters."""
    try:
        total, items = SchoolService.search_schools(
            db,
            school_name=clean_optional(school_name),
            province=clean_optional(province),
            school_level=clean_optional(school_level),
            is_985=is_985,
            is_211=is_211,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query schools. Please check MySQL connection and table initialization.",
        ) from exc

    return SchoolSearchResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{school_id}", response_model=SchoolDetail)
def get_school_detail(
    school_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> SchoolDetail:
    """Return school detail by school ID."""
    try:
        school = SchoolService.get_school_detail(db, school_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query school detail. Please check MySQL connection and table initialization.",
        ) from exc

    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School {school_id} was not found.")

    response = SchoolDetail(
        **school,
        is_favorited=(
            FavoriteSchoolService.is_favorited(db, user=current_user, school_id=school_id)
            if current_user is not None
            else False
        ),
    )
    ActivityService.record_activity(
        db,
        user=current_user,
        activity_type="school_view",
        target_id=school_id,
        summary=response.school_name,
        payload={
            "school_id": school_id,
            "school_name": response.school_name,
            "province": response.province,
        },
    )
    return response


@router.get("/{school_id}/score-lines", response_model=list[SchoolScoreLine])
def get_school_score_lines(
    school_id: int = Path(..., ge=1),
    province: str | None = Query(default=None, min_length=1, max_length=32),
    year: int | None = Query(default=None, ge=2000, le=2100),
    subject_type: str | None = Query(default=None, min_length=1, max_length=32),
    major_name: str | None = Query(default=None, min_length=1, max_length=128),
    db: Session = Depends(get_db),
) -> list[SchoolScoreLine]:
    """Return historical score lines for one school."""
    try:
        if not SchoolService.school_exists(db, school_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School {school_id} was not found.")

        rows = SchoolService.get_school_score_lines(
            db,
            school_id=school_id,
            province=clean_optional(province),
            year=year,
            subject_type=clean_optional(subject_type),
            major_name=clean_optional(major_name),
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query score lines. Please check MySQL connection and table initialization.",
        ) from exc

    return [SchoolScoreLine(**row) for row in rows]
