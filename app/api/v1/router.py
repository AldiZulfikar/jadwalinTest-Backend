from fastapi import APIRouter
from app.api.v1.endpoints import bookings, environments, health, auth, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(environments.router)
api_router.include_router(bookings.router)

# Expose /health and /environments at root level for quick accessibility
root_router = APIRouter()
root_router.include_router(health.router)
root_router.include_router(environments.router)
