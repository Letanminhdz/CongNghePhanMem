from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.bookmark import Bookmark
from app.schemas.bookmark import BookmarkCreate

def create_bookmark(db: Session, user_id: int, bookmark_in: BookmarkCreate) -> Bookmark:
    """
    Tạo bản ghi đánh dấu (bookmark) mới trong cơ sở dữ liệu PostgreSQL.
    """
    db_bookmark = Bookmark(
        user_id=user_id,
        item_type=bookmark_in.item_type,
        item_neo4j_id=bookmark_in.item_neo4j_id
    )
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    return db_bookmark

def get_user_bookmarks(db: Session, user_id: int, item_type: Optional[str] = None, limit: int = 20, skip: int = 0) -> List[Bookmark]:
    """
    Truy vấn danh sách các đánh dấu của người dùng (hỗ trợ lọc theo loại và phân trang).
    """
    query = db.query(Bookmark).filter(Bookmark.user_id == user_id)
    if item_type:
        query = query.filter(Bookmark.item_type == item_type)
    return query.order_by(Bookmark.created_at.desc()).offset(skip).limit(limit).all()

def delete_bookmark(db: Session, bookmark_id: int, user_id: int) -> bool:
    """
    Xóa bản ghi đánh dấu khỏi cơ sở dữ liệu dựa trên ID đánh dấu và ID người dùng.
    """
    result = db.query(Bookmark).filter(Bookmark.id == bookmark_id, Bookmark.user_id == user_id).delete()
    db.commit()
    return result > 0

def get_bookmark_by_item(db: Session, user_id: int, item_type: str, item_neo4j_id: str) -> Optional[Bookmark]:
    """
    Kiểm tra và lấy ra bản ghi đánh dấu cụ thể dựa trên thực thể Neo4j để tránh trùng lặp.
    """
    return db.query(Bookmark).filter(
        Bookmark.user_id == user_id,
        Bookmark.item_type == item_type,
        Bookmark.item_neo4j_id == item_neo4j_id
    ).first()
