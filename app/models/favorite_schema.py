"""Pydantic schemas for favorite school APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FavoriteSchoolResponse(BaseModel):
    """One favorite school entry."""

    id: int
    school_id: int
    school_name: str = Field(..., description="Snapshot school name.")
    province: str | None = Field(default=None, description="Snapshot province.")
    city: str | None = Field(default=None, description="Snapshot city.")
    created_at: datetime


class FavoriteSchoolStatusResponse(BaseModel):
    """Current user's favorite status for one school."""

    school_id: int
    is_favorited: bool
