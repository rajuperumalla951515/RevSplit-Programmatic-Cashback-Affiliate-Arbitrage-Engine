from fastapi import APIRouter
from app.routers.click_router import router as click_router
from app.routers.webhook_router import router as webhook_router
from app.agents.router import router as agents_router

# Aggregated API router that groups all RevSplit route handlers
api_router = APIRouter()
api_router.include_router(click_router)
api_router.include_router(webhook_router)
api_router.include_router(agents_router)

__all__ = ["api_router", "click_router", "webhook_router", "agents_router"]
