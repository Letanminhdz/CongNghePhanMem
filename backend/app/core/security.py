from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ALGORITHM: Thuật toán mã hóa ký và xác thực mã JWT
ALGORITHM = "HS256"

# pwd_context: Cấu hình mã hóa mật khẩu sử dụng thuật toán bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Mục đích: Xác minh tính chính xác của mật khẩu thô người dùng nhập so với mật khẩu băm lưu trong DB.
    Cơ chế hoạt động: So sánh mật khẩu thô với mã hash bằng thư viện passlib (bcrypt).
    """
    # plain_password: Mật khẩu chưa mã hóa do người dùng nhập vào
    # hashed_password: Mật khẩu đã băm được lấy từ cơ sở dữ liệu
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Mục đích: Mã hóa băm mật khẩu thô trước khi lưu trữ vào cơ sở dữ liệu để bảo mật.
    Cơ chế hoạt động: Sử dụng thuật toán bcrypt để băm mật khẩu thô.
    """
    # password: Mật khẩu thô cần băm
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Mục đích: Tạo mã thông báo truy cập Access Token định dạng JWT để xác thực các yêu cầu API tiếp theo.
    Cơ chế hoạt động: Tạo payload chứa định danh (`subject`) và thời điểm hết hạn (`exp`), sau đó dùng thư viện `jose` mã hóa JWT với khóa bí mật `SECRET_KEY` và thuật toán HS256.
    """
    # subject: Thông tin định danh người dùng (thường là ID người dùng hoặc email) cần lưu vào token
    # expires_delta: Khoảng thời gian hết hạn tùy chọn của token
    if expires_delta:
        # expire: Thời điểm hết hạn của token
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    # to_encode: Payload dữ liệu thô chuẩn bị mã hóa thành JWT
    to_encode = {"exp": expire, "sub": str(subject)}
    # encoded_jwt: Chuỗi JWT đã được mã hóa và ký số bằng SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
