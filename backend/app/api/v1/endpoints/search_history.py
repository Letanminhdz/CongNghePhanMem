from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Annotated

from app.api.v1.endpoints.deps import get_db, get_current_user
from app.models.user import User
from app.services.search_history_service import search_history_service
from app.schemas.search_history import SearchHistoryCreate, SearchHistoryList, SearchHistoryResponse

router = APIRouter(prefix="/search/history", tags=["search-history"])

@router.post("/", response_model=SearchHistoryResponse)
def add_search_history(
    request: SearchHistoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Ghi lại lịch sử tìm kiếm cho người dùng hiện tại.
    """
    return search_history_service.add_search_entry(db, int(current_user.id), request)

@router.get("/", response_model=SearchHistoryList)
def get_search_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Lấy danh sách lịch sử tìm kiếm của người dùng hiện tại.
    """
    return search_history_service.get_history(db, int(current_user.id), limit=limit, skip=skip)

@router.delete("/{id}")
def delete_search_history(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Xóa một mục cụ thể trong lịch sử tìm kiếm.
    """
    success = search_history_service.delete_history_entry(db, int(current_user.id), id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Search history entry not found")
    return {"success": True}
