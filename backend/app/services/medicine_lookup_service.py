"""
Dịch vụ tra cứu thuốc.
Điều phối các hoạt động liên quan đến thuốc giữa repository và schemas.
"""

import logging
from typing import Any

from app.repositories.medicine_repository import medicine_repository

logger = logging.getLogger(__name__)


class MedicineLookupService:
    """Dịch vụ truy xuất và quản lý thông tin thuốc."""

    def __init__(self):
        self._repository = medicine_repository

    def get_medicine_detail(self, name: str) -> dict[str, Any] | None:
        """Lấy thông tin chi tiết đầy đủ của một loại thuốc."""
        return self._repository.get_medicine_by_name(name)

    def search_medicines(self, query: str, limit: int = 10, skip: int = 0) -> dict[str, Any]:
        """Tìm kiếm thuốc kèm theo metadata phân trang."""
        items = self._repository.search_medicines(query, limit, skip)
        # Trong ứng dụng thực tế, chúng ta có thể cần phân trang phức tạp hơn
        return {
            "query": query,
            "limit": limit,
            "skip": skip,
            "total": len(items),
            "items": items
        }

    def get_medicines_by_disease(
        self, disease_name: str, limit: int = 10, skip: int = 0
    ) -> dict[str, Any]:
        """Lấy danh sách các loại thuốc điều trị một bệnh cụ thể."""
        items = self._repository.get_medicines_by_disease(disease_name, limit, skip)
        return {
            "disease_name": disease_name,
            "limit": limit,
            "skip": skip,
            "total": len(items),
            "items": items
        }

    def get_medicine_ingredients(self, name: str) -> list[dict[str, Any]]:
        """Lấy các thành phần hoạt chất của một loại thuốc."""
        return self._repository.get_medicine_ingredients(name)

    def create_medicine(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Tạo một loại thuốc mới (Admin)."""
        return self._repository.create_medicine(data)

    def update_medicine(self, name: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Cập nhật thuốc hiện có (Admin)."""
        return self._repository.update_medicine(name, data)

    def delete_medicine(self, name: str) -> bool:
        """Xóa thuốc (Admin)."""
        return self._repository.delete_medicine(name)


medicine_lookup_service = MedicineLookupService()
