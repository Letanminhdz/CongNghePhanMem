from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    neo4j,
    users,
    compat,
    medicines,
    diseases,
    interactions,
    chat,
    admin,
    debug,
    search_history,
    bookmarks,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(neo4j.router)
api_router.include_router(users.router)
api_router.include_router(compat.router)
api_router.include_router(medicines.router)
api_router.include_router(diseases.router)
api_router.include_router(interactions.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
api_router.include_router(debug.router)
api_router.include_router(search_history.router)
api_router.include_router(bookmarks.router)
