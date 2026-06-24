from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate, is_superuser: bool = False) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_superuser=is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, user: User, new_password: str) -> User:
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_users(db: Session, limit: int = 100, skip: int = 0):
    return db.query(User).offset(skip).limit(limit).all()


def update_user_role(db: Session, user_id: int, is_superuser: bool) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if user:
        user.is_superuser = is_superuser
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def update_user_status(db: Session, user_id: int, is_active: bool) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = is_active
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_user_stats(db: Session):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    superusers = db.query(User).filter(User.is_superuser.is_(True)).count()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "superusers": superusers
    }
