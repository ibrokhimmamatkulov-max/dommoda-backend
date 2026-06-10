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
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError

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
        # Idempotent column additions / constraint fixes for existing DBs
        await conn.execute(text(
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100)"
        ))
    # Make zip_code nullable — separate transaction so failure doesn't block startup
    try:
        async with engine.begin() as conn2:
            await conn2.execute(text(
                "ALTER TABLE orders ALTER COLUMN zip_code DROP NOT NULL"
            ))
    except Exception:
        pass  # already nullable or table freshly created as nullable
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
# Global exception handler — ensures CORS headers are present on all errors
# (ServerErrorMiddleware bypasses CORSMiddleware, so we catch here instead)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def _all_exceptions(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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
