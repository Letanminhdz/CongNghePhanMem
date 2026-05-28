from fastapi import APIRouter, HTTPException
from typing import Any

from app.services.neo4j_service import neo4j_service

from app.repositories.neo4j_repository import neo4j_repository

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/drugs")
def get_all_drugs_debug() -> Any:
    """
    Directly query Neo4j to see what drugs are visible.
    """
    query = "MATCH (d:Drug) RETURN d.name AS name LIMIT 10"
    results = neo4j_repository.execute_read(query)
    return results

@router.get("/drug/{name}")
def get_drug_debug(name: str) -> Any:
    """
    Debug endpoint to directly test Neo4j drug retrieval.
    """
    logger.info(f"DEBUG REQ: Drug name = '{name}'")
    detail = neo4j_service.get_drug_detail(name)
    logger.info(f"DEBUG RES: Detail = {detail}")
    
    # Return raw detail even if None to see what's happening
    return {
        "requested_name": name,
        "detail": detail,
        "type": str(type(detail))
    }

@router.get("/disease/{name}")
def get_disease_debug(name: str) -> Any:
    """
    Debug endpoint to directly test Neo4j disease retrieval.
    """
    logger.info(f"DEBUG REQ: Disease name = '{name}'")
    detail = neo4j_service.get_disease_symptoms(name)
    logger.info(f"DEBUG RES: Detail = {detail}")
    
    return {
        "requested_name": name,
        "detail": detail,
        "type": str(type(detail))
    }
