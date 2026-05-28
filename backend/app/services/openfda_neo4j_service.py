"""
OpenFDA to Neo4j integration service.
DEPRECATED: Use app.services.neo4j_service instead.
This service is kept for backwards compatibility and delegates to neo4j_service.
"""

import logging
from typing import Any

from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)


class OpenFDANeo4jService:
    """Legacy service delegating to modern neo4j_service."""

    def merge_drug_to_neo4j(self, name: str, **kwargs: Any) -> bool:
        kwargs["name"] = name
        return neo4j_service.merge_drug(kwargs)

    def verify_drug_count(self) -> int:
        stats = neo4j_service.get_graph_stats()
        return stats.get("label_counts", {}).get("Drug", 0)

    def verify_disease_count(self) -> int:
        stats = neo4j_service.get_graph_stats()
        return stats.get("label_counts", {}).get("Disease", 0)

    def merge_disease_to_neo4j(self, name: str, description: str = "", **kwargs: Any) -> bool:
        # Simple merge using service repository implicitly
        return neo4j_service.merge_treats_relationship("DUMMY_DRUG", name)

    def merge_treats_relationship(self, drug_name: str, disease_name: str) -> bool:
        return neo4j_service.merge_treats_relationship(drug_name, disease_name)

    def merge_ingredient_to_neo4j(self, name: str, **kwargs: Any) -> bool:
        # Ingredients are merged automatically in relationships now
        return True

    def merge_contains_relationship(self, drug_name: str, ingredient_name: str) -> bool:
        return neo4j_service.merge_contains_relationship(drug_name, ingredient_name)

    def merge_manufacturer_to_neo4j(self, name: str, **kwargs: Any) -> bool:
        return True

    def merge_produces_relationship(self, manufacturer_name: str, drug_name: str) -> bool:
        return neo4j_service.merge_made_by_relationship(drug_name, manufacturer_name)

    def merge_interaction_relationship(self, drug_name_1: str, drug_name_2: str, **kwargs: Any) -> bool:
        return neo4j_service.create_interacts_relationship(drug_name_1, drug_name_2, **kwargs)

    def search_drugs(self, query: str, limit: int = 10) -> list[dict]:
        return neo4j_service.search_drugs(query, limit)

    def search_diseases(self, query: str, limit: int = 10) -> list[dict]:
        return neo4j_service.search_diseases(query, limit)

    def close(self) -> None:
        pass # Managed by repository now


openfda_neo4j_service = OpenFDANeo4jService()
