from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Bookmark(Base):
    """
    Model đại diện cho tính năng đánh dấu (bookmark) thuốc hoặc bệnh lý của người dùng.
    """
    __tablename__ = "bookmark"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ID tự tăng của bản ghi đánh dấu
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)  # Khóa ngoại liên kết tới người dùng (user) sở hữu đánh dấu này
    item_type = Column(String, index=True, nullable=False)  # Loại đối tượng đánh dấu: "Medicine" (Dược phẩm) hoặc "Disease" (Bệnh lý)
    item_neo4j_id = Column(String, index=True, nullable=False) # Lưu tên hoặc ID Neo4j của đối tượng được đánh dấu
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Thời gian tạo đánh dấu, mặc định là thời điểm hiện tại
