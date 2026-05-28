"""
Favorite drugs API schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FavoriteDrugItem(BaseModel):
    """Favorite drug item."""

    drug_name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    purpose: Optional[str] = None
    added_at: Optional[datetime] = None


class AddFavoriteRequest(BaseModel):
    """Request to add a drug to favorites."""

    drug_name: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = Field(None, max_length=500)


class FavoritesDrugListResponse(BaseModel):
    """Response with list of favorite drugs."""

    user_id: int
    total: int
    drugs: List[FavoriteDrugItem] = Field(default_factory=list)


class RemoveFavoriteRequest(BaseModel):
    """Request to remove a drug from favorites."""

    drug_name: str = Field(..., min_length=1, max_length=255)


class FavoriteActionResponse(BaseModel):
    """Response for favorite action."""

    success: bool
    message: str
    user_id: int
