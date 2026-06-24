from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ChatMessageResponse(BaseModel):
    answer: str
    entities: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ChatHistoryItem(BaseModel):
    id: int
    message: str
    response: str
    intent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryList(BaseModel):
    total: int
    items: List[ChatHistoryItem]


class AILogResponse(BaseModel):
    total: int
    items: List[ChatHistoryItem]
    page: int
    limit: int
