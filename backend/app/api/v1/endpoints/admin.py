from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Annotated, Optional, Literal
from pydantic import BaseModel

from app.api.v1.endpoints.deps import get_current_user
from app.models.user import User
from app.services.import_openfda_service import import_openfda_drugs
from app.services.neo4j_service import neo4j_service

router = APIRouter(prefix="/admin", tags=["admin"])

# ============================================
# PYDANTIC SCHEMAS FOR ADMIN CRUD
# ============================================

class DrugCreateRequest(BaseModel):
    name: str
    generic_name: Optional[str] = None
    purpose: Optional[str] = None
    indications: Optional[str] = None
    warnings: Optional[str] = None
    dosage: Optional[str] = None

class DiseaseCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icd_code: Optional[str] = None

class InteractionCreateRequest(BaseModel):
    drug_1: str
    drug_2: str
    severity: str = "moderate"
    description: str = ""

class BulkImportRequest(BaseModel):
    drugs: list[DrugCreateRequest] = []
    diseases: list[DiseaseCreateRequest] = []
    interactions: list[InteractionCreateRequest] = []
    treatments: list[dict] = []
    symptoms: list[dict] = []

class AISettingsUpdateRequest(BaseModel):
    provider: Optional[Literal["openai", "gemini", "groq", "none"]] = None
    model: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    timeout: Optional[int] = None

# ============================================
# EXISTING IMPORT & GRAPH MANAGEMENT ENDPOINTS
# ============================================

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

# ============================================
# NEW CRUD ENDPOINTS: DRUGS, DISEASES, RULES
# ============================================

