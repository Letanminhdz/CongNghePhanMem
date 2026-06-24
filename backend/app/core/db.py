from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import engine
from app.models.user import User
from app.repositories.user_repository import create_user, get_user_by_email
from app.schemas.user import UserCreate


def init_db(session: Session) -> None:
    """
    Mục đích: Khởi tạo cơ sở dữ liệu SQL ban đầu bằng cách tự động tạo tài khoản Admin (superuser) đầu tiên.
    Cơ chế hoạt động: Kiểm tra xem tài khoản email admin chỉ định trong `settings` đã tồn tại chưa. Nếu chưa, tạo mới tài khoản admin này với cờ `is_superuser=True`.
    """
    # session: Phiên làm việc với SQL Database
    # existing_user: Đối tượng người dùng đã tồn tại trong cơ sở dữ liệu nếu có
    existing_user = get_user_by_email(session, settings.FIRST_SUPERUSER)
    if not existing_user:
        # user_in: Dữ liệu schema dùng để tạo tài khoản admin đầu tiên lấy từ settings
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
        )
        create_user(session, user_in, is_superuser=True)
        
    existing_regular_user = get_user_by_email(session, settings.FIRST_USER)
    if not existing_regular_user:
        user_regular_in = UserCreate(
            email=settings.FIRST_USER,
            password=settings.FIRST_USER_PASSWORD,
        )
        create_user(session, user_regular_in, is_superuser=False)
