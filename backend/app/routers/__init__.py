"""
API路由
"""
from app.routers.auth import router as auth_router
from app.routers.stores import router as stores_router
from app.routers.cards import router as cards_router
from app.routers.schedules import router as schedules_router
from app.routers.appointments import router as appointments_router
from app.routers.users import router as users_router
from app.routers.ai import router as ai_router

__all__ = [
    "auth_router",
    "stores_router", 
    "cards_router",
    "schedules_router",
    "appointments_router",
    "users_router",
    "ai_router",
]
