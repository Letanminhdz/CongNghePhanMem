"""
Drug interaction endpoints.
Handles drug interaction checks.
"""

from fastapi import APIRouter, HTTPException, Query, Path, status
import logging

from app.services.drug_interaction_service import drug_interaction_service
from app.schemas.interaction import InteractionCheckRequest, InteractionCheckResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/{drug_name}")
def get_drug_interactions(
    drug_name: str = Path(..., description="Drug name"),
):
    """
    Get all known interactions for a specific drug.
    
    - **drug_name**: Name of the drug to check (required)
    
    Returns list of drugs that interact with the specified drug,
    including severity level and description of the interaction.
    """
    logger.info(f"GET /api/v1/interactions/{drug_name}")
    try:
        interactions = drug_interaction_service.get_drug_interactions(drug_name)
        if not interactions:
            return {
                "drug_name": drug_name,
                "interactions": [],
                "total": 0,
                "message": f"No interactions found for '{drug_name}'",
            }
        return {
            "drug_name": drug_name,
            "interactions": interactions,
            "total": len(interactions),
        }
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
    Check interactions between multiple drugs.
    
    Request body should contain:
    ```json
    {
        "drug_names": ["Drug1", "Drug2", "Drug3"]
    }
    ```
    
    Returns all interaction pairs found with severity levels.
    
    - Severity levels: "severe", "moderate", "mild"
    - Minimum 2 drugs required, maximum 10
    """
    logger.info(f"POST /api/v1/interactions/check with drugs: {request.drug_names}")
    try:
        return drug_interaction_service.check_multiple_interactions(request.drug_names)
    except Exception as exc:
        logger.exception(f"Error checking multiple interactions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check drug interactions",
        )


@router.get("/{drug_1}/with/{drug_2}")
def assess_interaction(
    drug_1: str = Path(..., description="First drug name"),
    drug_2: str = Path(..., description="Second drug name"),
):
    """
    Assess the interaction between two specific drugs.
    
    - **drug_1**: Name of first drug (required)
    - **drug_2**: Name of second drug (required)
    
    Returns detailed interaction information if it exists,
    or null if no interaction is known.
    """
    logger.info(f"GET /api/v1/interactions/{drug_1}/with/{drug_2}")
    try:
        interaction = drug_interaction_service.assess_interaction_severity(
            drug_1, drug_2
        )
        if not interaction:
            return {
                "drug_1": drug_1,
                "drug_2": drug_2,
                "has_interaction": False,
                "message": f"No known interaction between '{drug_1}' and '{drug_2}'",
            }
        return {
            "drug_1": drug_1,
            "drug_2": drug_2,
            "has_interaction": True,
            "severity": interaction.get("severity"),
            "description": interaction.get("description"),
        }
    except Exception as exc:
        logger.exception(f"Error assessing interaction: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess drug interaction",
        )


@router.post("/analyze-combination")
def analyze_drug_combination(
    request: InteractionCheckRequest,
):
    """
    Analyze a combination of drugs to identify safe and unsafe combinations.
    
    Request body should contain:
    ```json
    {
        "drug_names": ["Drug1", "Drug2", "Drug3"]
    }
    ```
    
    Returns:
    - Summary of all interactions by severity
    - Overall safety assessment (is_safe: boolean)
    - Warnings for severe and moderate interactions
    
    - Minimum 2 drugs required, maximum 10
    """
    logger.info(f"POST /api/v1/interactions/analyze-combination with drugs: {request.drug_names}")
    try:
        return drug_interaction_service.get_safe_drug_combinations(request.drug_names)
    except Exception as exc:
        logger.exception(f"Error analyzing drug combination: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze drug combination",
        )
