from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class SearchHistory(Base):
    """
    Model lưu trữ lịch sử tìm kiếm dược phẩm hoặc bệnh lý của người dùng.
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ID tự tăng của bản ghi lịch sử tìm kiếm
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)  # Khóa ngoại liên kết tới người dùng (user) thực hiện tìm kiếm
    query_text = Column(String, index=True, nullable=False)  # Văn bản/từ khóa truy vấn được tìm kiếm
    item_type = Column(String, nullable=True)  # Loại đối tượng tìm kiếm: "Medicine" (Dược phẩm) hoặc "Disease" (Bệnh lý)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Thời điểm thực hiện tìm kiếm, mặc định là thời điểm hiện tại
