"""Service layer for user volunteer plan management."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException, status
from sqlalchemy import bindparam, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.plan import Plan, PlanItem
from app.models.plan_schema import (
    CreatePlanRequest,
    GroupedPlanItemsResponse,
    PlanDetailResponse,
    PlanItemCreateRequest,
    PlanItemResponse,
    PlanSummaryResponse,
    UpdatePlanRequest,
)
from app.models.user import User


class PlanService:
    """Encapsulate plan CRUD, duplication, and item grouping."""

    DEFAULT_COPY_SUFFIX = "副本"
    GROUP_RISK_DEFAULTS = {
        "rush": "high",
        "stable": "medium",
        "safe": "low",
    }

    @staticmethod
    def create_plan(db: Session, *, user: User, payload: CreatePlanRequest) -> PlanDetailResponse:
        """Create a plan and all of its items in one transaction."""
        try:
            plan = Plan(
                user_id=user.id,
                name=payload.name.strip(),
                province=payload.province.strip(),
                subject_type=payload.subject_type.strip(),
                score=payload.score,
                rank=payload.rank,
                status=payload.status.strip(),
            )
            db.add(plan)
            db.flush()

            for item in payload.items:
                db.add(PlanService._build_plan_item(db, plan_id=plan.id, payload=item))

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create plan.",
            ) from exc

        return PlanService.get_plan_detail(db, user=user, plan_id=plan.id)

    @staticmethod
    def list_plans(db: Session, *, user: User) -> list[PlanSummaryResponse]:
        """Return all plans owned by the current user."""
        rows = db.execute(
            select(Plan, func.count(PlanItem.id).label("items_count"))
            .outerjoin(PlanItem, PlanItem.plan_id == Plan.id)
            .where(Plan.user_id == user.id)
            .group_by(Plan.id)
            .order_by(Plan.updated_at.desc(), Plan.id.desc())
        ).all()

        return [
            PlanSummaryResponse(
                id=plan.id,
                user_id=plan.user_id,
                name=plan.name,
                province=plan.province,
                subject_type=plan.subject_type,
                score=plan.score,
                rank=plan.rank,
                status=plan.status,
                created_at=plan.created_at,
                updated_at=plan.updated_at,
                items_count=items_count,
            )
            for plan, items_count in rows
        ]

    @staticmethod
    def get_plan_detail(db: Session, *, user: User, plan_id: int) -> PlanDetailResponse:
        """Return one plan with all items and grouped buckets."""
        plan = PlanService._get_owned_plan(db, user=user, plan_id=plan_id)
        item_responses = PlanService._build_item_responses(db, plan.items)
        grouped_items = GroupedPlanItemsResponse(
            rush=[item for item in item_responses if item.group_type == "rush"],
            stable=[item for item in item_responses if item.group_type == "stable"],
            safe=[item for item in item_responses if item.group_type == "safe"],
        )
        return PlanDetailResponse(
            id=plan.id,
            user_id=plan.user_id,
            name=plan.name,
            province=plan.province,
            subject_type=plan.subject_type,
            score=plan.score,
            rank=plan.rank,
            status=plan.status,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            items_count=len(item_responses),
            items=item_responses,
            grouped_items=grouped_items,
        )

    @staticmethod
    def update_plan(
        db: Session,
        *,
        user: User,
        plan_id: int,
        payload: UpdatePlanRequest,
    ) -> PlanDetailResponse:
        """Update plan base metadata."""
        plan = PlanService._get_owned_plan(db, user=user, plan_id=plan_id)

        if payload.name is not None:
            plan.name = payload.name.strip()
        if payload.province is not None:
            plan.province = payload.province.strip()
        if payload.subject_type is not None:
            plan.subject_type = payload.subject_type.strip()
        if payload.score is not None:
            plan.score = payload.score
        if payload.rank is not None:
            plan.rank = payload.rank
        if payload.status is not None:
            plan.status = payload.status.strip()

        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update plan.",
            ) from exc

        return PlanService.get_plan_detail(db, user=user, plan_id=plan_id)

    @staticmethod
    def delete_plan(db: Session, *, user: User, plan_id: int) -> None:
        """Delete a plan and its plan items."""
        plan = PlanService._get_owned_plan(db, user=user, plan_id=plan_id)
        try:
            db.delete(plan)
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete plan.",
            ) from exc

    @staticmethod
    def duplicate_plan(db: Session, *, user: User, plan_id: int) -> PlanDetailResponse:
        """Create a full copy of an existing plan."""
        source_plan = PlanService._get_owned_plan(db, user=user, plan_id=plan_id)

        try:
            copied_plan = Plan(
                user_id=user.id,
                name=f"{source_plan.name}-{PlanService.DEFAULT_COPY_SUFFIX}",
                province=source_plan.province,
                subject_type=source_plan.subject_type,
                score=source_plan.score,
                rank=source_plan.rank,
                status=source_plan.status,
            )
            db.add(copied_plan)
            db.flush()

            for item in source_plan.items:
                db.add(
                    PlanItem(
                        plan_id=copied_plan.id,
                        school_id=item.school_id,
                        major_id=item.major_id,
                        group_type=item.group_type,
                        sort_order=item.sort_order,
                        source_type=item.source_type,
                        recommend_reason=item.recommend_reason,
                        risk_level=item.risk_level,
                        school_name_snapshot=item.school_name_snapshot,
                        major_name_snapshot=item.major_name_snapshot,
                    )
                )

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to duplicate plan.",
            ) from exc

        return PlanService.get_plan_detail(db, user=user, plan_id=copied_plan.id)

    @staticmethod
    def _get_owned_plan(db: Session, *, user: User, plan_id: int) -> Plan:
        """Load one plan and enforce ownership."""
        plan = db.execute(
            select(Plan)
            .options(selectinload(Plan.items))
            .where(Plan.id == plan_id, Plan.user_id == user.id)
        ).scalar_one_or_none()
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

        plan.items.sort(key=lambda item: (item.group_type, item.sort_order, item.id))
        return plan

    @staticmethod
    def _build_plan_item(db: Session, *, plan_id: int, payload: PlanItemCreateRequest) -> PlanItem:
        """Resolve identifiers and create a plan item ORM object."""
        resolved_school_id, resolved_school_name = PlanService._resolve_school(
            db,
            school_id=payload.school_id,
            school_name=payload.school_name.strip(),
            province=payload.province.strip() if payload.province else None,
        )
        resolved_major_id, resolved_major_name = PlanService._resolve_major(
            db,
            major_id=payload.major_id,
            major_name=payload.major_name.strip() if payload.major_name else None,
        )

        return PlanItem(
            plan_id=plan_id,
            school_id=resolved_school_id,
            major_id=resolved_major_id,
            group_type=payload.group_type,
            sort_order=payload.sort_order,
            source_type=payload.source_type,
            recommend_reason=payload.recommend_reason.strip() if payload.recommend_reason else None,
            risk_level=(payload.risk_level or PlanService.GROUP_RISK_DEFAULTS[payload.group_type]).strip(),
            school_name_snapshot=resolved_school_name,
            major_name_snapshot=resolved_major_name,
        )

    @staticmethod
    def _resolve_school(
        db: Session,
        *,
        school_id: int | None,
        school_name: str,
        province: str | None,
    ) -> tuple[int | None, str]:
        """Resolve school id by explicit id or by exact name lookup."""
        if school_id is not None:
            try:
                row = db.execute(
                    text("SELECT id, name FROM school WHERE id = :school_id"),
                    {"school_id": school_id},
                ).mappings().first()
            except SQLAlchemyError:
                row = None
            if row is not None:
                return int(row["id"]), str(row["name"])

        params: dict[str, object] = {"school_name": school_name}
        sql = "SELECT id, name FROM school WHERE name = :school_name"
        if province:
            sql += " AND province = :province"
            params["province"] = province
        sql += " ORDER BY id ASC LIMIT 1"
        try:
            row = db.execute(text(sql), params).mappings().first()
        except SQLAlchemyError:
            row = None
        if row is not None:
            return int(row["id"]), str(row["name"])
        return None, school_name

    @staticmethod
    def _resolve_major(
        db: Session,
        *,
        major_id: int | None,
        major_name: str | None,
    ) -> tuple[int | None, str | None]:
        """Resolve major id by explicit id or by exact name lookup."""
        if major_id is not None:
            try:
                row = db.execute(
                    text("SELECT id, name FROM major WHERE id = :major_id"),
                    {"major_id": major_id},
                ).mappings().first()
            except SQLAlchemyError:
                row = None
            if row is not None:
                return int(row["id"]), str(row["name"])

        if not major_name:
            return None, None

        try:
            row = db.execute(
                text("SELECT id, name FROM major WHERE name = :major_name ORDER BY id ASC LIMIT 1"),
                {"major_name": major_name},
            ).mappings().first()
        except SQLAlchemyError:
            row = None
        if row is not None:
            return int(row["id"]), str(row["name"])
        return None, major_name

    @staticmethod
    def _build_item_responses(db: Session, items: Iterable[PlanItem]) -> list[PlanItemResponse]:
        """Join school/major labels in bulk and return sorted response objects."""
        item_list = sorted(items, key=lambda item: (item.group_type, item.sort_order, item.id))
        school_names = PlanService._fetch_names_map(
            db,
            table_name="school",
            ids={item.school_id for item in item_list if item.school_id is not None},
        )
        major_names = PlanService._fetch_names_map(
            db,
            table_name="major",
            ids={item.major_id for item in item_list if item.major_id is not None},
        )

        return [
            PlanItemResponse(
                id=item.id,
                plan_id=item.plan_id,
                school_id=item.school_id,
                major_id=item.major_id,
                school_name=school_names.get(item.school_id) or item.school_name_snapshot,
                major_name=major_names.get(item.major_id) or item.major_name_snapshot,
                group_type=item.group_type,
                sort_order=item.sort_order,
                source_type=item.source_type,
                recommend_reason=item.recommend_reason,
                risk_level=item.risk_level,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in item_list
        ]

    @staticmethod
    def _fetch_names_map(db: Session, *, table_name: str, ids: set[int]) -> dict[int, str]:
        """Bulk-load resource names for response enrichment."""
        if not ids:
            return {}

        try:
            rows = db.execute(
                text(f"SELECT id, name FROM {table_name} WHERE id IN :ids").bindparams(
                    bindparam("ids", expanding=True)
                ),
                {"ids": list(ids)},
            ).mappings()
        except SQLAlchemyError:
            return {}
        return {int(row["id"]): str(row["name"]) for row in rows}
