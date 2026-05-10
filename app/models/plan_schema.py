"""Pydantic schemas for volunteer plan APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


GroupType = Literal["rush", "stable", "safe"]
SourceType = Literal["manual", "recommendation"]


class PlanItemCreateRequest(BaseModel):
    """Create payload for a single plan item."""

    school_id: int | None = Field(default=None, ge=1)
    major_id: int | None = Field(default=None, ge=1)
    school_name: str = Field(..., min_length=1, max_length=128)
    major_name: str | None = Field(default=None, max_length=128)
    province: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=64)
    group_type: GroupType
    sort_order: int = Field(default=0, ge=0)
    source_type: SourceType = "recommendation"
    recommend_reason: str | None = Field(default=None, max_length=2000)
    risk_level: str | None = Field(default=None, max_length=32)


class CreatePlanRequest(BaseModel):
    """Create a new plan with initial items."""

    name: str = Field(..., min_length=1, max_length=100)
    province: str = Field(..., min_length=1, max_length=32)
    subject_type: str = Field(..., min_length=1, max_length=32)
    score: int = Field(..., ge=0, le=750)
    rank: int = Field(..., ge=1)
    status: str = Field(default="draft", min_length=1, max_length=32)
    items: list[PlanItemCreateRequest] = Field(default_factory=list)


class UpdatePlanRequest(BaseModel):
    """Update plan basic metadata."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    province: str | None = Field(default=None, min_length=1, max_length=32)
    subject_type: str | None = Field(default=None, min_length=1, max_length=32)
    score: int | None = Field(default=None, ge=0, le=750)
    rank: int | None = Field(default=None, ge=1)
    status: str | None = Field(default=None, min_length=1, max_length=32)


class PlanSummaryResponse(BaseModel):
    """List response for a plan."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    province: str
    subject_type: str
    score: int
    rank: int
    status: str
    created_at: datetime
    updated_at: datetime
    items_count: int = 0


class PlanItemResponse(BaseModel):
    """Detailed plan item response."""

    id: int
    plan_id: int
    school_id: int | None = None
    major_id: int | None = None
    school_name: str
    major_name: str | None = None
    group_type: GroupType
    sort_order: int
    source_type: SourceType
    recommend_reason: str | None = None
    risk_level: str | None = None
    created_at: datetime
    updated_at: datetime


class GroupedPlanItemsResponse(BaseModel):
    """Plan items grouped into rush/stable/safe buckets."""

    rush: list[PlanItemResponse] = Field(default_factory=list)
    stable: list[PlanItemResponse] = Field(default_factory=list)
    safe: list[PlanItemResponse] = Field(default_factory=list)


class PlanDetailResponse(PlanSummaryResponse):
    """Detailed plan payload including items and grouped result."""

    items: list[PlanItemResponse] = Field(default_factory=list)
    grouped_items: GroupedPlanItemsResponse
