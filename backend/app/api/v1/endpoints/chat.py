from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.api.v1.endpoints.deps import get_db, get_current_user, get_optional_current_user
from app.models.user import User
from app.services.chat_service import chat_service
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryList, ChatHistoryItem

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask", response_model=ChatMessageResponse)
async def ask_question(
    request: ChatMessageRequest,
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Tương tác với Trợ lý ảo Y tế (Medical Chatbot).
    Câu trả lời bao gồm phản hồi từ AI, các thực thể được phát hiện, nguồn tham khảo và các cảnh báo an toàn.
    """
    user_id = current_user.id if current_user else None
    return await chat_service.process_chat(db, user_id, request.message)

@router.get("/history", response_model=ChatHistoryList)
def get_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20
):
    """
    Lấy lịch sử chat của người dùng hiện tại.
    """
    history = chat_service.get_user_history(db, current_user.id, limit=limit)
    total = chat_service.get_chat_logs_count(db, user_id=current_user.id)
    return {"total": total, "items": history}

@router.get("/history/{id}", response_model=ChatHistoryItem)
def get_chat_detail(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Lấy thông tin chi tiết một lượt chat cụ thể từ lịch sử.
    """
    from fastapi import HTTPException
    chat = chat_service.get_chat_detail(db, id, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat history not found")
    return chat
