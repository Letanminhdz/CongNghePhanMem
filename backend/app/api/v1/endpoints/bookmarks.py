from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.api.v1.endpoints.deps import get_db, get_current_user
from app.models.user import User
from app.services.bookmark_service import bookmark_service
from app.schemas.bookmark import BookmarkCreate, BookmarkResponse, BookmarkList

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])

@router.post("/", response_model=BookmarkResponse)
def create_bookmark(
    request: BookmarkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Đánh dấu (bookmark) một thuốc hoặc bệnh lý.
    """
    return bookmark_service.add_bookmark(db, int(current_user.id), request)

@router.get("/", response_model=BookmarkList)
def get_bookmarks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    item_type: Optional[str] = Query(None, description="Filter by 'Medicine' or 'Disease'"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Lấy danh sách các đánh dấu (bookmark) của người dùng hiện tại.
    """
    return bookmark_service.get_bookmarks(db, int(current_user.id), item_type, limit, skip)

@router.delete("/{id}")
def delete_bookmark(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Xóa một đánh dấu (bookmark) theo ID.
    """
    success = bookmark_service.remove_bookmark(db, int(id), int(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"success": True, "message": "Bookmark removed"}
