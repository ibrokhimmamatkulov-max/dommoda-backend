from __future__ import annotations

import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductListOut, ProductOut

router = APIRouter(prefix="/api/products", tags=["products"])

DB = Annotated[AsyncSession, Depends(get_db)]

SortParam = Literal["popular", "price_asc", "price_desc", "new"]


_EXCLUDE_KEYWORDS = [
    "трус", "носк", "бюстгальтер", "бра ", "слип", "боксер", "плавк",
    "колгот", "чулк", "термобелье", "нижнее белье", "подвязк",
    "наклейки на грудь", "купальник",
]

@router.get(
    "/featured",
    response_model=list[ProductOut],
    response_model_by_alias=True,
    summary="Get featured products for home page — newest, excluding underwear/socks",
)
async def get_featured_products(
    db: DB,
    limit: int = Query(12, ge=1, le=48),
    offset: int = Query(0, ge=0),
) -> list[ProductOut]:
    from sqlalchemy import and_
    exclusions = [Product.name.ilike(f"%{kw}%") for kw in _EXCLUDE_KEYWORDS]
    result = await db.execute(
        select(Product)
        .where(and_(Product.in_stock.is_(True), *[~ex for ex in exclusions]))
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    products = result.scalars().all()
    return [ProductOut.from_orm_product(p) for p in products]


@router.get(
    "/brands",
    response_model=list[dict],
    summary="List all brands with product counts",
)
async def list_brands(db: DB) -> list[dict]:
    result = await db.execute(
        select(Product.brand, func.count(Product.id).label("count"))
        .where(Product.in_stock.is_(True))
        .group_by(Product.brand)
        .order_by(func.count(Product.id).desc())
    )
    return [{"name": row.brand, "count": row.count} for row in result.all()]


@router.get(
    "/{product_id}",
    response_model=ProductOut,
    response_model_by_alias=True,
    summary="Get a single product by ID",
)
async def get_product(product_id: str, db: DB) -> ProductOut:
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return ProductOut.from_orm_product(product)


@router.get(
    "",
    response_model=ProductListOut,
    response_model_by_alias=True,
    summary="List products with optional filtering and sorting",
)
async def list_products(
    db: DB,
    category: str | None = Query(None),
    subcategory: str | None = Query(None),
    brand: str | None = Query(None, description="Filter by exact brand name"),
    search: str | None = Query(None, description="Search by name or brand"),
    sort: SortParam = Query("popular"),
    has_discount: bool | None = Query(None, description="Filter to only discounted items"),
    size: str | None = Query(None, description="Filter to products where this size is available"),
    min_price: int | None = Query(None, ge=0, description="Minimum price in RUB"),
    max_price: int | None = Query(None, ge=0, description="Maximum price in RUB"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
) -> ProductListOut:
    stmt = select(Product).where(Product.in_stock.is_(True))

    if category is not None:
        stmt = stmt.where(Product.category == category)
    if subcategory is not None:
        stmt = stmt.where(Product.subcategory == subcategory)
    if brand is not None:
        stmt = stmt.where(Product.brand == brand)
    if has_discount is True:
        stmt = stmt.where(Product.discount_percent > 0)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    if search is not None and search.strip():
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Product.name.ilike(pattern), Product.brand.ilike(pattern))
        )
    # Size filter: JSON contains the size label with available=true
    # Uses PostgreSQL JSON operator — sizes_json is a TEXT column with JSON array
    if size is not None:
        stmt = stmt.where(
            Product.sizes_json.contains(json.dumps({"label": size, "available": True}))
        )

    match sort:
        case "price_asc":
            stmt = stmt.order_by(Product.price.asc())
        case "price_desc":
            stmt = stmt.order_by(Product.price.desc())
        case "new":
            stmt = stmt.order_by(Product.created_at.desc())
        case _:
            stmt = stmt.order_by(Product.review_count.desc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return ProductListOut(
        products=[ProductOut.from_orm_product(p) for p in products],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + len(products)) < total,
    )
