from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Annotated

from app.api.v1.endpoints.deps import get_current_user
from app.models.user import User
from app.services.import_openfda_service import import_openfda_drugs
from app.services.neo4j_service import neo4j_service

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/import/openfda")
def admin_import_openfda(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(10, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """
    Admin only: Import drugs from openFDA.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    
    imported = import_openfda_drugs(limit=limit, skip=skip)
    return {
        "success": True,
        "imported": imported,
        "stats": neo4j_service.get_graph_stats()
    }

@router.post("/rebuild-graph")
def admin_rebuild_graph(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Admin only: Rebuild Neo4j constraints and indexes.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    
    success = neo4j_service.rebuild_graph()
    return {"success": success}

@router.post("/graph/reset")
def admin_reset_graph(
    current_user: Annotated[User, Depends(get_current_user)],
    confirm: bool = Query(False, description="Must be true to actually delete data"),
    test_only: bool = Query(True, description="If true, only clean test/dummy data")
):
    """
    Admin only: Reset or cleanup the Neo4j graph.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    
    if test_only:
        return neo4j_service.cleanup_test_data()
    
    return neo4j_service.reset_graph(confirm=confirm)

@router.get("/graph/stats")
def admin_graph_stats(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Admin only: Get Neo4j graph statistics.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    
    return neo4j_service.get_graph_stats()
