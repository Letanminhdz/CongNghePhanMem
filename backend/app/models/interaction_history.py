from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class InteractionHistory(Base):
    """
    Model lưu trữ lịch sử kiểm tra tương tác thuốc của người dùng.
    """
    __tablename__ = "interaction_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ID tự tăng của bản ghi lịch sử kiểm tra tương tác
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)  # Khóa ngoại liên kết tới người dùng (user) thực hiện kiểm tra
    drugs = Column(String, nullable=False)  # Danh sách tên các thuốc được kiểm tra cùng nhau (ví dụ: "Aspirin, Ibuprofen")
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Thời điểm tạo bản ghi kiểm tra, mặc định là thời điểm hiện tại
