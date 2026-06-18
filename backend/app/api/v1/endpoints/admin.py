from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.api.v1.endpoints.deps import get_db, get_current_user
from app.models.user import User
from app.services.neo4j_service import neo4j_service
from app.services.medicine_lookup_service import medicine_lookup_service
from app.services.disease_lookup_service import disease_lookup_service
from app.schemas.medicine import MedicineCreate, MedicineUpdate, MedicineDetailResponse
from app.schemas.disease import DiseaseCreate, DiseaseUpdate, DiseaseDetailResponse
from app.schemas.chat import AILogResponse
from app.schemas.user import UserCreateAdmin, UserUpdateAdmin, UserRead, UserCreate

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/rebuild-graph")
def admin_rebuild_graph(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Chỉ dành cho Admin: Tái thiết lập các ràng buộc (constraints) và chỉ mục (indexes) trong Neo4j.
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
    Chỉ dành cho Admin: Khởi động lại (reset) hoặc dọn dẹp đồ thị Neo4j.
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
    Chỉ dành cho Admin: Lấy số liệu thống kê đồ thị Neo4j.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can perform this action")
    
    return neo4j_service.get_graph_stats()

@router.get("/users")
def admin_get_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100,
    skip: int = 0
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    return user_repository.get_users(db, limit=limit, skip=skip)

@router.put("/users/{id}/role")
def admin_update_user_role(
    id: int,
    is_superuser: bool,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    user = user_repository.update_user_role(db, id, is_superuser)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{id}/status")
def admin_update_user_status(
    id: int,
    is_active: bool,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    user = user_repository.update_user_status(db, id, is_active)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserRead)
def admin_create_user(
    user_in: UserCreateAdmin,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    db_user = user_repository.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user_create = UserCreate(
        email=user_in.email,
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        password=user_in.password
    )
    return user_repository.create_user(db, user_in=user_create, is_superuser=user_in.is_superuser)


@router.put("/users/{id}", response_model=UserRead)
def admin_update_user(
    id: int,
    user_in: UserUpdateAdmin,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    user = user_repository.get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.is_superuser is not None:
        user.is_superuser = user_in.is_superuser
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{id}")
def admin_delete_user(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    user = user_repository.get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"success": True}


@router.get("/stats")
def admin_get_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    from app.services.search_history_service import search_history_service
    from app.services.chat_service import chat_service
    
    user_stats = user_repository.get_user_stats(db)
    graph_stats = neo4j_service.get_graph_stats()
    top_medicines = search_history_service.get_top_searches(db, item_type="medicine", limit=5)
    chat_topics = chat_service.get_chat_topic_stats(db)
    
    return {
        "users": user_stats,
        "graph": graph_stats,
        "top_medicines": top_medicines,
        "chat_topics": chat_topics
    }

@router.get("/ai-logs", response_model=AILogResponse)
def admin_get_ai_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    user_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1)
):
    """Admin: Lấy nhật ký tương tác AI từ lịch sử chat (ChatHistory)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from app.services.chat_service import chat_service
    skip = (page - 1) * limit
    logs = chat_service.get_all_chat_logs(db, user_id=user_id, limit=limit, skip=skip)
    total = chat_service.get_chat_logs_count(db, user_id=user_id)
    return {"total": total, "items": logs, "page": page, "limit": limit}

from pydantic import BaseModel
class AIConfigUpdate(BaseModel):
    model: str
    api_key: str

@router.get("/ai-config")
def admin_get_ai_config(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.core.ai_settings_store import get_ai_settings
    from app.services.chat_service import chat_service
    config = get_ai_settings()
    quota_used = chat_service.get_monthly_ai_usage(db)
    return {"model": config["model"], "api_key": config["api_key"], "quota_used": quota_used}

@router.post("/ai-config")
def admin_update_ai_config(
    config_in: AIConfigUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.core.ai_settings_store import save_ai_settings
    save_ai_settings(config_in.model, config_in.api_key)
    return {"success": True}

class AITestRequest(BaseModel):
    api_key: str

@router.post("/ai-config/test")
async def admin_test_ai_config(
    test_in: AITestRequest,
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import httpx
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models?key={test_in.api_key}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(endpoint, timeout=10)
            if resp.status_code == 200:
                return {"success": True, "message": "Connection successful"}
            else:
                return {"success": False, "message": f"Invalid API Key. Status: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

# Admin Medicine CRUD (Các thao tác CRUD Thuốc của Admin)
@router.post("/medicines", response_model=MedicineDetailResponse, status_code=201)
def admin_create_medicine(
    medicine_in: MedicineCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = medicine_lookup_service.create_medicine(medicine_in.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create medicine")
    return result

@router.put("/medicines/{id}", response_model=MedicineDetailResponse)
def admin_update_medicine(
    id: str,
    medicine_in: MedicineUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = medicine_lookup_service.update_medicine(id, medicine_in.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return result

@router.delete("/medicines/{id}")
def admin_delete_medicine(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    success = medicine_lookup_service.delete_medicine(id)
    if not success:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"success": True}

# Admin Disease CRUD (Các thao tác CRUD Bệnh của Admin)
@router.post("/diseases", response_model=DiseaseDetailResponse, status_code=201)
def admin_create_disease(
    disease_in: DiseaseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = disease_lookup_service.create_disease(disease_in.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create disease")
    return result

@router.put("/diseases/{id}", response_model=DiseaseDetailResponse)
def admin_update_disease(
    id: str,
    disease_in: DiseaseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = disease_lookup_service.update_disease(id, disease_in.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Disease not found")
    return result

@router.delete("/diseases/{id}")
def admin_delete_disease(
    id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    success = disease_lookup_service.delete_disease(id)
    if not success:
        raise HTTPException(status_code=404, detail="Disease not found")
    return {"success": True}
