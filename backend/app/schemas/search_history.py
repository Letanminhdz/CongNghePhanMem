from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SearchHistoryBase(BaseModel):
    query_text: str
    item_type: Optional[str] = None

class SearchHistoryCreate(SearchHistoryBase):
    pass

class SearchHistoryResponse(SearchHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SearchHistoryList(BaseModel):
    total: int
    items: List[SearchHistoryResponse]
