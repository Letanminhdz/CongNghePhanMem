from fastapi import APIRouter, HTTPException, Query
import logging

from app.schemas.drug import DrugDetailResponse, DrugSearchResponse
from app.schemas.disease import DiseaseDetailResponse, DiseaseSearchResponse
from app.schemas.interaction import (
    InteractionCheckRequest,
    InteractionCheckResponse,
    InteractionResult,
)
from app.schemas.domain_model import DiseaseCreate, DrugInteraction
from app.schemas.graph import GraphResponse
from app.services.neo4j_service import neo4j_service
from app.services.openfda_neo4j_service import openfda_neo4j_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/neo4j", tags=["neo4j"])


@router.get("/test")
def test_neo4j_connection():
    try:
        result = neo4j_service.verify_connectivity()
        if not result:
            raise Exception("connectivity check failed")

        # Ensure a simple Test node exists and return it
        try:
            repo = neo4j_service._repository
            # ensure driver exists
            repo._ensure_driver()
            # use a session directly to perform write/read
            with repo._driver.session() as session:
                session.run("MERGE (t:Test {name: $name})", name="hello")
                result = session.run(
                    "MATCH (t:Test {name: $name}) RETURN t.name AS name", name="hello"
                )
                rows = [r.data() for r in result]
                node = rows[0] if rows else None
        except Exception:
            node = None

        return {"status": "connected", "result": result, "node": node}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection failed: {str(e)}")


@router.get("/drugs/search", response_model=DrugSearchResponse)
def search_drugs(
    query: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(10, ge=1, le=100),
):
    drugs = neo4j_service.search_drugs(query, limit)
    return {"total": len(drugs), "limit": limit, "items": drugs}


@router.get("/drugs/{drug_name}", response_model=DrugDetailResponse)
def get_drug_detail(drug_name: str):
    detail = neo4j_service.get_drug_detail(drug_name)
    if not detail:
        raise HTTPException(status_code=404, detail="Drug not found")
    return detail


@router.get("/diseases/search", response_model=DiseaseSearchResponse)
def search_diseases(
    query: str = Query(..., min_length=1, max_length=255),
    limit: int = Query(10, ge=1, le=100),
):
    diseases = neo4j_service.search_diseases(query, limit)
    return {"total": len(diseases), "limit": limit, "items": diseases}


@router.get("/diseases/{disease_name}", response_model=DiseaseDetailResponse)
def get_disease_symptoms(disease_name: str):
    disease = neo4j_service.get_disease_symptoms(disease_name)
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    return disease


@router.post("/interactions/check", response_model=InteractionCheckResponse)
def check_interactions(request: InteractionCheckRequest):
    results = neo4j_service.check_drug_interactions(request.drug_names)
    interactions = [
        InteractionResult(
            drug_1=item["drug_1"],
            drug_2=item["drug_2"],
            has_interaction=True,
            severity=item.get("severity"),
            description=item.get("description"),
        )
        for item in results
    ]
    return InteractionCheckResponse(results=interactions)


@router.post("/diseases/create")
def create_disease(disease: DiseaseCreate):
    """Create a new disease node in Neo4j."""
    logger.info(f"Creating disease: {disease.name}")
    result = openfda_neo4j_service.merge_disease_to_neo4j(
        name=disease.name,
        description=disease.description or "",
        icd_code=disease.icd_code or "",
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create disease node")
    return {"status": "created", "disease": disease.name}


@router.post("/relationships/treats")
def create_treats_relationship(interaction: DrugInteraction):
    """Create a TREATS relationship between a drug and disease."""
    logger.info(f"Creating TREATS relationship: {interaction.drug_name} -> {interaction.disease_name}")
    result = openfda_neo4j_service.merge_treats_relationship(
        drug_name=interaction.drug_name,
        disease_name=interaction.disease_name,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create TREATS relationship")
    return {"status": "created", "drug": interaction.drug_name, "disease": interaction.disease_name}


@router.get("/stats")
def get_neo4j_stats():
    """Get statistics about Neo4j data."""
    drug_count = openfda_neo4j_service.verify_drug_count()
    disease_count = openfda_neo4j_service.verify_disease_count()
    logger.info(f"Neo4j stats: drugs={drug_count}, diseases={disease_count}")
    return {
        "total_drugs": drug_count,
        "total_diseases": disease_count,
    }


@router.get("/graph", response_model=GraphResponse)
def get_graph_data(limit: int = Query(100, ge=1, le=1000)):
    """Get all nodes and relationships for graph visualization."""
    return neo4j_service.get_graph_data(limit=limit)
