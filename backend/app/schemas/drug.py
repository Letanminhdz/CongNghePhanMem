"""
Drug API schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


class DrugSearchRequest(BaseModel):
    """Drug search request."""

    query: str = Field(..., min_length=1, max_length=255)
    limit: int = Field(10, ge=1, le=100)


class DrugIngredient(BaseModel):
    """Ingredient in drug."""

    name: str
    description: Optional[str] = None


class DrugManufacturer(BaseModel):
    """Manufacturer info."""

    name: str
    country: Optional[str] = None


class DrugInteraction(BaseModel):
    """Drug interaction."""

    name: str
    severity: str


class DrugResponse(BaseModel):
    """Drug response model."""

    id: Optional[str] = None
    name: str
    generic_name: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None
    warnings: Optional[str] = None
    dosage: Optional[str] = None


class DrugDetailResponse(DrugResponse):
    """Drug detail with relationships."""

    ingredients: list[DrugIngredient] = Field(default_factory=list)
    manufacturers: list[DrugManufacturer] = Field(default_factory=list)
    interactions: list[DrugInteraction] = Field(default_factory=list)


class DrugSearchResponse(BaseModel):
    """Drug search response."""

    total: int
    limit: int
    items: list[DrugResponse]


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    status_code: int
