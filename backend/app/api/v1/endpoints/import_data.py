from fastapi import APIRouter, HTTPException
import logging

from app.services.import_openfda_service import import_openfda_drugs
from app.services.openfda_neo4j_service import openfda_neo4j_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["import"])


@router.post("/openfda-drugs")
def import_openfda(limit: int = 10, skip: int = 0):
    logger.info(f"Starting openFDA import: limit={limit}, skip={skip}")
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
