from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# engine: Đối tượng engine kết nối cơ sở dữ liệu của SQLAlchemy, sử dụng cấu hình URI và bật pool_pre_ping để tự động kiểm tra lại kết nối chết
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)

# SessionLocal: Nhà máy sản xuất phiên làm việc (sessionmaker) dùng để tạo các session kết nối cơ sở dữ liệu của SQL cho từng request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
