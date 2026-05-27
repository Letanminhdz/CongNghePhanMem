from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, import_data, neo4j, users, compat

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(neo4j.router)
api_router.include_router(import_data.router)
api_router.include_router(users.router)
api_router.include_router(compat.router)
