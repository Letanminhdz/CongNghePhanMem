"""
Repository thuốc cho các thao tác Neo4j.
Xử lý các tra cứu, tìm kiếm và mối quan hệ của thuốc.
"""

import logging
from typing import Any

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class DrugRepository:
    """Repository cho các thao tác Neo4j liên quan đến thuốc."""

    def __init__(self):
        self._repository = neo4j_repository

    def get_drug_by_name(self, drug_name: str) -> dict[str, Any] | None:
        """
        Lấy thông tin thuốc theo tên chính xác cùng với tất cả thông tin liên quan.
        """
        query = """
        MATCH (d:Drug)
        WHERE toLower(trim(d.name)) = toLower(trim($name))
           OR toLower(trim(coalesce(d.brand_name, ""))) = toLower(trim($name))
           OR toLower(trim(coalesce(d.generic_name, ""))) = toLower(trim($name))
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            d.generic_name AS generic_name,
            d.manufacturer AS manufacturer,
            d.purpose AS purpose,
            d.indications AS indications,
            d.warnings AS warnings,
            d.dosage AS dosage,
            d.contraindications AS contraindications,
            d.adverse_reactions AS adverse_reactions,
            d.updated_at AS updated_at,
            [(d)-[:CONTAINS]->(i:Ingredient) | i.name] AS ingredients,
            [(d)-[:MADE_BY]->(m:Manufacturer) | m.name] AS manufacturers,
            [(d)-[:TREATS]->(dis:Disease) | dis.name] AS treated_diseases,
            [(d)-[int:INTERACTS_WITH]-(d2:Drug) | {
                name: d2.name,
                severity: int.severity,
                description: int.description
            }] AS interactions
        """
        try:
            results = self._repository.execute_read(query, name=drug_name)
            if results:
                return results[0]
            return None
        except Exception as exc:
            logger.error(f"Error retrieving drug '{drug_name}': {exc}")
            return None

    def search_drugs(self, query_str: str, limit: int = 10, skip: int = 0) -> list[dict[str, Any]]:
        """
        Tìm kiếm thuốc theo tên thương mại, nhãn hiệu hoặc tên chung (generic).
        """
        query = """
        MATCH (d:Drug)
        WHERE toLower(coalesce(d.name, "")) CONTAINS toLower($query) 
           OR toLower(coalesce(d.brand_name, "")) CONTAINS toLower($query) 
           OR toLower(coalesce(d.generic_name, "")) CONTAINS toLower($query)
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            d.generic_name AS generic_name,
            d.manufacturer AS manufacturer,
            d.purpose AS purpose,
            d.indications AS indications,
            d.dosage AS dosage
        SKIP $skip
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                query, query=query_str, limit=limit, skip=skip
            )
            return results if results else []
        except Exception as exc:
            logger.error(f"Error searching drugs with query '{query_str}': {exc}")
            return []

    def get_drugs_by_disease(
        self, disease_name: str, limit: int = 10, skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách các thuốc điều trị một bệnh lý cụ thể.
        """
        query = """
        MATCH (disease:Disease {name: $disease_name})
        MATCH (drug:Drug)-[:TREATS]->(disease)
        RETURN 
            drug.name AS name,
            drug.brand_name AS brand_name,
            drug.generic_name AS generic_name,
            drug.dosage AS dosage
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
                f"Error getting drugs for disease '{disease_name}': {exc}"
            )
            return []

    def get_drug_interactions(self, drug_name: str, limit: int = 10, skip: int = 0) -> list[dict[str, Any]]:
        """
        Lấy tất cả các loại thuốc có tương tác với một thuốc cụ thể.
        """
        query = """
        MATCH (drug:Drug {name: $drug_name})
        MATCH (drug)-[int:INTERACTS_WITH]-(d:Drug)
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            int.severity AS severity,
            int.description AS description
        SKIP $skip
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(query, drug_name=drug_name, limit=limit, skip=skip)
            return results if results else []
        except Exception as exc:
            logger.error(
                f"Error getting interactions for drug '{drug_name}': {exc}"
            )
            return []

    def check_multiple_drug_interactions(
        self, drug_names: list[str]
    ) -> list[dict[str, Any]]:
        """
        Kiểm tra tương tác giữa nhiều loại thuốc.
        Trả về tất cả các cặp thuốc có xảy ra tương tác.
        """
        if not drug_names or len(drug_names) < 2:
            return []

        query = """
        MATCH (d:Drug)-[int:INTERACTS_WITH]-(d2:Drug)
        WHERE d.name IN $drug_names AND d2.name IN $drug_names
        RETURN 
            d.name AS drug_1,
            d2.name AS drug_2,
            int.severity AS severity,
            int.description AS description
        """
        try:
            results = self._repository.execute_read(query, drug_names=drug_names)
            return results if results else []
        except Exception as exc:
            logger.error(f"Error checking multiple drug interactions: {exc}")
            return []

    def get_drug_ingredients(self, drug_name: str) -> list[dict[str, Any]]:
        """
        Lấy tất cả các thành phần có trong một loại thuốc.
        """
        query = """
        MATCH (d:Drug {name: $drug_name})
        MATCH (d)-[:CONTAINS]->(i:Ingredient)
        RETURN 
            i.name AS name,
            i.description AS description
        """
        try:
            results = self._repository.execute_read(query, drug_name=drug_name)
            return results if results else []
        except Exception as exc:
            logger.error(f"Error getting ingredients for drug '{drug_name}': {exc}")
            return []




drug_repository = DrugRepository()
