"""Database seed script.

Populates the database with:
- Products from products.json (copied from the frontend)
- Categories from categories.json (copied from the frontend)
- Promo codes: DOMMODA10 (10% off), FIRST500 (500 flat off)

Usage:
    python seed.py

The script is idempotent: running it twice won't create duplicates because
it uses INSERT OR REPLACE (SQLite) / upsert semantics.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Products and categories data — embedded directly so the seed script works
# without a running frontend. Keep in sync with the frontend JSON files or
# point PRODUCTS_FILE / CATEGORIES_FILE at the frontend data folder.
# ---------------------------------------------------------------------------

PRODUCTS_FILE = Path(__file__).parent.parent / "dommoda-app" / "src" / "data" / "products.json"
CATEGORIES_FILE = Path(__file__).parent.parent / "dommoda-app" / "src" / "data" / "categories.json"

# Fallback embedded data in case the frontend is not on this machine
EMBEDDED_PRODUCTS: list[dict] = []  # populated below
EMBEDDED_CATEGORIES: list[dict] = []  # populated below


async def seed() -> None:
    # Import here to ensure the app module path is set up correctly
    from app.database import async_session_factory, engine, Base
    import app.models  # noqa: F401 — register all models

    # Create tables if they don't exist yet (useful for fresh installs)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load data from the frontend project if available, else use embedded
    if PRODUCTS_FILE.exists():
        products_raw: list[dict] = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
        print(f"Loaded {len(products_raw)} products from {PRODUCTS_FILE}")
    else:
        products_raw = EMBEDDED_PRODUCTS
        print(f"Frontend data not found at {PRODUCTS_FILE}. Using embedded data ({len(products_raw)} products).")

    if CATEGORIES_FILE.exists():
        categories_raw: list[dict] = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
        print(f"Loaded {len(categories_raw)} categories from {CATEGORIES_FILE}")
    else:
        categories_raw = EMBEDDED_CATEGORIES
        print(f"Frontend data not found at {CATEGORIES_FILE}. Using embedded data ({len(categories_raw)} categories).")

    from app.models.product import Product
    from app.models.category import Category
    from app.models.promo import PromoCode
    from sqlalchemy import select

    async with async_session_factory() as session:
        # ------------------------------------------------------------------ #
        # Categories
        # ------------------------------------------------------------------ #
        for cat in categories_raw:
            existing = await session.get(Category, cat["id"])
            if existing is None:
                category = Category(
                    id=cat["id"],
                    label=cat["label"],
                    icon=cat["icon"],
                )
                category.subcategories = cat.get("subcategories", [])
                session.add(category)
            else:
                existing.label = cat["label"]
                existing.icon = cat["icon"]
                existing.subcategories = cat.get("subcategories", [])

        # ------------------------------------------------------------------ #
        # Products
        # ------------------------------------------------------------------ #
        for raw in products_raw:
            existing = await session.get(Product, raw["id"])
            if existing is None:
                product = Product(
                    id=raw["id"],
                    brand=raw["brand"],
                    name=raw["name"],
                    category=raw["category"],
                    subcategory=raw["subcategory"],
                    price=raw["price"],
                    price_original=raw.get("priceOriginal"),
                    discount_percent=raw.get("discountPercent"),
                    rating=raw.get("rating", 0.0),
                    review_count=raw.get("reviewCount", 0),
                    description=raw.get("description"),
                    in_stock=raw.get("inStock", True),
                )
                product.images = raw.get("images", [])
                product.sizes = raw.get("sizes", [])
                product.colors = raw.get("colors", [])
                session.add(product)
            else:
                # Update mutable fields; preserve the ID
                existing.brand = raw["brand"]
                existing.name = raw["name"]
                existing.category = raw["category"]
                existing.subcategory = raw["subcategory"]
                existing.price = raw["price"]
                existing.price_original = raw.get("priceOriginal")
                existing.discount_percent = raw.get("discountPercent")
                existing.rating = raw.get("rating", 0.0)
                existing.review_count = raw.get("reviewCount", 0)
                existing.description = raw.get("description")
                existing.in_stock = raw.get("inStock", True)
                existing.images = raw.get("images", [])
                existing.sizes = raw.get("sizes", [])
                existing.colors = raw.get("colors", [])

        # ------------------------------------------------------------------ #
        # Promo codes
        # ------------------------------------------------------------------ #
        promo_codes = [
            PromoCode(code="DOMMODA10", discount_percent=10, discount_amount=None, is_active=True),
            PromoCode(code="FIRST500", discount_percent=None, discount_amount=500, is_active=True),
        ]
        for promo in promo_codes:
            existing_promo = await session.get(PromoCode, promo.code)
            if existing_promo is None:
                session.add(promo)
            else:
                existing_promo.discount_percent = promo.discount_percent
                existing_promo.discount_amount = promo.discount_amount
                existing_promo.is_active = promo.is_active

        await session.commit()

    total_products = len(products_raw)
    total_categories = len(categories_raw)
    print(f"\nSeed complete:")
    print(f"  {total_categories} categories")
    print(f"  {total_products} products")
    print(f"  2 promo codes (DOMMODA10, FIRST500)")


if __name__ == "__main__":
    asyncio.run(seed())
