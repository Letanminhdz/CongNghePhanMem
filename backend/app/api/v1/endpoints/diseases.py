"""
Các endpoint tra cứu bệnh lý.
Xử lý các tìm kiếm và truy xuất thông tin bệnh lý.
"""

from fastapi import APIRouter, HTTPException, Query, Path, status
import logging

from app.services.disease_lookup_service import disease_lookup_service
from app.schemas.disease import DiseaseSearchResponse, DiseaseDetailResponse, DiseaseTreatmentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get("/search", response_model=DiseaseSearchResponse)
def search_diseases(
    q: str = Query(..., min_length=0, max_length=255, description="Search query"), # q: Từ khóa tìm kiếm bệnh lý do người dùng nhập vào
    limit: int = Query(10, ge=1, le=100, description="Max results"), # limit: Giới hạn số lượng kết quả tối đa trả về trên mỗi trang
    skip: int = Query(0, ge=0, description="Number of results to skip"), # skip: Số lượng kết quả cần bỏ qua (sử dụng trong việc phân trang)
):
    """
    Mục đích: Tìm kiếm các bệnh lý theo tên hoặc mô tả.
    Cơ chế hoạt động: Nhận từ khóa tìm kiếm và các thông số phân trang, gọi tầng service `disease_lookup_service.search_diseases` để thực hiện truy vấn trong Neo4j và trả về kết quả định dạng chuẩn.
    """
    logger.info(f"GET /api/v1/diseases/search?q={q}&limit={limit}&skip={skip}")
    try:
        # result: Kết quả tìm kiếm bệnh lý được lấy từ cơ sở dữ liệu đồ thị Neo4j thông qua service
        result = disease_lookup_service.search_diseases(query=q, limit=limit, skip=skip)
        return result
    except Exception as exc:
        logger.exception(f"Error searching diseases: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search diseases",
        )


@router.get("/{disease_name}/detail", response_model=DiseaseDetailResponse)
def get_disease_detail(
    disease_name: str = Path(..., description="Disease name"), # disease_name: Tên của bệnh lý cần lấy thông tin chi tiết
):
    """
    Mục đích: Lấy thông tin chi tiết về một bệnh lý cụ thể bao gồm mô tả, mức độ và các triệu chứng liên quan.
    Cơ chế hoạt động: Nhận tên bệnh lý từ đường dẫn URL, gọi `disease_lookup_service.get_disease_detail` để tìm kiếm nút bệnh lý và các nút triệu chứng liên kết trong đồ thị Neo4j.
    """
    logger.info(f"GET /api/v1/diseases/{disease_name}/detail")
    try:
        # disease: Đối tượng chứa thông tin chi tiết của bệnh lý truy vấn được từ cơ sở dữ liệu
        disease = disease_lookup_service.get_disease_detail(disease_name)
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disease '{disease_name}' not found",
            )
        return disease
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error getting disease detail: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve disease details",
        )


@router.get("/{disease_name}/treatments", response_model=DiseaseTreatmentResponse)
def get_disease_treatments(
    disease_name: str = Path(..., description="Disease name"), # disease_name: Tên bệnh lý cần tìm thuốc điều trị
    limit: int = Query(10, ge=1, le=100, description="Max results"), # limit: Giới hạn số lượng thuốc tối đa trả về
    skip: int = Query(0, ge=0, description="Number of results to skip"), # skip: Số lượng thuốc bỏ qua để phân trang kết quả
):
    """
    Mục đích: Lấy danh sách các loại thuốc dùng để điều trị một bệnh lý cụ thể.
    Cơ chế hoạt động: Tìm kiếm các mối quan hệ TREATS (điều trị) từ nút Bệnh lý đến nút Thuốc trong cơ sở dữ liệu đồ thị Neo4j và trả về danh sách thuốc tương ứng.
    """
    logger.info(f"GET /api/v1/diseases/{disease_name}/treatments?limit={limit}&skip={skip}")
    try:
        # medicines: Danh sách các thuốc có quan hệ điều trị đối với bệnh lý được chỉ định
        medicines = disease_lookup_service.get_treating_medicines(disease_name, limit=limit, skip=skip)
        if not medicines:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No treatments found for disease '{disease_name}'",
            )
        return DiseaseTreatmentResponse(
            disease_name=disease_name,
            treatments=medicines,
            total=len(medicines),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error getting disease treatments: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve disease treatments",
        )
