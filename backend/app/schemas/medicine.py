from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MedicineBase(BaseModel):
    name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None
    warnings: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    adverse_reactions: Optional[str] = None
    side_effects: Optional[str] = None

class MedicineCreate(MedicineBase):
    pass

class MedicineUpdate(BaseModel):
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None
    warnings: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    adverse_reactions: Optional[str] = None
    side_effects: Optional[str] = None

class MedicineSummary(BaseModel):
    name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    manufacturer: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None

class MedicineDetailResponse(MedicineBase):
    updated_at: Optional[datetime] = None
    ingredients: List[str] = []
    manufacturers: List[str] = []
    treated_diseases: List[str] = []
    interactions: List[dict] = []

class MedicineSearchResponse(BaseModel):
    query: str
    total: int
    limit: int
    skip: int
    items: List[MedicineSummary]
