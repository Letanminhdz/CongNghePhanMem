from fastapi import APIRouter, Depends
from typing import Any, Annotated

from app.api.v1.endpoints.deps import get_current_active_superuser
from app.models.user import User

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/medicine/{name}")
def get_medicine_debug(
    name: str,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> Any:
    """
    Endpoint debug để trực tiếp kiểm tra việc truy xuất thông tin thuốc từ Neo4j.
    """
    logger.info(f"DEBUG REQ: Medicine name = '{name}'")
    from app.services.medicine_lookup_service import medicine_lookup_service
    detail = medicine_lookup_service.get_medicine_detail(name)
    logger.info(f"DEBUG RES: Detail = {detail}")
    
    return {
        "requested_name": name,
        "detail": detail,
        "type": str(type(detail))
    }

@router.get("/disease/{name}")
def get_disease_debug(
    name: str,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> Any:
    """
    Endpoint debug để trực tiếp kiểm tra việc truy xuất thông tin bệnh từ Neo4j.
    """
    logger.info(f"DEBUG REQ: Disease name = '{name}'")
    from app.services.disease_lookup_service import disease_lookup_service
    detail = disease_lookup_service.get_disease_detail(name)
    logger.info(f"DEBUG RES: Detail = {detail}")
    
    return {
        "requested_name": name,
        "detail": detail,
        "type": str(type(detail))
    }
