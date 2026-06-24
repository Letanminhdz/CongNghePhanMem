from sqlalchemy.orm import Session
from app.repositories import search_history_repository
from app.schemas.search_history import SearchHistoryCreate, SearchHistoryResponse, SearchHistoryList

class SearchHistoryService:
    """
    Dịch vụ quản lý lịch sử tìm kiếm các thuốc và bệnh lý của người dùng.
    """

    def add_search_entry(self, db: Session, user_id: int, search_in: SearchHistoryCreate) -> SearchHistoryResponse:
        """
        Thêm một bản ghi lịch sử tìm kiếm mới cho người dùng.
        """
        db_search = search_history_repository.create_search_history(db, user_id, search_in)
        return SearchHistoryResponse.model_validate(db_search)

    def get_history(self, db: Session, user_id: int, limit: int = 20, skip: int = 0) -> SearchHistoryList:
        """
        Lấy toàn bộ danh sách lịch sử tìm kiếm của người dùng hiện tại (hỗ trợ phân trang).
        """
        history = search_history_repository.get_user_search_history(db, user_id, limit, skip)
        total = search_history_repository.get_user_search_history_count(db, user_id)
        return SearchHistoryList(
            total=total,
            items=[SearchHistoryResponse.model_validate(item) for item in history]
        )

    def clear_history(self, db: Session, user_id: int) -> bool:
        """
        Xóa toàn bộ lịch sử tìm kiếm của một người dùng.
        """
        search_history_repository.delete_user_search_history(db, user_id)
        return True

    def delete_history_entry(self, db: Session, user_id: int, entry_id: int) -> bool:
        """
        Xóa một bản ghi lịch sử tìm kiếm cụ thể bằng ID.
        """
        return search_history_repository.delete_search_history_entry(db, user_id, entry_id)

    def get_top_searches(self, db: Session, item_type: str = "medicine", limit: int = 5):
        """
        Lấy các từ khóa tìm kiếm phổ biến hàng đầu hệ thống theo phân loại thực thể.
        """
        return search_history_repository.get_top_searches(db, item_type, limit)

search_history_service = SearchHistoryService()
