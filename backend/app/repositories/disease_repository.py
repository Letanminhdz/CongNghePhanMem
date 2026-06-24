"""
Repository bệnh lý cho các thao tác Neo4j.
Xử lý các tìm kiếm và truy xuất thông tin bệnh lý.
"""

import logging
from typing import Any

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class DiseaseRepository:
    """Repository cho các thao tác Neo4j liên quan đến bệnh lý."""

    def __init__(self):
        self._repository = neo4j_repository

    def get_disease_by_name(self, disease_name: str) -> dict[str, Any] | None:
        """
        Lấy thông tin bệnh lý theo tên chính xác cùng với tất cả thông tin liên quan.
        """
        query = """
        MATCH (d:Disease {name: $name})
        OPTIONAL MATCH (m:Drug)-[:TREATS]->(d)
        OPTIONAL MATCH (d)-[:HAS_SYMPTOM|RELATED_TO]->(s:Symptom)
        RETURN 
            d.name AS name,
            d.description AS description,
            d.icd_code AS icd_code,
            d.category AS category,
            d.severity AS severity,
            d.updated_at AS updated_at,
            collect(DISTINCT m.name) AS treating_medicines,
            collect(DISTINCT {name: s.name, description: s.description}) AS symptoms
        """
        try:
            results = self._repository.execute_read(query, name=disease_name)
            if results:
                return results[0]
            return None
        except Exception as exc:
            logger.error(f"Error retrieving disease '{disease_name}': {exc}")
            return None

    def search_diseases(self, query_str: str, limit: int = 10, skip: int = 0) -> list[dict[str, Any]]:
        """
        Tìm kiếm bệnh lý theo tên hoặc mô tả.
        """
        cypher_query = """
        MATCH (d:Disease)
        WHERE toLower(coalesce(d.name, "")) CONTAINS toLower($search_query) 
           OR toLower(coalesce(d.description, "")) CONTAINS toLower($search_query)
        RETURN 
            d.name AS name,
            d.description AS description,
            d.icd_code AS icd_code,
            d.category AS category,
            d.severity AS severity
        ORDER BY d.name ASC
        SKIP $skip
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                cypher_query, search_query=query_str, limit=limit, skip=skip
            )
            return results if results else []
        except Exception as exc:
            logger.error(f"Error searching diseases with query '{query_str}': {exc}")
            return []

    def get_treating_medicines(
        self, disease_name: str, limit: int = 10, skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách các thuốc điều trị một bệnh lý cụ thể.
        """
        query = """
        MATCH (disease:Disease {name: $disease_name})
        MATCH (m:Drug)-[:TREATS]->(disease)
        RETURN 
            m.name AS name,
            m.brand_name AS brand_name,
            m.generic_name AS generic_name,
            m.dosage AS dosage
        SKIP $skip
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                query, disease_name=disease_name, limit=limit, skip=skip
            )
            return results if results else []
        except Exception as exc:
            logger.error(
                f"Error getting treating medicines for disease '{disease_name}': {exc}"
            )
            return []



    def create_disease(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Tạo một nút bệnh lý mới."""
        query = """
        MERGE (d:Disease {name: $name})
        SET d += $props, d.updated_at = datetime()
        RETURN 
            d.name AS name,
            d.description AS description,
            d.icd_code AS icd_code,
            d.category AS category,
            d.severity AS severity,
            d.updated_at AS updated_at
        """
        name = data.get("name")
        props = {k: v for k, v in data.items() if k != "name"}
        try:
            results = self._repository.execute_write(query, name=name, props=props)
            return results[0] if results else None
        except Exception as exc:
            logger.error(f"Error creating disease '{name}': {exc}")
            return None

    def update_disease(self, name: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Cập nhật một nút bệnh lý hiện có."""
        query = """
        MATCH (d:Disease {name: $name})
        SET d += $props, d.updated_at = datetime()
        RETURN 
            d.name AS name,
            d.description AS description,
            d.icd_code AS icd_code,
            d.category AS category,
            d.severity AS severity,
            d.updated_at AS updated_at
        """
        try:
            results = self._repository.execute_write(query, name=name, props=data)
            return results[0] if results else None
        except Exception as exc:
            logger.error(f"Error updating disease '{name}': {exc}")
            return None

    def delete_disease(self, name: str) -> bool:
        """Xóa một nút bệnh lý và các mối quan hệ của nó."""
        query = """
        MATCH (d:Disease {name: $name})
        DETACH DELETE d
        """
        try:
            self._repository.execute_write(query, name=name)
            return True
        except Exception as exc:
            logger.error(f"Error deleting disease '{name}': {exc}")
            return False


disease_repository = DiseaseRepository()
