"""Dommoda FastAPI application entry point.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models import (  # noqa: F401 — import side-effect: registers metadata
    Category,
    Order,
    Product,
    PromoCode,
)
from app.database import Base
from app.routers import (
    admin_router,
    analytics_router,
    user_auth_router,
    cart_router,
    categories_router,
    orders_router,
    products_router,
    promo_router,
    settings_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create all tables on startup if they do not exist.

    In production you would rely solely on Alembic migrations; this is
    kept here as a convenience for local development without needing to
    run ``alembic upgrade head`` first.
    """
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent column additions for existing DBs (safe to run every startup)
        await conn.execute(text(
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100)"
        ))
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(admin_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(promo_router)
app.include_router(settings_router)
app.include_router(analytics_router)
app.include_router(user_auth_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"], summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}
