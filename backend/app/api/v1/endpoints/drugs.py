"""
Drug lookup endpoints.
Handles drug searches and retrievals.
"""

from fastapi import APIRouter, HTTPException, Query, Path, status
import logging

from app.services.drug_lookup_service import drug_lookup_service
from app.schemas.drug import DrugSearchRequest, DrugSearchResponse, DrugDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drugs", tags=["drugs"])


@router.get("/search", response_model=DrugSearchResponse)
def search_drugs(
    q: str = Query(..., min_length=1, max_length=255, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
):
    """
    Search for drugs by name, brand name, or generic name.
    
    - **q**: Search query (required)
    - **limit**: Maximum number of results (default: 10, max: 100)
    """
    logger.info(f"GET /api/v1/drugs/search?q={q}&limit={limit}")
    try:
        return drug_lookup_service.search_drugs(query=q, limit=limit)
    except Exception as exc:
        logger.exception(f"Error searching drugs: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search drugs",
        )


@router.get("/{drug_name}/detail", response_model=DrugDetailResponse)
def get_drug_detail(
    drug_name: str = Path(..., description="Drug name"),
):
    """
    Get detailed information about a specific drug.
    
    Includes:
    - Basic drug information (brand name, generic name, dosage, warnings, etc.)
    - Ingredients
    - Manufacturers
    - Known drug interactions
    """
    logger.info(f"GET /api/v1/drugs/{drug_name}/detail")
    try:
        drug = drug_lookup_service.get_drug_detail(drug_name)
        if not drug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drug '{drug_name}' not found",
            )
        return drug
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error getting drug detail: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drug details",
        )


@router.get("/{drug_name}/ingredients")
def get_drug_ingredients(
    drug_name: str = Path(..., description="Drug name"),
):
    """
    Get all ingredients in a specific drug.
    """
    logger.info(f"GET /api/v1/drugs/{drug_name}/ingredients")
    try:
        ingredients = drug_lookup_service.get_drug_ingredients(drug_name)
        if not ingredients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ingredients found for drug '{drug_name}'",
            )
        return {"drug_name": drug_name, "ingredients": ingredients}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error getting drug ingredients: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drug ingredients",
        )


@router.get("/for-disease/{disease_name}", response_model=DrugSearchResponse)
def get_drugs_for_disease(
    disease_name: str = Path(..., description="Disease name"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
):
    """
    Get drugs that treat a specific disease.
    """
    logger.info(f"GET /api/v1/drugs/for-disease/{disease_name}?limit={limit}")
    try:
        return drug_lookup_service.get_drugs_by_disease(disease_name, limit=limit)
    except Exception as exc:
        logger.exception(f"Error getting drugs for disease: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drugs for disease",
        )
