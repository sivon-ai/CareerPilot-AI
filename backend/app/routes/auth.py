from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(ch.isupper() for ch in value) or not any(ch.islower() for ch in value):
            raise ValueError("Password must contain both uppercase and lowercase letters.")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one number.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    email = request.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email,
        password_hash=hash_password(request.password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        full_name=request.full_name,
        headline=None,
        location=None,
        bio=None,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": profile.full_name,
            "is_active": user.is_active,
        },
    }


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    email = request.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(user.id)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": profile.full_name if profile else None,
            "is_active": user.is_active,
        },
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    profile = current_user.profile
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": profile.full_name if profile else None,
        "is_active": current_user.is_active,
    }


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "logged_out"}
