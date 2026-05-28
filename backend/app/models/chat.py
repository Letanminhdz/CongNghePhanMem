from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class ChatHistory(Base):
    __tablename__ = "chathistory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    intent = Column(String, index=True)
    entities = Column(Text)  # JSON string of extracted entities
    created_at = Column(DateTime(timezone=True), server_default=func.now())
