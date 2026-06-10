from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductListOut, ProductOut

router = APIRouter(prefix="/api/products", tags=["products"])

# Dependency alias for cleaner signatures
DB = Annotated[AsyncSession, Depends(get_db)]

SortParam = Literal["popular", "price_asc", "price_desc", "new"]


@router.get(
    "/featured",
    response_model=list[ProductOut],
    response_model_by_alias=True,
    summary="Get featured products for the home page (top 4 by review count)",
)
async def get_featured_products(db: DB) -> list[ProductOut]:
    """Return the 4 most-reviewed in-stock products for the homepage banner."""
    result = await db.execute(
        select(Product)
        .where(Product.in_stock.is_(True))
        .order_by(Product.review_count.desc())
        .limit(4)
    )
    products = result.scalars().all()
    return [ProductOut.from_orm_product(p) for p in products]


@router.get(
    "/{product_id}",
    response_model=ProductOut,
    response_model_by_alias=True,
    summary="Get a single product by ID",
)
async def get_product(product_id: str, db: DB) -> ProductOut:
    """Return a product by its string ID.

    Raises 404 if the product does not exist.
    """
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
    search: str | None = Query(None, description="Search by name or brand"),
    sort: SortParam = Query("popular"),
    has_discount: bool | None = Query(None, description="Filter to only discounted items"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
) -> ProductListOut:
    stmt = select(Product).where(Product.in_stock.is_(True))

    if category is not None:
        stmt = stmt.where(Product.category == category)
    if subcategory is not None:
        stmt = stmt.where(Product.subcategory == subcategory)
    if has_discount is True:
        stmt = stmt.where(Product.discount_percent > 0)
    if search is not None and search.strip():
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Product.name.ilike(pattern), Product.brand.ilike(pattern))
        )

    match sort:
        case "price_asc":
            stmt = stmt.order_by(Product.price.asc())
        case "price_desc":
            stmt = stmt.order_by(Product.price.desc())
        case "new":
            stmt = stmt.order_by(Product.created_at.desc())
        case _:  # "popular" — default
            stmt = stmt.order_by(Product.review_count.desc())

    # Total count for pagination metadata
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Paginate
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
