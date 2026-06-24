from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
import logging

# Kiểm tra dịch vụ Neo4j
from app.services.neo4j_service import neo4j_service

# app: Đối tượng FastAPI đại diện cho toàn bộ ứng dụng web API
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Medical Chatbot Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Cấu hình CORS
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Router v1 (auth, health, neo4j, import)
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root health check (không cần prefix)
@app.get("/health", tags=["health"])
def root_health():
    """
    Mục đích: Cung cấp API kiểm tra trạng thái hoạt động cơ bản (health check) của máy chủ Backend.
    Cơ chế hoạt động: Trả về trạng thái "ok" dưới dạng JSON để thông báo máy chủ đang chạy.
    """
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Mục đích: Bắt và xử lý toàn bộ các lỗi ngoại lệ (Exceptions) chưa được bắt trong ứng dụng để tránh sập máy chủ và ẩn thông tin chi tiết lỗi với người dùng cuối.
    Cơ chế hoạt động:
    1. Lấy đối tượng logger để ghi nhận stack trace lỗi.
    2. Trả về phản hồi HTTP 500 kèm theo thông báo chung "Internal Server Error" ở dạng JSON.
    """
    # request: Đối tượng HTTP Request gây ra lỗi
    # exc: Đối tượng ngoại lệ (exception) chứa thông tin chi tiết lỗi
    # logger: Đối tượng ghi nhật ký lỗi
    logger = logging.getLogger("app.error")
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


@app.on_event("startup")
def on_startup() -> None:
    """
    Mục đích: Thực thi các thiết lập và kiểm tra kết nối tài nguyên khi ứng dụng bắt đầu khởi động.
    Cơ chế hoạt động:
    1. Ghi log các thông tin cơ bản về môi trường và chế độ debug.
    2. Cố gắng kết nối và kiểm tra tính kết nối tới cơ sở dữ liệu đồ thị Neo4j.
    """
    # logger: Đối tượng ghi nhật ký hoạt động khởi động ứng dụng
    logger = logging.getLogger("app.startup")
    logger.info("=" * 60)
    logger.info("Backend Application Starting")
    logger.info(f"Project: {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    try:
        # ok: Kết quả kiểm tra kết nối tới Neo4j (True nếu thành công)
        ok = neo4j_service.verify_connectivity()
        if ok:
            logger.info("✓ Neo4j connected successfully")
        else:
            logger.error("✗ Neo4j connectivity check returned False")
    except Exception as exc:  # pragma: no cover - ghi log runtime
        logger.exception(f"✗ Neo4j connection failed during startup: {exc}")
    logger.info("=" * 60)
    
    logger.info("Startup openFDA import disabled; using database-first seed data")
