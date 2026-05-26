"""
Users endpoints: profile, settings, etc.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, UserCreate
from app.repositories import user_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current user profile.
    """
    logger.info(f"GET /users/me - user_id={current_user.id}, email={current_user.email}")
    return current_user


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> User:
    """
    Get user by ID (admin only for now).
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )
    user = user_repository.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/me", response_model=UserRead)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> User:
    """
    Update current user profile.
    """
    logger.info(f"PUT /users/me - user_id={current_user.id}")
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.is_active is not None:
        current_user.is_active = user_update.is_active
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/signup", response_model=UserRead, status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """Compatibility endpoint for frontend: /users/signup"""
    existing = user_repository.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = user_repository.create_user(db, user_in=user_in)
    logger.info("New user registered user_id=%s, email=%s", user.id, user.email)
    return user
