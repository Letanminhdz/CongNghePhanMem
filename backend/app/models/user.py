from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    """
    Model lưu trữ thông tin tài khoản người dùng trong hệ thống.
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ID tự tăng, khóa chính của người dùng
    full_name = Column(String, index=True)  # Họ và tên của người dùng
    email = Column(String, unique=True, index=True, nullable=False)  # Địa chỉ email duy nhất, dùng để đăng nhập và định danh tài khoản
    hashed_password = Column(String, nullable=False)  # Mật khẩu người dùng đã được băm để bảo mật
    is_active = Column(Boolean(), default=True)  # Trạng thái hoạt động của tài khoản (True: đang hoạt động, False: bị vô hiệu hóa)
    is_superuser = Column(Boolean(), default=False)  # Quyền quản trị viên cao cấp (True: là admin, False: là người dùng thường)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Thời điểm tài khoản được tạo, mặc định là thời điểm hiện tại
