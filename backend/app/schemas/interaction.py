"""
Interaction API schemas.
"""

from pydantic import BaseModel, Field
from typing import List


class InteractionCheckRequest(BaseModel):
    """Request to check interactions between drugs."""

    drug_names: List[str] = Field(..., min_items=2, max_items=10)


class InteractionResult(BaseModel):
    """Interaction result between two drugs."""

    drug_1: str
    drug_2: str
    has_interaction: bool
    severity: str | None = None
    description: str | None = None


class InteractionCheckResponse(BaseModel):
    """Response for interaction check."""

    results: List[InteractionResult] = Field(default_factory=list)
