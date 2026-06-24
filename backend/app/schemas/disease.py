"""
API Schemas cho bệnh lý.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class DiseaseSearchRequest(BaseModel):
    """Yêu cầu tìm kiếm bệnh lý."""

    query: str = Field(..., min_length=1, max_length=255)
    limit: int = Field(10, ge=1, le=100)


class DiseaseSymptom(BaseModel):
    """Mô hình triệu chứng bệnh lý."""

    name: str
    description: Optional[str] = None


class DiseaseResponse(BaseModel):
    """Phản hồi cơ bản của bệnh lý."""

    id: Optional[str] = None
    name: str
    category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None


class DiseaseDetailResponse(DiseaseResponse):
    """Phản hồi chi tiết của bệnh lý kèm theo các triệu chứng."""

    category: Optional[str] = None
    severity: Optional[str] = None
    symptoms: List[DiseaseSymptom] = Field(default_factory=list)
    treatments: List[str] = Field(default_factory=list, description="Medicine names")


class DiseaseSearchResponse(BaseModel):
    """Phản hồi tìm kiếm bệnh lý."""

    total: int
    limit: int
    items: List[DiseaseResponse]

class DiseaseTreatmentResponse(BaseModel):
    """Phản hồi về các thuốc điều trị một bệnh cụ thể."""
    disease_name: str
    treatments: List[dict] = Field(default_factory=list, description="Medicine list with basic details")
    total: int

class DiseaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    treatments: List[str] = Field(default_factory=list, description="List of medicine names that treat this disease")

class DiseaseUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    treatments: Optional[List[str]] = None
