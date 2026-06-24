from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class ChatHistory(Base):
    """
    Model lưu trữ lịch sử các cuộc hội thoại giữa người dùng và trợ lý ảo (chatbot).
    """
    __tablename__ = "chathistory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ID tự tăng của bản ghi lịch sử chat
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)  # Khóa ngoại liên kết tới người dùng (user) thực hiện cuộc chat
    message = Column(Text, nullable=False)  # Nội dung câu hỏi/tin nhắn của người dùng gửi cho chatbot
    response = Column(Text, nullable=False)  # Câu trả lời của chatbot trả về cho người dùng
    intent = Column(String, index=True)  # Ý định (intent) được chatbot phân tích từ tin nhắn của người dùng
    entities = Column(Text)  # Chuỗi JSON lưu các thực thể y khoa đã trích xuất được từ tin nhắn (ví dụ: tên thuốc, bệnh lý)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Thời điểm tạo bản ghi hội thoại, mặc định là thời điểm hiện tại
