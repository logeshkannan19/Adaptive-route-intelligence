import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from core.config import settings
from database.database import async_engine, Base
from routers import routes

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Urban Route Optimization API v2.0")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")
    
    yield
    
    logger.info("Shutting down...")
    await async_engine.dispose()


app = FastAPI(
    title="Urban Route Optimization API",
    description="AI-powered routing with human feedback learning - Production Ready",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Urban Route Optimization API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
