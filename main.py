"""Dommoda FastAPI application entry point.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError

from app.config import settings

_logger = logging.getLogger(__name__)
_TZ_DUSHANBE = timezone(timedelta(hours=5))


async def _size_sync_scheduler() -> None:
    """Check every 10 min; fire size sync at 01:00 Dushanbe time (UTC+5).

    Render free tier kills the process after ~15 min of no HTTP traffic.
    The GitHub Actions healthcheck pings at :00 and :30 every hour, so
    the process restarts at 20:00 UTC = 01:00 Dushanbe.  The first loop
    iteration runs immediately on startup — if it is 01:xx and the sync
    has not run today, it fires right away.
    """
    last_run_date: date | None = None
    while True:
        try:
            now = datetime.now(_TZ_DUSHANBE)
            if now.hour == 1 and last_run_date != now.date():
                last_run_date = now.date()
                _logger.info("Scheduled size sync: starting")
                from app.services.lamoda_sync import run_full_sync
                await run_full_sync()
                _logger.info("Scheduled size sync: complete")
        except Exception as exc:
            _logger.exception("Scheduled size sync error: %s", exc)
        await asyncio.sleep(600)


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
    from sqlalchemy.ext.asyncio import create_async_engine
    # ALTER TYPE ADD VALUE requires AUTOCOMMIT — create a separate autocommit engine
    _ddl_engine = create_async_engine(engine.url, isolation_level="AUTOCOMMIT")
    try:
        async with _ddl_engine.connect() as conn:
            await conn.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'received'"))
    except Exception:
        pass
    finally:
        await _ddl_engine.dispose()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Products — idempotent column additions
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100)"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS price_original INTEGER"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_percent INTEGER"))
        # Orders — add missing columns and make optional fields nullable
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS email VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS city VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS street VARCHAR(300)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS building VARCHAR(50)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS apartment VARCHAR(50)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS zip_code VARCHAR(20)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS comment TEXT"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS promo_discount INTEGER NOT NULL DEFAULT 0"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS promo_code VARCHAR(50)"))
        # Ensure updated_at column exists (may be missing on older instances)
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))
        # Drop NOT NULL from optional order fields (may have been created NOT NULL in earlier schema)
        for col in ("recipient_name", "email", "city", "street", "building", "apartment", "zip_code", "comment", "promo_code"):
            await conn.execute(text(f"ALTER TABLE orders ALTER COLUMN {col} DROP NOT NULL"))
        # Back-fill sku from description "Артикул: XXX" for products parsed before the sku column was deployed
        await conn.execute(text(
            "UPDATE products SET sku = TRIM(SUBSTRING(description FROM 10)) "
            "WHERE sku IS NULL AND description LIKE 'Артикул: %'"
        ))

        # ------------------------------------------------------------------ #
        # STEP 1 — Fix CATEGORY (men / women / kids / sport) first.
        # Source of truth: Russian gender keywords in the product name, and
        # women-exclusive item types (dresses, skirts).  No brand-based guesses.
        # ------------------------------------------------------------------ #

        # Explicit men keywords in name → "men"
        await conn.execute(text(
            "UPDATE products SET category = 'men' "
            "WHERE (LOWER(name) LIKE '%мужск%' OR LOWER(name) LIKE '%мужчин%') "
            "AND category NOT IN ('kids')"
        ))

        # Explicit women keywords in name → "women"
        await conn.execute(text(
            "UPDATE products SET category = 'women' "
            "WHERE (LOWER(name) LIKE '%женск%' OR LOWER(name) LIKE '%женщин%') "
            "AND category NOT IN ('kids')"
        ))

        # Women-exclusive item types → "women" (dresses, skirts, blouses are never men's/kids')
        await conn.execute(text(
            "UPDATE products SET category = 'women' "
            "WHERE subcategory IN ('dresses', 'skirts', 'blouses') "
            "AND category NOT IN ('kids')"
        ))

        # "спортивн" in name → "sport" (applies to both men's and women's sportswear)
        await conn.execute(text(
            "UPDATE products SET category = 'sport' "
            "WHERE LOWER(name) LIKE '%спортивн%' "
            "AND category NOT IN ('kids')"
        ))

        # ------------------------------------------------------------------ #
        # STEP 2 — Back-fill SUBCATEGORY by keywords in name.
        # Order matters: specific patterns first, generic last.
        # ------------------------------------------------------------------ #
        _subcat_updates = [
            ("jumpsuits",  "комбинезон"),
            ("jumpsuits",  "сарафан"),
            ("jumpsuits",  "боди"),
            ("blazers",    "жакет"),
            ("blazers",    "костюм"),
            ("hoodies",    "худи"),
            ("hoodies",    "свитшот"),
            ("hoodies",    "толстовк"),
            ("knitwear",   "свитер"),
            ("knitwear",   "джемпер"),
            ("knitwear",   "кардиган"),
            ("knitwear",   "пуловер"),
            ("knitwear",   "водолазк"),
            ("dresses",    "платье"),
            ("skirts",     "юбк"),
            ("jeans",      "джинс"),
            ("leggings",   "леггинс"),
            ("leggings",   "тайтс"),
            ("sport_sets", "спортивный костюм"),
            ("shorts",     "шорт"),
            ("pants",      "брюк"),
            ("pants",      "лосин"),
            ("jackets",    "куртк"),
            ("jackets",    "пальто"),
            ("jackets",    "пуховик"),
            ("jackets",    "бомбер"),
            ("jackets",    "ветровк"),
            ("jackets",    "анорак"),
            ("jackets",    "пиджак"),
            ("jackets",    "жилет"),
            ("jackets",    "накидк"),
            ("shirts",     "рубашк"),
            ("blouses",    "блуз"),
            ("tshirts",    "футболк"),
            ("tshirts",    "майк"),
            ("tshirts",    "лонгслив"),
            ("tshirts",    "джерси"),
            ("tshirts",    " топ"),
            ("polo",       "поло"),
            ("shoes",      "кроссовк"),
            ("shoes",      "кед"),
            ("shoes",      "туфл"),
            ("shoes",      "ботинк"),
            ("shoes",      "сапог"),
            ("shoes",      "мокасин"),
            ("shoes",      "балетк"),
            ("shoes",      "сандали"),
            ("shoes",      "слипон"),
            ("shoes",      "сланц"),
            ("shoes",      "шлепанц"),
            ("shoes",      "слипер"),
            ("shoes",      "тапочк"),
            ("shoes",      "сабо"),
            ("accessories","ремен"),
            ("accessories","сумк"),
            ("accessories","шарф"),
            ("accessories","платок"),
            ("accessories","очки"),
            ("accessories","панам"),
            ("accessories","кепк"),
            ("accessories","бейсболк"),
            ("accessories","шапк"),
            ("accessories","перчатк"),
            ("accessories","носк"),
            ("accessories","браслет"),
            ("accessories","колье"),
            ("accessories","серьг"),
            ("accessories","трус"),
            ("accessories","боксер"),
            ("accessories","купальн"),
        ]
        for subcat, keyword in _subcat_updates:
            await conn.execute(text(
                "UPDATE products SET subcategory = :subcat "
                "WHERE (subcategory IS NULL OR subcategory = '') "
                "AND LOWER(name) LIKE :pattern"
            ), {"subcat": subcat, "pattern": f"%{keyword}%"})

    scheduler_task = asyncio.create_task(_size_sync_scheduler())
    yield
    scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await scheduler_task
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
    origin = request.headers.get("origin", "")
    cors_headers: dict[str, str] = {}
    if origin and origin in settings.get_cors_origins():
        cors_headers["access-control-allow-origin"] = origin
        cors_headers["access-control-allow-credentials"] = "true"
    import logging
    logging.getLogger(__name__).exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=cors_headers,
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
