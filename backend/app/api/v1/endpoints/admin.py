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
    """
    Chỉ dành cho Admin: Lấy danh sách toàn bộ người dùng trong hệ thống (hỗ trợ phân trang).
    """
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
    """
    Chỉ dành cho Admin: Cập nhật vai trò/quyền quản trị viên (superuser) của người dùng theo ID.
    """
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
    """
    Chỉ dành cho Admin: Cập nhật trạng thái hoạt động (kích hoạt hoặc vô hiệu hóa) của người dùng theo ID.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.repositories import user_repository
    user = user_repository.update_user_status(db, id, is_active)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/stats")
def admin_get_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Chỉ dành cho Admin: Lấy số liệu thống kê tổng hợp của hệ thống bao gồm: người dùng, đồ thị Neo4j, các thuốc tìm kiếm hàng đầu, và các chủ đề chat phổ biến.
    """
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
from typing import Optional, Dict, Any, List

class AIConfigUpdate(BaseModel):
    model: Optional[str] = None
    api_key: Optional[str] = None
    system_version: Optional[str] = None
    performance_stats: Optional[Dict[str, float]] = None
    feature_modules: Optional[Dict[str, bool]] = None
    disclaimers: Optional[List[Dict[str, str]]] = None

@router.get("/ai-config")
def admin_get_ai_config(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Chỉ dành cho Admin: Lấy thông tin cấu hình AI hiện tại (API key, model) và số lượng lượt sử dụng AI trong tháng.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.core.ai_settings_store import get_ai_settings
    from app.services.chat_service import chat_service
    config = get_ai_settings()
    quota_used = chat_service.get_monthly_ai_usage(db)
    
    # Gộp quota_used vào kết quả trả về
    response_data = dict(config)
    response_data["quota_used"] = quota_used
    return response_data

@router.post("/ai-config")
def admin_update_ai_config(
    config_in: AIConfigUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Chỉ dành cho Admin: Cập nhật cấu hình AI (API key, model, phiên bản hệ thống, v.v.).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.core.ai_settings_store import save_ai_settings
    
    # Chỉ lưu các trường có giá trị được gửi lên
    update_data = config_in.model_dump(exclude_unset=True)
    if update_data:
        save_ai_settings(update_data)
        
    return {"success": True}

@router.get("/ai-models")
async def admin_get_ai_models(
    current_user: Annotated[User, Depends(get_current_user)],
    api_key: Optional[str] = Query(None)
):
    """
    Chỉ dành cho Admin: Lấy danh sách các mô hình Gemini khả dụng thông qua Google API.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import httpx
    from app.core.ai_settings_store import get_ai_settings
    
    key_to_use = api_key
    if not key_to_use:
        config = get_ai_settings()
        key_to_use = config.get("api_key")
        
    # Danh sách mô hình dự phòng nếu không có API Key
    fallback_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.5-flash"]
    if not key_to_use:
        return {"models": fallback_models}
        
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models?key={key_to_use}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(endpoint, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                available_models = []
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        name = m.get("name", "").replace("models/", "")
                        if name.startswith("gemini"):
                            available_models.append(name)
                
                # Nếu API trả về rỗng, dùng fallback
                if not available_models:
                    return {"models": fallback_models}
                    
                # Sắp xếp để ưu tiên bản mới (hoặc đảo ngược chuỗi để 3.5 lên đầu)
                available_models.sort(reverse=True)
                return {"models": available_models}
            else:
                return {"models": fallback_models}
        except Exception:
            return {"models": fallback_models}

class AITestRequest(BaseModel):
    api_key: str

@router.post("/ai-config/test")
async def admin_test_ai_config(
    test_in: AITestRequest,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Chỉ dành cho Admin: Kiểm tra kết nối và tính hợp lệ của API Key Google Gemini.
    """
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
