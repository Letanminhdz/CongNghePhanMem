"""
Các endpoint tương tác thuốc.
Xử lý việc kiểm tra tương tác giữa các loại thuốc.
"""

from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from app.api.v1.endpoints.deps import get_db, get_optional_current_user, get_current_user
from app.repositories import interaction_history_repository
from app.models.user import User
import logging

from app.services.drug_interaction_service import drug_interaction_service
from app.schemas.interaction import (
    InteractionCheckRequest, 
    InteractionCheckResponse, 
    InteractionDetailResponse, 
    InteractionListResponse,
    InteractionSummaryResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interactions", tags=["interactions"])

@router.get("/history/count")
def get_interaction_history_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Lấy tổng số lượt kiểm tra tương tác thuốc mà người dùng đã thực hiện.
    """
    count = interaction_history_repository.get_user_interaction_count(db, current_user.id)
    return {"total": count}

@router.get("/{drug_name}", response_model=InteractionListResponse)
def get_drug_interactions(
    drug_name: str = Path(..., description="Medicine name"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    Lấy tất cả các tương tác đã biết của một loại thuốc cụ thể.
    
    - **drug_name**: Tên thuốc cần kiểm tra (bắt buộc)
    
    Trả về danh sách các loại thuốc tương tác với thuốc được chỉ định.
    """
    logger.info(f"GET /api/v1/interactions/{drug_name}?limit={limit}&skip={skip}")
    try:
        interactions = drug_interaction_service.get_drug_interactions(drug_name, limit=limit, skip=skip)
        if not interactions:
            return InteractionListResponse(
                drug_name=drug_name,
                interactions=[],
                total=0,
                message=f"No interactions found for '{drug_name}'",
            )
        return InteractionListResponse(
            drug_name=drug_name,
            interactions=interactions,
            total=len(interactions),
        )
    except Exception as exc:
        logger.exception(f"Error getting drug interactions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drug interactions",
        )


@router.post("/check", response_model=InteractionCheckResponse)
def check_multiple_interactions(
    request: InteractionCheckRequest,
):
    """
    Kiểm tra tương tác giữa nhiều loại thuốc.
    
    Trả về tất cả các cặp tương tác thuốc được tìm thấy kèm theo mức độ nghiêm trọng.
    """
    logger.info(f"POST /api/v1/interactions/check with medicines: {request.drug_names}")
    try:
        return drug_interaction_service.check_multiple_interactions(request.drug_names)
    except Exception as exc:
        logger.exception(f"Error checking multiple interactions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check drug interactions",
        )


@router.get("/{drug_1}/with/{drug_2}", response_model=InteractionDetailResponse)
def assess_interaction(
    drug_1: str = Path(..., description="First medicine name"),
    drug_2: str = Path(..., description="Second medicine name"),
):
    """
    Đánh giá mức độ tương tác giữa hai loại thuốc cụ thể.
    
    Trả về thông tin chi tiết về tương tác nếu có.
    """
    logger.info(f"GET /api/v1/interactions/{drug_1}/with/{drug_2}")
    try:
        interaction = drug_interaction_service.assess_interaction_severity(
            drug_1, drug_2
        )
        if not interaction:
            return InteractionDetailResponse(
                drug_1=drug_1,
                drug_2=drug_2,
                has_interaction=False,
                message=f"No known interaction between '{drug_1}' and '{drug_2}'",
            )
        return InteractionDetailResponse(
            drug_1=drug_1,
            drug_2=drug_2,
            has_interaction=True,
            severity=interaction.get("severity"),
            description=interaction.get("description"),
        )
    except Exception as exc:
        logger.exception(f"Error assessing interaction: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess drug interaction",
        )


@router.post("/analyze-combination", response_model=InteractionSummaryResponse)
def analyze_drug_combination(
    request: InteractionCheckRequest,
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Phân tích một tổ hợp các thuốc để xác định các tổ hợp an toàn và không an toàn.
    """
    logger.info(f"POST /api/v1/interactions/analyze-combination with medicines: {request.drug_names}")
    try:
        if current_user:
            interaction_history_repository.log_interaction_check(db, current_user.id, request.drug_names)
            
        result = drug_interaction_service.get_safe_drug_combinations(request.drug_names)
        return InteractionSummaryResponse(**result)
    except Exception as exc:
        logger.exception(f"Error analyzing drug combination: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze drug combination",
        )
