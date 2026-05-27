from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import engine
from app.models.user import User
from app.repositories.user_repository import create_user, get_user_by_email
from app.schemas.user import UserCreate


def init_db(session: Session) -> None:
    existing_user = get_user_by_email(session, settings.FIRST_SUPERUSER)
    if not existing_user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
        )
        create_user(session, user_in)
