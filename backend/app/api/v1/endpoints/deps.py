from collections.abc import Generator
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories import user_repository
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

reusable_oauth2_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    auto_error=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Mục đích: Khởi tạo và quản lý vòng đời của phiên kết nối cơ sở dữ liệu (Database Session) cho mỗi Request.
    Cơ chế hoạt động: Tạo Session mới và giải phóng (close) sau khi xử lý Request hoàn tất.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
):
    """
    Mục đích: Xác thực người dùng hiện tại thông qua mã JWT Bearer Token được gửi kèm trong request header.
    Cơ chế hoạt động: Giải mã token, trích xuất ID người dùng, truy vấn thông tin trong cơ sở dữ liệu và trả về đối tượng User.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, Exception):
        raise credentials_exception

    user = user_repository.get_user_by_id(db, user_id=int(token_data.sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(reusable_oauth2_optional),
) -> User | None:
    """
    Mục đích: Lấy thông tin người dùng hiện tại nếu có gửi token (không bắt buộc).
    Cơ chế hoạt động: Giải mã token nếu tồn tại. Trả về thông tin người dùng nếu hợp lệ hoặc None nếu không có hoặc không hợp lệ.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, Exception):
        return None

    user = user_repository.get_user_by_id(db, user_id=int(token_data.sub))
    if not user or not user.is_active:
        return None
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Mục đích: Kiểm tra xem người dùng hiện tại có ở trạng thái đang hoạt động (active) hay không.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Mục đích: Kiểm tra xem người dùng hiện tại có phải là quản trị viên hệ thống (superuser/admin) hay không.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
