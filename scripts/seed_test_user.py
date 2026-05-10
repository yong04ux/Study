"""Seed repeatable test users and post-login demo data."""

from __future__ import annotations

import json

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.favorite_school import FavoriteSchool
from app.models.plan import Plan, PlanItem
from app.models.user import User
from app.models.user_activity import UserActivity


TEST_USER = {
    "username": "demo_student",
    "email": "demo_student@example.com",
    "password": "gaokao123",
}


def upsert_user() -> User:
    """Create or refresh the demo user account."""
    with SessionLocal() as db:
        user = db.execute(
            select(User).where(
                (User.username == TEST_USER["username"]) | (User.email == TEST_USER["email"])
            )
        ).scalar_one_or_none()

        if user is None:
            user = User(
                username=TEST_USER["username"],
                email=TEST_USER["email"],
                password_hash=hash_password(TEST_USER["password"]),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        user.username = TEST_USER["username"]
        user.email = TEST_USER["email"]
        user.password_hash = hash_password(TEST_USER["password"])
        db.commit()
        db.refresh(user)
        return user


def reset_user_demo_data(user: User) -> None:
    """Replace the user's favorites, plans, and activity stream with demo data."""
    with SessionLocal() as db:
        db_user = db.get(User, user.id)
        if db_user is None:
            raise RuntimeError("Demo user was not found after creation.")

        for plan in db.execute(select(Plan).where(Plan.user_id == db_user.id)).scalars():
            db.delete(plan)

        for favorite in db.execute(
            select(FavoriteSchool).where(FavoriteSchool.user_id == db_user.id)
        ).scalars():
            db.delete(favorite)

        for activity in db.execute(
            select(UserActivity).where(UserActivity.user_id == db_user.id)
        ).scalars():
            db.delete(activity)

        db.flush()

        db.add(
            FavoriteSchool(
                user_id=db_user.id,
                school_id=900003,
                school_name_snapshot="中山大学",
                province_snapshot="广东",
                city_snapshot="广州",
            )
        )
        db.add(
            FavoriteSchool(
                user_id=db_user.id,
                school_id=900004,
                school_name_snapshot="华南理工大学",
                province_snapshot="广东",
                city_snapshot="广州",
            )
        )

        plan = Plan(
            user_id=db_user.id,
            name="广东物理类示例方案",
            province="广东",
            subject_type="物理类",
            score=625,
            rank=12000,
            status="draft",
        )
        db.add(plan)
        db.flush()

        demo_items = [
            {
                "group_type": "rush",
                "school_name": "中山大学",
                "major_name": "软件工程",
                "recommend_reason": "适合作为冲刺目标，兼顾地域与专业匹配。",
                "risk_level": "high",
            },
            {
                "group_type": "stable",
                "school_name": "华南理工大学",
                "major_name": "计算机科学与技术",
                "recommend_reason": "与当前分数段匹配度较高，适合作为主填方案。",
                "risk_level": "medium",
            },
            {
                "group_type": "safe",
                "school_name": "暨南大学",
                "major_name": "人工智能",
                "recommend_reason": "适合作为保底层，兼顾城市与专业偏好。",
                "risk_level": "low",
            },
        ]
        for index, item in enumerate(demo_items):
            db.add(
                PlanItem(
                    plan_id=plan.id,
                    school_id=None,
                    major_id=None,
                    group_type=item["group_type"],
                    sort_order=index,
                    source_type="recommendation",
                    recommend_reason=item["recommend_reason"],
                    risk_level=item["risk_level"],
                    school_name_snapshot=item["school_name"],
                    major_name_snapshot=item["major_name"],
                )
            )

        activities = [
            UserActivity(
                user_id=db_user.id,
                activity_type="recommendation",
                target_id=None,
                summary="广东-物理类 625分推荐",
                payload_json=json.dumps(
                    {
                        "province": "广东",
                        "subject_type": "物理类",
                        "score": 625,
                        "rank": 12000,
                        "rush_count": 1,
                        "stable_count": 1,
                        "safe_count": 1,
                    },
                    ensure_ascii=False,
                ),
            ),
            UserActivity(
                user_id=db_user.id,
                activity_type="school_view",
                target_id="900003",
                summary="中山大学",
                payload_json=json.dumps(
                    {
                        "school_id": 900003,
                        "school_name": "中山大学",
                        "province": "广东",
                    },
                    ensure_ascii=False,
                ),
            ),
            UserActivity(
                user_id=db_user.id,
                activity_type="qa",
                target_id=None,
                summary="如何安排冲稳保志愿顺序",
                payload_json=json.dumps(
                    {
                        "question": "如何安排冲稳保志愿顺序？",
                        "answer_preview": "建议先确定保底，再补足稳定层，最后保留少量冲刺名额。",
                    },
                    ensure_ascii=False,
                ),
            ),
            UserActivity(
                user_id=db_user.id,
                activity_type="report",
                target_id="demo-report-task",
                summary="广东-物理类 625分报告",
                payload_json=json.dumps(
                    {
                        "task_id": "demo-report-task",
                        "province": "广东",
                        "subject_type": "物理类",
                        "score": 625,
                        "rank": 12000,
                        "status": "completed",
                    },
                    ensure_ascii=False,
                ),
            ),
        ]
        db.add_all(activities)
        db.commit()


def main() -> None:
    """Seed one ready-to-use demo account and business data."""
    user = upsert_user()
    reset_user_demo_data(user)
    print("Seed completed.")
    print(f"username: {TEST_USER['username']}")
    print(f"email:    {TEST_USER['email']}")
    print(f"password: {TEST_USER['password']}")


if __name__ == "__main__":
    main()
