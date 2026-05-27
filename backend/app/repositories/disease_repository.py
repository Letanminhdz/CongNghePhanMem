"""
Disease repository for Neo4j operations.
Handles disease lookups and searches.
"""

import logging
from typing import Any

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class DiseaseRepository:
    """Repository for disease-related Neo4j operations."""

    def __init__(self):
        self._repository = neo4j_repository

    def get_disease_by_name(self, disease_name: str) -> dict[str, Any] | None:
        """
        Get a disease by exact name with all related information.
        """
        query = """
        MATCH (d:Disease {name: $name})
        OPTIONAL MATCH (drug:Drug)-[:TREATS]->(d)
        RETURN 
            d.name AS name,
            d.description AS description,
            d.icd_code AS icd_code,
            d.updated_at AS updated_at,
            collect(DISTINCT drug.name) AS treating_drugs
        """
        try:
            results = self._repository.execute_read(query, name=disease_name)
            if results:
                return results[0]
            return None
        except Exception as exc:
            logger.error(f"Error retrieving disease '{disease_name}': {exc}")
            return None

    def search_diseases(self, query_str: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search for diseases by name or description.
        """
        query = """
        MATCH (d:Disease)
        WHERE d.name CONTAINS $query 
           OR d.description CONTAINS $query
        RETURN 
            d.name AS name,
            d.description AS description,
            d.icd_code AS icd_code
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                query, query=query_str, limit=limit
            )
            return results if results else []
        except Exception as exc:
            logger.error(f"Error searching diseases with query '{query_str}': {exc}")
            return []

    def get_treating_drugs(
        self, disease_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get drugs that treat a specific disease.
        """
        query = """
        MATCH (disease:Disease {name: $disease_name})
        MATCH (drug:Drug)-[:TREATS]->(disease)
        RETURN 
            drug.name AS name,
            drug.brand_name AS brand_name,
            drug.generic_name AS generic_name,
            drug.dosage AS dosage
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                query, disease_name=disease_name, limit=limit
            )
            return results if results else []
        except Exception as exc:
            logger.error(
                f"Error getting treating drugs for disease '{disease_name}': {exc}"
            )
            return []

    def get_disease_count(self) -> int:
        """
        Get total count of diseases in database.
        """
        query = "MATCH (d:Disease) RETURN COUNT(d) AS count"
        try:
            results = self._repository.execute_read(query)
            if results:
                return results[0].get("count", 0)
            return 0
        except Exception as exc:
            logger.error(f"Error counting diseases: {exc}")
            return 0


disease_repository = DiseaseRepository()
