"""Service layer for lightweight authentication flows."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    """Encapsulate user registration, login, and token issuance."""

    @staticmethod
    def register_user(
        db: Session,
        *,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """Create a new user after checking username/email uniqueness."""
        normalized_username = username.strip()
        normalized_email = email.strip().lower()

        existing_user = db.execute(
            select(User).where(
                or_(
                    User.username == normalized_username,
                    User.email == normalized_email,
                )
            )
        ).scalar_one_or_none()
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists.",
            )

        user = User(
            username=normalized_username,
            email=normalized_email,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, *, username: str, password: str) -> User:
        """Validate username/email + password and return the matching user."""
        identity = username.strip()
        user = db.execute(
            select(User).where(
                or_(User.username == identity, User.email == identity.lower())
            )
        ).scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    def create_token_for_user(user: User) -> str:
        """Issue a bearer token for the authenticated user."""
        return create_access_token(user.id)
