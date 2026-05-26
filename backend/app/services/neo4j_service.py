"""
Neo4j Database Service.

Handles all Neo4j operations with proper session management,
error handling, and logging.
"""

import logging
from typing import Any, Optional

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j database service with singleton pattern."""

    _instance: Optional["Neo4jService"] = None

    def __new__(cls) -> "Neo4jService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._repository = neo4j_repository

    def verify_connectivity(self) -> bool:
        return self._repository.verify_connectivity()

    # ============================================
    # DRUG OPERATIONS
    # ============================================

    def merge_drug(self, drug_data: dict[str, Any]) -> bool:
        try:
            query = """
            MERGE (d:Drug {name: $name})
            SET d.generic_name = $generic_name,
                d.purpose = $purpose,
                d.indications = $indications,
                d.warnings = $warnings,
                d.dosage = $dosage,
                d.updated_at = datetime()
            RETURN d.name AS name
            """
            results = self._repository.execute_write(
                query,
                name=drug_data.get("name", ""),
                generic_name=drug_data.get("generic_name"),
                purpose=drug_data.get("purpose"),
                indications=drug_data.get("indications"),
                warnings=drug_data.get("warnings"),
                dosage=drug_data.get("dosage"),
            )
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging drug: {e}")
            return False

    def search_drugs(self, query_text: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Drug)
            WHERE toLower(d.name) CONTAINS toLower($search)
               OR toLower(coalesce(d.generic_name, "")) CONTAINS toLower($search)
               OR toLower(coalesce(d.purpose, "")) CONTAINS toLower($search)
            RETURN {
                id: id(d),
                name: d.name,
                generic_name: d.generic_name,
                purpose: d.purpose
            } AS drug
            LIMIT $limit
            """
            results = self._repository.execute_read(
                query, search=query_text, limit=limit
            )
            return [record["drug"] for record in results]
        except Exception as e:
            logger.error(f"Error searching drugs: {e}")
            return []

    def get_drug_detail(self, drug_name: str) -> Optional[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Drug {name: $name})
            OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
            OPTIONAL MATCH (d)-[:MADE_BY]->(m:Manufacturer)
            OPTIONAL MATCH (d)-[r:INTERACTS_WITH]-(other:Drug)
            RETURN {
                id: id(d),
                name: d.name,
                generic_name: d.generic_name,
                purpose: d.purpose,
                indications: d.indications,
                warnings: d.warnings,
                dosage: d.dosage,
                ingredients: collect(distinct {id: id(i), name: i.name}),
                manufacturers: collect(distinct {id: id(m), name: m.name}),
                interactions: collect(distinct {
                    id: id(other),
                    name: other.name,
                    severity: r.severity,
                    description: r.description
                })
            } AS detail
            """
            results = self._repository.execute_read(query, name=drug_name)
            if not results:
                return None
            detail = results[0].get("detail")
            if not isinstance(detail, dict):
                return None
            detail["ingredients"] = [
                item for item in detail.get("ingredients", []) if item and item.get("name")
            ]
            detail["manufacturers"] = [
                item for item in detail.get("manufacturers", []) if item and item.get("name")
            ]
            detail["interactions"] = [
                item
                for item in detail.get("interactions", [])
                if item and item.get("name")
            ]
            return detail
        except Exception as e:
            logger.error(f"Error getting drug detail: {e}")
            return None

    # ============================================
    # DISEASE OPERATIONS
    # ============================================

    def search_diseases(self, query_text: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Disease)
            WHERE toLower(d.name) CONTAINS toLower($search)
               OR toLower(coalesce(d.description, "")) CONTAINS toLower($search)
            RETURN {
                id: id(d),
                name: d.name,
                description: d.description
            } AS disease
            LIMIT $limit
            """
            results = self._repository.execute_read(
                query, search=query_text, limit=limit
            )
            return [record["disease"] for record in results]
        except Exception as e:
            logger.error(f"Error searching diseases: {e}")
            return []

    def get_disease_symptoms(self, disease_name: str) -> Optional[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Disease {name: $name})
            OPTIONAL MATCH (d)-[:RELATED_TO]->(s:Symptom)
            RETURN {
                id: id(d),
                name: d.name,
                description: d.description,
                symptoms: collect(distinct {id: id(s), name: s.name})
            } AS disease
            """
            results = self._repository.execute_read(query, name=disease_name)
            if not results:
                return None
            disease = results[0].get("disease")
            if not isinstance(disease, dict):
                return None
            disease["symptoms"] = [
                item for item in disease.get("symptoms", []) if item and item.get("name")
            ]
            return disease
        except Exception as e:
            logger.error(f"Error getting disease symptoms: {e}")
            return None

    # ============================================
    # INTERACTION OPERATIONS
    # ============================================

    def check_drug_interactions(self, drug_names: list[str]) -> list[dict[str, Any]]:
        interactions: list[dict[str, Any]] = []
        try:
            for i in range(len(drug_names)):
                for j in range(i + 1, len(drug_names)):
                    query = """
                    MATCH (d1:Drug {name: $drug1})-[r:INTERACTS_WITH]-(d2:Drug {name: $drug2})
                    RETURN {
                        drug_1: d1.name,
                        drug_2: d2.name,
                        has_interaction: true,
                        severity: r.severity,
                        description: r.description
                    } AS interaction
                    """
                    results = self._repository.execute_read(
                        query, drug1=drug_names[i], drug2=drug_names[j]
                    )
                    if results and results[0].get("interaction"):
                        interactions.append(results[0]["interaction"])
        except Exception as e:
            logger.error(f"Error checking interactions: {e}")
        return interactions

    # ============================================
    # RELATIONSHIP OPERATIONS
    # ============================================

    def create_contains_relationship(
        self, drug_name: str, ingredient_name: str
    ) -> bool:
        try:
            query = """
            MATCH (d:Drug {name: $drug_name})
            MATCH (i:Ingredient {name: $ingredient_name})
            MERGE (d)-[:CONTAINS]->(i)
            """
            self._repository.execute_write(
                query,
                drug_name=drug_name,
                ingredient_name=ingredient_name,
            )
            logger.debug(
                f"Created CONTAINS relationship: {drug_name} -> {ingredient_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Error creating CONTAINS relationship: {e}")
            return False

    def create_made_by_relationship(
        self, drug_name: str, manufacturer_name: str
    ) -> bool:
        try:
            query = """
            MATCH (d:Drug {name: $drug_name})
            MATCH (m:Manufacturer {name: $manufacturer_name})
            MERGE (d)-[:MADE_BY]->(m)
            """
            self._repository.execute_write(
                query,
                drug_name=drug_name,
                manufacturer_name=manufacturer_name,
            )
            logger.debug(
                f"Created MADE_BY relationship: {drug_name} -> {manufacturer_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Error creating MADE_BY relationship: {e}")
            return False

    def create_interacts_relationship(
        self,
        drug_name_1: str,
        drug_name_2: str,
        severity: str = "moderate",
        description: str = "",
    ) -> bool:
        try:
            query = """
            MATCH (d1:Drug {name: $drug_name_1})
            MATCH (d2:Drug {name: $drug_name_2})
            MERGE (d1)-[r:INTERACTS_WITH]->(d2)
            SET r.severity = $severity,
                r.description = $description
            """
            self._repository.execute_write(
                query,
                drug_name_1=drug_name_1,
                drug_name_2=drug_name_2,
                severity=severity,
                description=description,
            )
            logger.debug(
                f"Created INTERACTS_WITH relationship: {drug_name_1} <-> {drug_name_2}"
            )
            return True
        except Exception as e:
            logger.error(f"Error creating INTERACTS_WITH relationship: {e}")
            return False


neo4j_service = Neo4jService()
