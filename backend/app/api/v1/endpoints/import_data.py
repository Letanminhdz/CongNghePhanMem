from fastapi import APIRouter, HTTPException, Query
import logging

from app.services.import_openfda_service import import_openfda_drugs
from app.services.openfda_neo4j_service import openfda_neo4j_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["import"])


@router.post("/openfda")
def import_openfda(
    limit: int = Query(10, ge=1, le=1000, description="Number of drugs to import"),
    skip: int = Query(0, ge=0, description="Number of drugs to skip")
):
    """
    Import drugs from openFDA API into Neo4j.
    
    Features:
    - Imports drug nodes with name, brand name, generic name, dosage, warnings, etc.
    - Creates Ingredient nodes and CONTAINS relationships
    - Creates Manufacturer nodes and PRODUCES relationships
    - Extracts diseases from indications and creates TREATS relationships
    - Handles retry on transient API failures
    - Rate limiting and proper pagination
    
    Parameters:
    - **limit**: Number of drugs to import (max 1000)
    - **skip**: Number of drugs to skip for pagination
    
    Returns:
    - imported: Number of drugs imported in this request
    - total_drugs: Total drug nodes in Neo4j
    - total_diseases: Total disease nodes created
    """
    logger.info(f"Starting openFDA import: limit={limit}, skip={skip}")
    try:
        imported = import_openfda_drugs(limit=limit, skip=skip)
        total_drugs = openfda_neo4j_service.verify_drug_count()
        total_diseases = openfda_neo4j_service.verify_disease_count()
        
        logger.info(f"✓ Import completed: imported={imported}, total_drugs={total_drugs}")
        return {
            "success": True,
            "imported": imported,
            "total_drugs_in_neo4j": total_drugs,
            "total_diseases_in_neo4j": total_diseases,
            "source": "openFDA drug label API",
            "pagination": {
                "skip": skip,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.exception(f"✗ Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/openfda-drugs")
def import_openfda_v2(limit: int = 10, skip: int = 0):
    """
    Legacy endpoint - Import drugs from openFDA API into Neo4j.
    Use /api/v1/import/openfda instead.
    
    This endpoint is kept for backwards compatibility.
    """
    logger.info(f"Starting openFDA import (legacy): limit={limit}, skip={skip}")
    try:
        imported = import_openfda_drugs(limit=limit, skip=skip)
        total_drugs = openfda_neo4j_service.verify_drug_count()
        logger.info(f"✓ Import completed: imported={imported}, total_drugs={total_drugs}")
        return {
            "imported": imported,
            "total_drugs_in_neo4j": total_drugs,
            "source": "openFDA drug label",
        }
    except Exception as e:
        logger.exception(f"✗ Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
