"""Authentication APIs for register/login/current-user flows."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.auth_schema import (
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.models.user import User
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> CurrentUserResponse:
    """Register a new user with a hashed password."""
    user = AuthService.register_user(
        db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
    return CurrentUserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate credentials and return a JWT bearer token."""
    user = AuthService.authenticate_user(
        db,
        username=payload.username,
        password=payload.password,
    )
    return TokenResponse(access_token=AuthService.create_token_for_user(user))


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    """Return the current authenticated user."""
    return CurrentUserResponse.model_validate(current_user)
