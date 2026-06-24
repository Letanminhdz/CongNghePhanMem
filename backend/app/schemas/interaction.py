"""
API Schemas cho tương tác thuốc.
"""

from pydantic import BaseModel, Field
from typing import List


class InteractionCheckRequest(BaseModel):
    """Yêu cầu kiểm tra các tương tác giữa các loại thuốc."""

    drug_names: List[str] = Field(..., min_items=2, max_items=10)


class InteractionResult(BaseModel):
    """Kết quả tương tác giữa hai loại thuốc."""

    drug_1: str
    drug_2: str
    has_interaction: bool
    severity: str | None = None
    description: str | None = None


class InteractionCheckResponse(BaseModel):
    """Phản hồi cho việc kiểm tra tương tác."""

    results: List[InteractionResult] = Field(default_factory=list)

class InteractionDetailResponse(BaseModel):
    """Chi tiết tương tác giữa hai loại thuốc cụ thể."""
    drug_1: str
    drug_2: str
    has_interaction: bool
    severity: str | None = None
    description: str | None = None
    message: str | None = None

class InteractionListResponse(BaseModel):
    """Danh sách tất cả các tương tác đối với một loại thuốc cụ thể."""
    drug_name: str
    interactions: List[InteractionResult] = Field(default_factory=list)
    total: int
    message: str | None = None

class InteractionSummaryResponse(BaseModel):
    """Tóm tắt kết quả phân tích tổ hợp thuốc."""
    drug_names: List[str]
    interactions: List[InteractionResult]
    is_safe: bool
    warnings: List[str] = Field(default_factory=list)
    summary: str
