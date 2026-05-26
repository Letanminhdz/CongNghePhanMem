"""
Neo4j ORM Models for Medical Chatbot.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================
# DRUG
# ============================================


class DrugBase(BaseModel):
    """Base drug model."""

    name: str = Field(..., min_length=1, max_length=255)
    generic_name: Optional[str] = Field(None, max_length=255)
    purpose: Optional[str] = Field(None)
    indications: Optional[str] = Field(None)
    warnings: Optional[str] = Field(None)
    dosage: Optional[str] = Field(None)


class DrugCreate(DrugBase):
    """Drug creation model."""

    pass


class DrugUpdate(BaseModel):
    """Drug update model."""

    generic_name: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None
    warnings: Optional[str] = None
    dosage: Optional[str] = None


class DrugRead(DrugBase):
    """Drug read model with computed fields."""

    id: Optional[str] = None
    ingredients: list[dict] = Field(default_factory=list)
    manufacturers: list[dict] = Field(default_factory=list)
    interactions: list[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============================================
# INGREDIENT
# ============================================


class IngredientBase(BaseModel):
    """Base ingredient model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class IngredientCreate(IngredientBase):
    """Ingredient creation model."""

    pass


class IngredientRead(IngredientBase):
    """Ingredient read model."""

    id: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# DISEASE
# ============================================


class DiseaseBase(BaseModel):
    """Base disease model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DiseaseCreate(DiseaseBase):
    """Disease creation model."""

    pass


class DiseaseRead(DiseaseBase):
    """Disease read model."""

    id: Optional[str] = None
    symptoms: list[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============================================
# SYMPTOM
# ============================================


class SymptomBase(BaseModel):
    """Base symptom model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SymptomCreate(SymptomBase):
    """Symptom creation model."""

    pass


class SymptomRead(SymptomBase):
    """Symptom read model."""

    id: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# MANUFACTURER
# ============================================


class ManufacturerBase(BaseModel):
    """Base manufacturer model."""

    name: str = Field(..., min_length=1, max_length=255)
    country: Optional[str] = Field(None, max_length=100)


class ManufacturerCreate(ManufacturerBase):
    """Manufacturer creation model."""

    pass


class ManufacturerRead(ManufacturerBase):
    """Manufacturer read model."""

    id: Optional[str] = None
    drugs: list[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============================================
# INTERACTION
# ============================================


class InteractionBase(BaseModel):
    """Base interaction model."""

    severity: str = Field(
        ..., pattern="^(mild|moderate|severe|contraindicated)$"
    )
    description: Optional[str] = None


class InteractionCreate(InteractionBase):
    """Interaction creation model."""

    pass


class InteractionRead(InteractionBase):
    """Interaction read model."""

    id: Optional[str] = None
    drug_1_name: Optional[str] = None
    drug_2_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# SEARCH RESULT
# ============================================


class SearchResultItem(BaseModel):
    """Generic search result item."""

    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str  # "drug", "disease", "ingredient"


class SearchResults(BaseModel):
    """Search results wrapper."""

    total: int = 0
    items: list[SearchResultItem] = Field(default_factory=list)


# ============================================
# INTERACTION CHECK
# ============================================


class InteractionCheckRequest(BaseModel):
    """Request to check interactions between drugs."""

    drug_names: list[str] = Field(..., min_items=2, max_items=10)


class InteractionCheckResult(BaseModel):
    """Result of interaction check."""

    drug_1: str
    drug_2: str
    has_interaction: bool
    severity: Optional[str] = None  # mild, moderate, severe, contraindicated
    description: Optional[str] = None
