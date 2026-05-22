from typing import Any

from fastapi import APIRouter, Depends
from neo4j import Session

from app.core.neo4j import get_neo4j_session

router = APIRouter()


@router.get("/test")
def test_neo4j(_: Session = Depends(get_neo4j_session)) -> Any:
    """
    Test Neo4j connection
    """
    return {"message": "Hello Neo4j"}
