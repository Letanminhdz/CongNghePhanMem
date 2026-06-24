from sqlalchemy.orm import Session
from app.models.interaction_history import InteractionHistory

def log_interaction_check(db: Session, user_id: int, drugs: list[str]) -> InteractionHistory:
    """
    Mục đích: Lưu vết lịch sử kiểm tra tương tác thuốc của người dùng đã đăng nhập vào PostgreSQL.
    """
    entry = InteractionHistory(
        user_id=user_id,
        drugs=", ".join(drugs)
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_user_interaction_count(db: Session, user_id: int) -> int:
    """
    Mục đích: Đếm tổng số lượt kiểm tra tương tác thuốc của một người dùng.
    """
    return db.query(InteractionHistory).filter(InteractionHistory.user_id == user_id).count()
