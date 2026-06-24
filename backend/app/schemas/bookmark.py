from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class BookmarkBase(BaseModel):
    item_type: str  # "Medicine" (Dược phẩm) hoặc "Disease" (Bệnh lý)
    item_neo4j_id: str

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkResponse(BookmarkBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BookmarkList(BaseModel):
    total: int
    items: List[BookmarkResponse]
