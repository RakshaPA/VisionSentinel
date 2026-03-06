"""
VisionGuard AI — FastAPI Application Entry Point
"""
from __future__ import annotations
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.models.database import create_tables
from app.api import analyze, reports


# ── Logging ───────────────────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> — {message}",
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True,
)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    try:
        create_tables()
        logger.success("Database tables verified / created")
    except Exception as exc:
        logger.warning(f"DB init warning (tables may already exist): {exc}")
    yield
    logger.info("Shutting down VisionGuard AI")


# ── App Instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Intelligent surveillance analysis combining YOLOv8 object detection "
        "with LLM-powered scene understanding and risk assessment."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router,  prefix=settings.API_V1_PREFIX)
app.include_router(reports.router,  prefix=settings.API_V1_PREFIX)


# ── Root Endpoints ────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@app.get("/", tags=["System"])
async def root():
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs":    "/docs",
        "health":  "/health",
    }
