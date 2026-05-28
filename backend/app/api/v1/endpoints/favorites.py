"""
Favorite drugs endpoints.
Handles user's favorite drug management.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from typing import Annotated
import logging

from app.api.v1.endpoints.deps import get_current_user
from app.models.user import User
from app.services.favorite_drug_service import favorite_drug_service
from app.schemas.favorite import (
    FavoriteDrugItem,
    FavoritesDrugListResponse,
    AddFavoriteRequest,
    RemoveFavoriteRequest,
    FavoriteActionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/add", response_model=FavoriteActionResponse)
def add_to_favorites(
    request: AddFavoriteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Add a drug to current user's favorites.
    
    Request body:
    ```json
    {
        "drug_name": "Drug Name",
        "notes": "Optional notes about this drug"
    }
    ```
    """
    logger.info(
        f"POST /api/v1/favorites/add - user_id={current_user.id}, drug='{request.drug_name}'"
    )
    try:
        result = favorite_drug_service.add_to_favorites(
            current_user.id, request.drug_name, request.notes or ""
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return FavoriteActionResponse(
            success=True,
            message=result["message"],
            user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error adding favorite: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite",
        )


@router.post("/remove", response_model=FavoriteActionResponse)
def remove_from_favorites(
    request: RemoveFavoriteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Remove a drug from current user's favorites.
    
    Request body:
    ```json
    {
        "drug_name": "Drug Name"
    }
    ```
    """
    logger.info(
        f"POST /api/v1/favorites/remove - user_id={current_user.id}, drug='{request.drug_name}'"
    )
    try:
        result = favorite_drug_service.remove_from_favorites(
            current_user.id, request.drug_name
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"],
            )
        return FavoriteActionResponse(
            success=True,
            message=result["message"],
            user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error removing favorite: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite",
        )


@router.get("/list", response_model=FavoritesDrugListResponse)
def get_favorites(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get all favorite drugs for current user.
    """
    logger.info(f"GET /api/v1/favorites/list - user_id={current_user.id}")
    try:
        return favorite_drug_service.get_favorites(current_user.id)
    except Exception as exc:
        logger.exception(f"Error fetching favorites: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch favorites",
        )


@router.get("/{drug_name}/is-favorite")
def is_favorite(
    drug_name: str = Path(..., description="Drug name"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    Check if a drug is in current user's favorites.
    """
    logger.info(f"GET /api/v1/favorites/{drug_name}/is-favorite - user_id={current_user.id}")
    try:
        is_fav = favorite_drug_service.is_favorite(current_user.id, drug_name)
        return {
            "drug_name": drug_name,
            "is_favorite": is_fav,
            "user_id": current_user.id,
        }
    except Exception as exc:
        logger.exception(f"Error checking favorite status: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check favorite status",
        )