@router.post("/drugs")
def create_drug(
    current_user: Annotated[User, Depends(get_current_user)],
    drug: DrugCreateRequest
):
    """
    Admin only: Create/Merge a Drug node in Neo4j.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    success = neo4j_service.merge_drug(drug.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create drug")
    return {"success": True, "message": f"Drug '{drug.name}' created/merged successfully"}

@router.put("/drugs/{name}")
def update_drug(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    drug: DrugCreateRequest
):
    """
    Admin only: Update a Drug node's properties.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    data = drug.dict()
    data["name"] = name
    success = neo4j_service.merge_drug(data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update drug")
    return {"success": True, "message": f"Drug '{name}' updated successfully"}

@router.delete("/drugs/{name}")
def delete_drug(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Admin only: Delete a Drug node and all its relationships from Neo4j.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    query = "MATCH (d:Drug) WHERE toLower(trim(d.name)) = toLower(trim($name)) DETACH DELETE d"
    try:
        neo4j_service._repository.execute_write(query, name=name)
        return {"success": True, "message": f"Drug '{name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete drug: {e}")

@router.post("/diseases")
def create_disease(
    current_user: Annotated[User, Depends(get_current_user)],
    disease: DiseaseCreateRequest
):
    """
    Admin only: Create/Merge a Disease node in Neo4j.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    query = """
    MERGE (d:Disease {name: $name})
    SET d.description = $description,
        d.icd_code = $icd_code,
        d.updated_at = datetime()
    RETURN d.name AS name
    """
    try:
        neo4j_service._repository.execute_write(
            query,
            name=disease.name,
            description=disease.description,
            icd_code=disease.icd_code
        )
        return {"success": True, "message": f"Disease '{disease.name}' created/merged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create disease: {e}")

@router.put("/diseases/{name}")
def update_disease(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    disease: DiseaseCreateRequest
):
    """
    Admin only: Update a Disease node's properties.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    query = """
    MATCH (d:Disease) WHERE toLower(trim(d.name)) = toLower(trim($name))
    SET d.name = $new_name,
        d.description = $description,
        d.icd_code = $icd_code,
        d.updated_at = datetime()
    RETURN d.name AS name
    """
    try:
        neo4j_service._repository.execute_write(
            query,
            name=name,
            new_name=disease.name,
            description=disease.description,
            icd_code=disease.icd_code
        )
        return {"success": True, "message": f"Disease '{name}' updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update disease: {e}")

@router.delete("/diseases/{name}")
def delete_disease(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Admin only: Delete a Disease node and all its relationships from Neo4j.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    query = "MATCH (d:Disease) WHERE toLower(trim(d.name)) = toLower(trim($name)) DETACH DELETE d"
    try:
        neo4j_service._repository.execute_write(query, name=name)
        return {"success": True, "message": f"Disease '{name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete disease: {e}")

@router.post("/interactions")
def create_interaction(
    current_user: Annotated[User, Depends(get_current_user)],
    interaction: InteractionCreateRequest
):
    """
    Admin only: Create/Update an interaction rule relationship between two drugs.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    success = neo4j_service.create_interacts_relationship(
        interaction.drug_1,
        interaction.drug_2,
        interaction.severity,
        interaction.description
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create interaction relationship")
    return {"success": True, "message": f"Interaction between '{interaction.drug_1}' and '{interaction.drug_2}' created/merged successfully"}

@router.delete("/interactions/{drug_1}/with/{drug_2}")
def delete_interaction(
    drug_1: str,
    drug_2: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Admin only: Delete an interaction relationship between two drugs.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    query = """
    MATCH (d1:Drug)-[r:INTERACTS_WITH]-(d2:Drug)
    WHERE toLower(trim(d1.name)) = toLower(trim($drug_1))
      AND toLower(trim(d2.name)) = toLower(trim($drug_2))
    DELETE r
    """
    try:
        neo4j_service._repository.execute_write(query, drug_1=drug_1, drug_2=drug_2)
        return {"success": True, "message": f"Interaction between '{drug_1}' and '{drug_2}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete interaction: {e}")

# ============================================
# BULK IMPORT ENDPOINT
# ============================================

@router.post("/import/bulk")
def bulk_import(
    current_user: Annotated[User, Depends(get_current_user)],
    payload: BulkImportRequest
):
    """
    Admin only: Import multiple drugs, diseases, symptoms, treatments and interaction rules.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    
    drug_count = 0
    disease_count = 0
    interaction_count = 0
    treatment_count = 0
    symptom_count = 0
    
    # 1. Import Drugs
    for drug in payload.drugs:
        if neo4j_service.merge_drug(drug.dict()):
            drug_count += 1
            
    # 2. Import Diseases
    for disease in payload.diseases:
        query = """
        MERGE (d:Disease {name: $name})
        SET d.description = $description,
            d.icd_code = $icd_code,
            d.updated_at = datetime()
        RETURN d.name AS name
        """
        try:
            neo4j_service._repository.execute_write(
                query,
                name=disease.name,
                description=disease.description,
                icd_code=disease.icd_code
            )
            disease_count += 1
        except Exception:
            pass
            
    # 3. Import Interactions
    for inter in payload.interactions:
        if neo4j_service.create_interacts_relationship(
            inter.drug_1, inter.drug_2, inter.severity, inter.description
        ):
            interaction_count += 1
            
    # 4. Import treatments
    for treat in payload.treatments:
        drug_name = treat.get("drug_name")
        disease_name = treat.get("disease_name")
        if drug_name and disease_name:
            if neo4j_service.merge_treats_relationship(drug_name, disease_name):
                treatment_count += 1
                 
    # 5. Import symptoms
    for symp in payload.symptoms:
        disease_name = symp.get("disease_name")
        symptom_name = symp.get("symptom_name")
        if disease_name and symptom_name:
            if neo4j_service.merge_has_symptom_relationship(disease_name, symptom_name):
                symptom_count += 1
                 
    # Refresh cache
    from app.services.ner_service import ner_service
    try:
        ner_service.refresh_entities()
    except Exception:
        pass
         
    return {
        "success": True,
        "imported": {
            "drugs": drug_count,
            "diseases": disease_count,
            "interactions": interaction_count,
            "treatments": treatment_count,
            "symptoms": symptom_count
        }
    }

# ============================================
# AI CONFIGURATION ENDPOINTS
# ============================================

def update_env_file(updates: dict):
    import os
    env_path = ".env"
    if not os.path.exists(env_path):
        env_path = "../.env"
    if not os.path.exists(env_path):
        env_path = "../../.env"
    if not os.path.exists(env_path):
        env_path = ".env"
        
    content_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content_lines = f.readlines()
            
    env_dict = {}
    for line in content_lines:
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
            parts = line_stripped.split("=", 1)
            env_dict[parts[0].strip()] = parts[1].strip()
            
    for k, v in updates.items():
        if v is not None:
            env_dict[k] = str(v)
            
    new_lines = []
    written_keys = set()
    if os.path.exists(env_path):
        for line in content_lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
                key = line_stripped.split("=", 1)[0].strip()
                if key in env_dict:
                    new_lines.append(f"{key}={env_dict[key]}\n")
                    written_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
     
    for k, v in env_dict.items():
        if k not in written_keys:
            new_lines.append(f"{k}={v}\n")
             
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

@router.get("/ai/settings")
def get_ai_settings(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Admin only: Read the active system AI settings.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    from app.core.config import settings
    return {
        "LLM_PROVIDER": settings.LLM_PROVIDER,
        "LLM_MODEL": settings.LLM_MODEL,
        "LLM_TIMEOUT_SECONDS": settings.LLM_TIMEOUT_SECONDS,
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_groq_key": bool(settings.GROQ_API_KEY)
    }

@router.post("/ai/settings")
def update_ai_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    payload: AISettingsUpdateRequest
):
    """
    Admin only: Update active system AI settings (persisted in .env file).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
        
    from app.core.config import settings
    
    updates = {}
    if payload.provider is not None:
        settings.LLM_PROVIDER = payload.provider
        updates["LLM_PROVIDER"] = payload.provider
    if payload.model is not None:
        settings.LLM_MODEL = payload.model
        updates["LLM_MODEL"] = payload.model
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key
        updates["OPENAI_API_KEY"] = payload.openai_api_key
    if payload.gemini_api_key is not None:
        settings.GEMINI_API_KEY = payload.gemini_api_key
        updates["GEMINI_API_KEY"] = payload.gemini_api_key
    if payload.groq_api_key is not None:
        settings.GROQ_API_KEY = payload.groq_api_key
        updates["GROQ_API_KEY"] = payload.groq_api_key
    if payload.timeout is not None:
        settings.LLM_TIMEOUT_SECONDS = payload.timeout
        updates["LLM_TIMEOUT_SECONDS"] = payload.timeout
        
    try:
        update_env_file(updates)
        return {"success": True, "message": "AI configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings file: {e}")

# ============================================
# SYSTEM LOG VIEWER ENDPOINT
# ============================================

@router.get("/logs")
def get_system_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Admin only: View the system logs generated by the application.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
        
    import os
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.abspath(os.path.join(log_dir, "../../../../backend/app.log"))
    
    if not os.path.exists(log_file):
        log_file = os.path.abspath(os.path.join(log_dir, "../../../app.log"))
        
    if not os.path.exists(log_file):
        return {"logs": [], "message": "Log file not found at expected paths"}
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Get last N lines
            last_lines = [line.strip() for line in lines[-limit:]]
            return {"logs": last_lines, "total": len(lines)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {e}")
