"""
Favorite drugs repository for Neo4j operations.
Handles user favorite drug relationships.
"""

import logging
from typing import Any

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class FavoriteDrugRepository:
    """Repository for favorite drug operations in Neo4j."""

    def __init__(self):
        self._repository = neo4j_repository

    def add_to_favorites(
        self, user_id: int, drug_name: str, notes: str = ""
    ) -> bool:
        """
        Add a drug to user's favorites.
        Returns True if successful, False otherwise.
        """
        query = """
        MATCH (d:Drug {name: $drug_name})
        MERGE (u:User {id: $user_id})
        MERGE (u)-[r:FAVORITE]->(d)
        SET 
            r.notes = $notes,
            r.created_at = datetime()
        RETURN r
        """
        try:
            results = self._repository.execute_write(
                query,
                user_id=user_id,
                drug_name=drug_name,
                notes=notes or "",
            )
            if results:
                logger.info(
                    f"Added drug '{drug_name}' to favorites for user {user_id}"
                )
                return True
            return False
        except Exception as exc:
            logger.error(
                f"Failed to add drug '{drug_name}' to favorites for user {user_id}: {exc}"
            )
            return False

    def remove_from_favorites(self, user_id: int, drug_name: str) -> bool:
        """
        Remove a drug from user's favorites.
        Returns True if successful, False otherwise.
        """
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (u)-[r:FAVORITE]->(d:Drug {name: $drug_name})
        DELETE r
        RETURN COUNT(r) AS deleted
        """
        try:
            results = self._repository.execute_write(
                query,
                user_id=user_id,
                drug_name=drug_name,
            )
            if results and results[0].get("deleted", 0) > 0:
                logger.info(
                    f"Removed drug '{drug_name}' from favorites for user {user_id}"
                )
                return True
            return False
        except Exception as exc:
            logger.error(
                f"Failed to remove drug '{drug_name}' from favorites for user {user_id}: {exc}"
            )
            return False

    def get_user_favorites(
        self, user_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get all favorite drugs for a user.
        """
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (u)-[r:FAVORITE]->(d:Drug)
        RETURN 
            d.name AS name,
            d.brand_name AS brand_name,
            d.generic_name AS generic_name,
            d.purpose AS purpose,
            r.notes AS notes,
            r.created_at AS added_at
        LIMIT $limit
        """
        try:
            results = self._repository.execute_read(
                query,
                user_id=user_id,
                limit=limit,
            )
            return results if results else []
        except Exception as exc:
            logger.error(f"Failed to get favorites for user {user_id}: {exc}")
            return []

    def is_favorite(self, user_id: int, drug_name: str) -> bool:
        """
        Check if a drug is in user's favorites.
        """
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (u)-[:FAVORITE]->(d:Drug {name: $drug_name})
        RETURN COUNT(*) AS count
        """
        try:
            results = self._repository.execute_read(
                query,
                user_id=user_id,
                drug_name=drug_name,
            )
            if results:
                return results[0].get("count", 0) > 0
            return False
        except Exception as exc:
            logger.error(
                f"Failed to check if '{drug_name}' is favorite for user {user_id}: {exc}"
            )
            return False

    def get_favorite_count(self, user_id: int) -> int:
        """
        Get count of user's favorite drugs.
        """
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (u)-[:FAVORITE]->(d:Drug)
        RETURN COUNT(d) AS count
        """
        try:
            results = self._repository.execute_read(query, user_id=user_id)
            if results:
                return results[0].get("count", 0)
            return 0
        except Exception as exc:
            logger.error(f"Failed to count favorites for user {user_id}: {exc}")
            return 0


favorite_drug_repository = FavoriteDrugRepository()
