"""
Disease lookup endpoints.
Handles disease searches and retrievals.
"""

from fastapi import APIRouter, HTTPException, Query, Path, status
import logging

from app.services.disease_lookup_service import disease_lookup_service
from app.schemas.disease import DiseaseSearchResponse, DiseaseDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get("/search", response_model=DiseaseSearchResponse)
def search_diseases(
    q: str = Query(..., min_length=1, max_length=255, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
):
    """
    Search for diseases by name or description.
    
    - **q**: Search query (required)
    - **limit**: Maximum number of results (default: 10, max: 100)
    """
    logger.info(f"GET /api/v1/diseases/search?q={q}&limit={limit}")
    try:
        return disease_lookup_service.search_diseases(query=q, limit=limit)
    except Exception as exc:
        logger.exception(f"Error searching diseases: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search diseases",
        )


@router.get("/{disease_name}/detail", response_model=DiseaseDetailResponse)
def get_disease_detail(
    disease_name: str = Path(..., description="Disease name"),
):
    """
    Get detailed information about a specific disease.
    
    Includes:
    - Basic disease information (name, description, ICD code)
    - Symptoms and characteristics
    """
    logger.info(f"GET /api/v1/diseases/{disease_name}/detail")
    try:
        disease = disease_lookup_service.get_disease_detail(disease_name)
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disease '{disease_name}' not found",
            )
        return disease
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error getting disease detail: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve disease details",
        )


@router.get("/{disease_name}/treatments")
def get_disease_treatments(
    disease_name: str = Path(..., description="Disease name"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
):
    """
    Get drugs that treat a specific disease.
    
    - **disease_name**: Name of the disease (required)
    - **limit**: Maximum number of drugs to return (default: 10, max: 100)
    """
    logger.info(f"GET /api/v1/diseases/{disease_name}/treatments?limit={limit}")
    try:
        drugs = disease_lookup_service.get_treating_drugs(disease_name, limit=limit)
        if not drugs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No treatments found for disease '{disease_name}'",
            )
        return {
            "disease_name": disease_name,
            "treatments": drugs,
            "total": len(drugs),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error getting disease treatments: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve disease treatments",
        )
