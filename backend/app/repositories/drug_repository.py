"""
Drug repository for Neo4j operations.
Handles drug lookups, searches, and relationships.
"""

import logging
from typing import Any

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class DrugRepository:
    """Repository for drug-related Neo4j operations."""

    def __init__(self):
        self._repository = neo4j_repository

    def get_drug_by_name(self, drug_name: str) -> dict[str, Any] | None:
        """
        Get a drug by exact name with all related information.
        """
        query = """
        MATCH (d:Drug {name: $name})
        OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
        OPTIONAL MATCH (m:Manufacturer)-[:PRODUCES]->(d)
        OPTIONAL MATCH (d)-[int:INTERACTS_WITH]->(d2:Drug)
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            d.generic_name AS generic_name,
            d.manufacturer AS manufacturer,
            d.purpose AS purpose,
            d.indications AS indications,
            d.warnings AS warnings,
            d.dosage AS dosage,
            d.updated_at AS updated_at,
            collect(DISTINCT i.name) AS ingredients,
            collect(DISTINCT m.name) AS manufacturers,
            collect({
                name: d2.name,
                severity: int.severity,
                description: int.description
            }) AS interactions
        """
        try:
            results = self._repository.execute_read(query, name=drug_name)
            if results:
                return results[0]
            return None
        except Exception as exc:
            logger.error(f"Error retrieving drug '{drug_name}': {exc}")
            return None

    def search_drugs(self, query_str: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search for drugs by name, brand name, or generic name.
        """
        query = """
        MATCH (d:Drug)
        WHERE d.name CONTAINS $query 
           OR d.brand_name CONTAINS $query 
           OR d.generic_name CONTAINS $query
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            d.generic_name AS generic_name,
            d.manufacturer AS manufacturer,
            d.purpose AS purpose,
            d.indications AS indications,
            d.dosage AS dosage
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                query, query=query_str, limit=limit
            )
            return results if results else []
        except Exception as exc:
            logger.error(f"Error searching drugs with query '{query_str}': {exc}")
            return []

    def get_drugs_by_disease(
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
                f"Error getting drugs for disease '{disease_name}': {exc}"
            )
            return []

    def get_drug_interactions(self, drug_name: str) -> list[dict[str, Any]]:
        """
        Get all drugs that interact with a specific drug.
        """
        query = """
        MATCH (drug:Drug {name: $drug_name})
        MATCH (drug)-[int:INTERACTS_WITH]->(d:Drug)
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            int.severity AS severity,
            int.description AS description
        """
        try:
            results = self._repository.execute_read(query, drug_name=drug_name)
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
        Check interactions between multiple drugs.
        Returns all pairs that have interactions.
        """
        if not drug_names or len(drug_names) < 2:
            return []

        # Build the WHERE clause with drug names
        drug_list = ",".join([f"'{name}'" for name in drug_names])
        query = f"""
        MATCH (d:Drug)-[int:INTERACTS_WITH]->(d2:Drug)
        WHERE d.name IN [{drug_list}] AND d2.name IN [{drug_list}]
        RETURN 
            d.name AS drug_1,
            d2.name AS drug_2,
            int.severity AS severity,
            int.description AS description
        """
        try:
            results = self._repository.execute_read(query)
            return results if results else []
        except Exception as exc:
            logger.error(f"Error checking multiple drug interactions: {exc}")
            return []

    def get_drug_ingredients(self, drug_name: str) -> list[dict[str, Any]]:
        """
        Get all ingredients in a drug.
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

    def get_drug_count(self) -> int:
        """
        Get total count of drugs in database.
        """
        query = "MATCH (d:Drug) RETURN COUNT(d) AS count"
        try:
            results = self._repository.execute_read(query)
            if results:
                return results[0].get("count", 0)
            return 0
        except Exception as exc:
            logger.error(f"Error counting drugs: {exc}")
            return 0


drug_repository = DrugRepository()
