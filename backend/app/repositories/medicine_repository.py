"""
Repository dược phẩm/thuốc cho các thao tác Neo4j.
Xử lý các tra cứu, tìm kiếm và mối quan hệ của dược phẩm/thuốc.
"""

import logging
from typing import Any

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class MedicineRepository:
    """Repository cho các thao tác Neo4j liên quan đến dược phẩm/thuốc."""

    def __init__(self):
        self._repository = neo4j_repository

    def get_medicine_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Lấy thông tin thuốc theo tên chính xác cùng với tất cả thông tin liên quan.
        """
        query = """
        MATCH (m:Drug)
        WHERE toLower(trim(m.name)) = toLower(trim($name))
           OR toLower(trim(coalesce(m.brand_name, ""))) = toLower(trim($name))
           OR toLower(trim(coalesce(m.generic_name, ""))) = toLower(trim($name))
        RETURN 
            m.name AS name,
            m.brand_name AS brand_name,
            m.generic_name AS generic_name,
            coalesce(m.manufacturer, [(m)-[:MADE_BY]->(man:Manufacturer) | man.name][0]) AS manufacturer,
            m.purpose AS purpose,
            m.indications AS indications,
            m.warnings AS warnings,
            m.dosage AS dosage,
            m.contraindications AS contraindications,
            m.adverse_reactions AS adverse_reactions,
            m.updated_at AS updated_at,
            [(m)-[:CONTAINS]->(i:Ingredient) | i.name] AS ingredients,
            [(m)-[:MADE_BY]->(man:Manufacturer) | man.name] AS manufacturers,
            [(m)-[:TREATS]->(dis:Disease) | dis.name] AS treated_diseases,
            [(m)-[int:INTERACTS_WITH]-(m2:Drug) | {
                name: m2.name,
                severity: int.severity,
                description: int.description
            }] AS interactions
        """
        try:
            results = self._repository.execute_read(query, name=name)
            if results:
                return results[0]
            return None
        except Exception as exc:
            logger.error(f"Error retrieving medicine '{name}': {exc}")
            return None

    def search_medicines(self, query_str: str, limit: int = 10, skip: int = 0) -> list[dict[str, Any]]:
        """
        Tìm kiếm thuốc theo tên thương mại, nhãn hiệu hoặc tên chung (generic).
        """
        cypher_query = """
        MATCH (m:Drug)
        WHERE toLower(coalesce(m.name, "")) CONTAINS toLower($search_query) 
           OR toLower(coalesce(m.brand_name, "")) CONTAINS toLower($search_query) 
           OR toLower(coalesce(m.generic_name, "")) CONTAINS toLower($search_query)
        RETURN 
            m.name AS name,
            m.brand_name AS brand_name,
            m.generic_name AS generic_name,
            coalesce(m.manufacturer, [(m)-[:MADE_BY]->(man:Manufacturer) | man.name][0]) AS manufacturer,
            m.purpose AS purpose,
            m.indications AS indications,
            m.dosage AS dosage
        ORDER BY m.name ASC
        SKIP $skip
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                cypher_query, search_query=query_str, limit=limit, skip=skip
            )
            return results if results else []
        except Exception as exc:
            logger.error(f"Error searching medicines with query '{query_str}': {exc}")
            return []

    def get_medicines_by_disease(
        self, disease_name: str, limit: int = 10, skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách các thuốc điều trị một bệnh lý cụ thể.
        """
        query = """
        MATCH (disease:Disease {name: $disease_name})
        MATCH (medicine:Drug)-[:TREATS]->(disease)
        RETURN 
            medicine.name AS name,
            medicine.brand_name AS brand_name,
            medicine.generic_name AS generic_name,
            medicine.dosage AS dosage
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
                f"Error getting medicines for disease '{disease_name}': {exc}"
            )
            return []

    def get_medicine_interactions(self, name: str, limit: int = 10, skip: int = 0) -> list[dict[str, Any]]:
        """
        Lấy tất cả các loại thuốc có tương tác với một thuốc cụ thể.
        """
        query = """
        MATCH (medicine:Drug {name: $name})
        MATCH (medicine)-[int:INTERACTS_WITH]-(m2:Drug)
        RETURN 
            m2.name AS name,
            m2.brand_name AS brand_name,
            int.severity AS severity,
            int.description AS description
        SKIP $skip
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(query, name=name, limit=limit, skip=skip)
            return results if results else []
        except Exception as exc:
            logger.error(
                f"Error getting interactions for medicine '{name}': {exc}"
            )
            return []

    def check_multiple_medicine_interactions(
        self, names: list[str]
    ) -> list[dict[str, Any]]:
        """
        Kiểm tra tương tác giữa nhiều loại thuốc.
        Trả về tất cả các cặp thuốc có xảy ra tương tác.
        """
        if not names or len(names) < 2:
            return []

        query = """
        MATCH (m1:Drug)-[int:INTERACTS_WITH]-(m2:Drug)
        WHERE m1.name IN $names AND m2.name IN $names
        RETURN 
            m1.name AS medicine_1,
            m2.name AS medicine_2,
            int.severity AS severity,
            int.description AS description
        """
        try:
            results = self._repository.execute_read(query, names=names)
            return results if results else []
        except Exception as exc:
            logger.error(f"Error checking multiple medicine interactions: {exc}")
            return []

    def get_medicine_ingredients(self, name: str) -> list[dict[str, Any]]:
        """
        Lấy tất cả các thành phần có trong một loại thuốc.
        """
        query = """
        MATCH (m:Drug {name: $name})
        MATCH (m)-[:CONTAINS]->(i:Ingredient)
        RETURN 
            i.name AS name,
            i.description AS description
        """
        try:
            results = self._repository.execute_read(query, name=name)
            return results if results else []
        except Exception as exc:
            logger.error(f"Error getting ingredients for medicine '{name}': {exc}")
            return []



    def create_medicine(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Tạo một nút thuốc mới."""
        query = """
        MERGE (m:Drug {name: $name})
        SET m += $props, m.updated_at = datetime()
        RETURN 
            m.name AS name,
            m.brand_name AS brand_name,
            m.generic_name AS generic_name,
            m.manufacturer AS manufacturer,
            m.purpose AS purpose,
            m.indications AS indications,
            m.warnings AS warnings,
            m.dosage AS dosage,
            m.contraindications AS contraindications,
            m.adverse_reactions AS adverse_reactions,
            m.updated_at AS updated_at
        """
        name = data.get("name")
        props = {k: v for k, v in data.items() if k != "name"}
        try:
            results = self._repository.execute_write(query, name=name, props=props)
            return results[0] if results else None
        except Exception as exc:
            logger.error(f"Error creating medicine '{name}': {exc}")
            return None

    def update_medicine(self, name: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Cập nhật một nút thuốc hiện có."""
        query = """
        MATCH (m:Drug {name: $name})
        SET m += $props, m.updated_at = datetime()
        RETURN 
            m.name AS name,
            m.brand_name AS brand_name,
            m.generic_name AS generic_name,
            m.manufacturer AS manufacturer,
            m.purpose AS purpose,
            m.indications AS indications,
            m.warnings AS warnings,
            m.dosage AS dosage,
            m.contraindications AS contraindications,
            m.adverse_reactions AS adverse_reactions,
            m.updated_at AS updated_at
        """
        try:
            results = self._repository.execute_write(query, name=name, props=data)
            return results[0] if results else None
        except Exception as exc:
            logger.error(f"Error updating medicine '{name}': {exc}")
            return None

    def delete_medicine(self, name: str) -> bool:
        """Xóa một nút thuốc và các mối quan hệ của nó."""
        query = """
        MATCH (m:Drug {name: $name})
        DETACH DELETE m
        """
        try:
            self._repository.execute_write(query, name=name)
            return True
        except Exception as exc:
            logger.error(f"Error deleting medicine '{name}': {exc}")
            return False


medicine_repository = MedicineRepository()
