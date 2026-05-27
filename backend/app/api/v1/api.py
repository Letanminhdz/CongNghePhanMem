from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    import_data,
    neo4j,
    users,
    compat,
    drugs,
    diseases,
    interactions,
    favorites,
    chat,
    admin,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(neo4j.router)
api_router.include_router(import_data.router)
api_router.include_router(users.router)
api_router.include_router(compat.router)
api_router.include_router(drugs.router)
api_router.include_router(diseases.router)
api_router.include_router(interactions.router)
api_router.include_router(favorites.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
