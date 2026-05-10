"""SQLAlchemy ORM model for favorite schools."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FavoriteSchool(Base):
    """Persist one user's favorite school snapshot."""

    __tablename__ = "favorite_school"
    __table_args__ = (
        UniqueConstraint("user_id", "school_id", name="uk_favorite_school_user_school"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    school_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    school_name_snapshot: Mapped[str] = mapped_column(String(128), nullable=False)
    province_snapshot: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city_snapshot: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
