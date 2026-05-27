"""Neo4j Domain Models schemas for API responses."""

from typing import Optional
from pydantic import BaseModel


# ============ Drug Schema ============
class DrugBase(BaseModel):
    name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None


class DrugCreate(DrugBase):
    pass


class DrugRead(DrugBase):
    node_id: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ Disease Schema ============
class DiseaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    icd_code: Optional[str] = None


class DiseaseCreate(DiseaseBase):
    pass


class DiseaseRead(DiseaseBase):
    node_id: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ FavoriteDrug Schema ============
class FavoriteDrugBase(BaseModel):
    user_id: int
    drug_name: str


class FavoriteDrugCreate(FavoriteDrugBase):
    pass


class FavoriteDrugRead(FavoriteDrugBase):
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ Interaction/Relationship Schema ============
class DrugInteraction(BaseModel):
    """Represent a TREATS relationship between Drug and Disease."""
    drug_name: str
    disease_name: str
    confidence: Optional[float] = None
    evidence_count: Optional[int] = None
