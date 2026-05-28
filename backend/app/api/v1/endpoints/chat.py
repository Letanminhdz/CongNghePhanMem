from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.api.v1.endpoints.deps import get_db, get_current_user
from app.models.user import User
from app.services.chat_service import chat_service
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryList

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatMessageResponse)
async def chat_with_ai(
    request: ChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Interact with the Medical Chatbot.
    The response includes AI answer, detected entities, sources, and safety warnings.
    """
    return await chat_service.process_chat(db, current_user.id, request.message)

@router.get("/history", response_model=ChatHistoryList)
def get_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20
):
    """
    Retrieve the current user's chat history.
    """
    history = chat_service.get_user_history(db, current_user.id, limit=limit)
    return ChatHistoryList(total=len(history), items=history)
