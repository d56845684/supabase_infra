from fastapi import APIRouter
from app.api.v1 import auth, users, health, line_auth, line_notifications, courses

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(health.router)
api_router.include_router(line_auth.router)
api_router.include_router(line_notifications.router)
api_router.include_router(courses.router)