import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.redis_client import init_redis, close_redis
from app.core.kafka_client import init_kafka, close_kafka
from app.routers import click_router, webhook_router
from app.agents import router as agents_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("revsplit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown routines."""
    logger.info("Initializing RevSplit services...")
    await init_redis()
    await init_kafka()
    yield
    logger.info("Shutting down RevSplit services...")
    await close_redis()
    await close_kafka()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-Performance Programmatic Cashback & Affiliate Arbitrage Engine with Autonomous Multi-Agent AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Frontend Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Service Routers
app.include_router(click_router.router)
app.include_router(webhook_router.router)
app.include_router(agents_router.router)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "HEALTHY", "engine": settings.PROJECT_NAME, "multi_agent_system": "ONLINE"}
