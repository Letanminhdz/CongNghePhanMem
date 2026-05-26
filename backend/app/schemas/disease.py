"""
Disease API schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class DiseaseSearchRequest(BaseModel):
    """Disease search request."""

    query: str = Field(..., min_length=1, max_length=255)
    limit: int = Field(10, ge=1, le=100)


class DiseaseSymptom(BaseModel):
    """Disease symptom model."""

    name: str
    description: Optional[str] = None


class DiseaseResponse(BaseModel):
    """Disease basic response."""

    id: Optional[str] = None
    name: str
    description: Optional[str] = None


class DiseaseDetailResponse(DiseaseResponse):
    """Disease detail response with symptoms."""

    symptoms: List[DiseaseSymptom] = Field(default_factory=list)


class DiseaseSearchResponse(BaseModel):
    """Disease search response."""

    total: int
    limit: int
    items: List[DiseaseResponse]
