from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
import logging

# Neo4j service check
from app.services.neo4j_service import neo4j_service
from app.services.startup_import_service import perform_startup_import

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Medical Chatbot Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# v1 routers (auth, health, neo4j, import)
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root health check (không cần prefix)
@app.get("/health", tags=["health"])
def root_health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger = logging.getLogger("app.error")
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


@app.on_event("startup")
def on_startup() -> None:
    logger = logging.getLogger("app.startup")
    logger.info("=" * 60)
    logger.info("Backend Application Starting")
    logger.info(f"Project: {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    try:
        ok = neo4j_service.verify_connectivity()
        if ok:
            logger.info("✓ Neo4j connected successfully")
        else:
            logger.error("✗ Neo4j connectivity check returned False")
    except Exception as exc:  # pragma: no cover - runtime logging
        logger.exception(f"✗ Neo4j connection failed during startup: {exc}")
    logger.info("=" * 60)
    
    # Auto-import openFDA drugs
    try:
        perform_startup_import()
    except Exception as exc:
        logger.exception(f"Startup import error (non-blocking): {exc}")
