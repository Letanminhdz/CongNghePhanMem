"""
Favorite drugs service.
Handles user's favorite drug management.
"""

import logging
from typing import Any

from app.repositories.favorite_drug_repository import favorite_drug_repository
from app.repositories.drug_repository import drug_repository
from app.schemas.favorite import FavoriteDrugItem, FavoritesDrugListResponse

logger = logging.getLogger(__name__)


class FavoriteDrugService:
    """Service for managing favorite drugs."""

    def __init__(self):
        self._fav_repository = favorite_drug_repository
        self._drug_repository = drug_repository

    def add_to_favorites(
        self, user_id: int, drug_name: str, notes: str = ""
    ) -> dict[str, Any]:
        """
        Add a drug to user's favorites.
        Returns response indicating success or failure.
        """
        logger.info(f"Adding drug '{drug_name}' to favorites for user {user_id}")

        try:
            # Verify drug exists
            drug = self._drug_repository.get_drug_by_name(drug_name)
            if not drug:
                logger.warning(f"Drug '{drug_name}' not found")
                return {
                    "success": False,
                    "message": f"Drug '{drug_name}' not found",
                    "user_id": user_id,
                }

            # Check if already favorite
            if self._fav_repository.is_favorite(user_id, drug_name):
                logger.info(f"Drug '{drug_name}' already in favorites for user {user_id}")
                return {
                    "success": False,
                    "message": f"Drug '{drug_name}' is already in your favorites",
                    "user_id": user_id,
                }

            # Add to favorites
            success = self._fav_repository.add_to_favorites(
                user_id, drug_name, notes
            )
            if success:
                logger.info(f"Successfully added drug '{drug_name}' to favorites")
                return {
                    "success": True,
                    "message": f"Added '{drug_name}' to favorites",
                    "user_id": user_id,
                }
            else:
                logger.error(f"Failed to add drug '{drug_name}' to favorites")
                return {
                    "success": False,
                    "message": f"Failed to add '{drug_name}' to favorites",
                    "user_id": user_id,
                }

        except Exception as exc:
            logger.exception(f"Error adding drug to favorites: {exc}")
            return {
                "success": False,
                "message": "Failed to add drug to favorites",
                "user_id": user_id,
            }

    def remove_from_favorites(self, user_id: int, drug_name: str) -> dict[str, Any]:
        """
        Remove a drug from user's favorites.
        Returns response indicating success or failure.
        """
        logger.info(f"Removing drug '{drug_name}' from favorites for user {user_id}")

        try:
            success = self._fav_repository.remove_from_favorites(user_id, drug_name)
            if success:
                logger.info(f"Successfully removed drug '{drug_name}' from favorites")
                return {
                    "success": True,
                    "message": f"Removed '{drug_name}' from favorites",
                    "user_id": user_id,
                }
            else:
                logger.warning(
                    f"Drug '{drug_name}' not found in favorites for user {user_id}"
                )
                return {
                    "success": False,
                    "message": f"Drug '{drug_name}' not found in your favorites",
                    "user_id": user_id,
                }

        except Exception as exc:
            logger.exception(f"Error removing drug from favorites: {exc}")
            return {
                "success": False,
                "message": "Failed to remove drug from favorites",
                "user_id": user_id,
            }

    def get_favorites(
        self, user_id: int, limit: int = 50
    ) -> FavoritesDrugListResponse:
        """
        Get all favorite drugs for a user.
        """
        logger.info(f"Fetching favorites for user {user_id}")

        try:
            results = self._fav_repository.get_user_favorites(user_id, limit=limit)

            items = [
                FavoriteDrugItem(
                    drug_name=drug.get("name", ""),
                    brand_name=drug.get("brand_name"),
                    generic_name=drug.get("generic_name"),
                    purpose=drug.get("purpose"),
                    added_at=drug.get("added_at"),
                )
                for drug in results
            ]

            logger.info(f"Found {len(items)} favorite drugs for user {user_id}")
            return FavoritesDrugListResponse(user_id=user_id, total=len(items), drugs=items)

        except Exception as exc:
            logger.exception(f"Error fetching favorites for user {user_id}: {exc}")
            return FavoritesDrugListResponse(user_id=user_id, total=0, drugs=[])

    def is_favorite(self, user_id: int, drug_name: str) -> bool:
        """
        Check if a drug is in user's favorites.
        """
        try:
            return self._fav_repository.is_favorite(user_id, drug_name)
        except Exception as exc:
            logger.exception(f"Error checking favorite status: {exc}")
            return False


favorite_drug_service = FavoriteDrugService()
