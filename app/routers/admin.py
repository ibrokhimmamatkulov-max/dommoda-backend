"""Admin API: authentication + product CRUD.

All product-mutating endpoints require a valid admin JWT delivered as
``Authorization: Bearer <token>``.
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.admin import (
    AdminLoginRequest,
    AdminProductListOut,
    AdminTokenResponse,
    ProductCreate,
    ProductUpdate,
)
from app.schemas.product import ProductOut
from app.security import create_admin_access_token
from app.services.lamoda_sync import apply_availability, fetch_lamoda_availability

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Dependency aliases
DB = Annotated[AsyncSession, Depends(get_db)]
Admin = Annotated[str, Depends(get_current_admin)]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=AdminTokenResponse,
    summary="Admin login — returns a 24-hour JWT",
)
async def admin_login(body: AdminLoginRequest) -> AdminTokenResponse:
    """Verify admin credentials and return a signed JWT.

    Uses a constant-time string comparison to prevent timing attacks.
    """
    import hmac

    credentials_valid = hmac.compare_digest(
        body.login, settings.admin_login
    ) and hmac.compare_digest(body.password, settings.admin_password)

    if not credentials_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    return AdminTokenResponse(access_token=create_admin_access_token())


# ---------------------------------------------------------------------------
# Product CRUD
# ---------------------------------------------------------------------------


def _product_to_dict(product: Product) -> dict:
    """Serialize a Product ORM instance to a plain dict for admin responses."""
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "subcategory": product.subcategory,
        "sku": product.sku,
        "price": product.price,
        "price_original": product.price_original,
        "discount_percent": product.discount_percent,
        "images": product.images,
        "sizes": [s["label"] for s in product.sizes],
        "colors": product.colors,
        "rating": product.rating,
        "review_count": product.review_count,
        "description": product.description,
        "in_stock": product.in_stock,
        "created_at": product.created_at.isoformat(),
    }


@router.get(
    "/products/{product_id}",
    response_model=dict,
    summary="Get a single product — admin only",
)
async def admin_get_product(
    product_id: str,
    _admin: Admin,
    db: DB,
) -> dict:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product: Product | None = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return _product_to_dict(product)


@router.get(
    "/products",
    response_model=AdminProductListOut,
    summary="List all products (including inactive) — admin only",
)
async def admin_list_products(
    _admin: Admin,
    db: DB,
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    include_inactive: bool = Query(False, description="Include soft-deleted products"),
) -> AdminProductListOut:
    """Return a paginated list of all products.

    Raises:
        HTTPException 401: when the JWT is missing or invalid.
    """
    stmt = select(Product)
    if not include_inactive:
        stmt = stmt.where(Product.in_stock.isnot(None))  # all active records

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * limit
    stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return AdminProductListOut(
        products=[_product_to_dict(p) for p in products],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + len(products)) < total,
    )


@router.post(
    "/products",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product — admin only",
)
async def admin_create_product(
    body: ProductCreate,
    _admin: Admin,
    db: DB,
) -> dict:
    """Create a product from the supplied data.

    ``sizes`` and ``colors`` are accepted as plain strings and stored in the
    JSON columns using the same ``{label, available}`` / ``{label, hex}``
    shape the frontend expects. Pass structured dicts via the seed script for
    full control.

    Raises:
        HTTPException 401: when the JWT is missing or invalid.
    """
    discount_percent: int | None = None
    if body.price_original and body.price_original > body.price:
        discount_percent = round(
            (body.price_original - body.price) / body.price_original * 100
        )

    product = Product(
        id=str(uuid4()),
        name=body.name,
        brand=body.brand,
        category=body.category,
        subcategory=body.subcategory,
        sku=body.sku,
        price=body.price,
        price_original=body.price_original,
        discount_percent=discount_percent,
        description=body.description,
        in_stock=body.in_stock,
    )
    # Use the property setters so JSON serialisation is consistent
    product.images = body.images
    product.sizes = [{"label": s, "available": True} for s in body.sizes]
    product.colors = [{"label": c, "hex": "#000000"} for c in body.colors]

    db.add(product)
    await db.flush()  # populate server-side defaults (created_at)
    await db.refresh(product)
    return _product_to_dict(product)


@router.put(
    "/products/{product_id}",
    response_model=dict,
    summary="Update a product — admin only",
)
async def admin_update_product(
    product_id: str,
    body: ProductUpdate,
    _admin: Admin,
    db: DB,
) -> dict:
    """Apply a partial update to the product identified by ``product_id``.

    Only fields explicitly provided in the request body are changed.

    Raises:
        HTTPException 401: when the JWT is missing or invalid.
        HTTPException 404: when the product does not exist.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product: Product | None = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )

    update_data = body.model_dump(exclude_unset=True)

    # Handle JSON-encoded list fields via property setters
    if "sizes" in update_data:
        product.sizes = [{"label": s, "available": True} for s in update_data.pop("sizes")]
    if "colors" in update_data:
        product.colors = [{"label": c, "hex": "#000000"} for c in update_data.pop("colors")]
    if "images" in update_data:
        product.images = update_data.pop("images")

    # Recalculate discount if price fields are touched
    price = update_data.get("price", product.price)
    price_original = update_data.get("price_original", product.price_original)
    if price_original and price_original > price:
        update_data["discount_percent"] = round(
            (price_original - price) / price_original * 100
        )
    elif "price" in update_data or "price_original" in update_data:
        update_data["discount_percent"] = None

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return _product_to_dict(product)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Soft-delete a product (sets is_active=False) — admin only",
)
async def admin_delete_product(
    product_id: str,
    _admin: Admin,
    db: DB,
) -> None:
    """Soft-delete a product by setting ``in_stock = False``.

    The record is retained in the database. Returns 204 No Content.

    Raises:
        HTTPException 401: when the JWT is missing or invalid.
        HTTPException 404: when the product does not exist.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product: Product | None = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    product.in_stock = False
    await db.flush()


@router.delete(
    "/products",
    status_code=status.HTTP_200_OK,
    summary="Delete ALL products — admin only",
)
async def admin_delete_all_products(_admin: Admin, db: DB) -> dict:
    """Hard-delete every row from the products table."""
    from sqlalchemy import delete as sa_delete
    result = await db.execute(sa_delete(Product))
    await db.flush()
    return {"deleted": result.rowcount}


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.get("/orders", response_model=list[dict], summary="List all orders — admin only")
async def admin_list_orders(_admin: Admin, db: DB) -> list[dict]:
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "status": o.status.value,
            "recipient_name": o.recipient_name,
            "phone": o.phone,
            "email": o.email,
            "city": o.city,
            "delivery_method": o.delivery_method.value,
            "total": o.total,
            "items_count": len(o.items),
            "items": o.items,
            "promo_code": o.promo_code,
            "promo_discount": o.promo_discount,
            "subtotal": o.subtotal,
            "street": o.street,
            "building": o.building,
            "apartment": o.apartment,
            "comment": o.comment,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


@router.patch("/orders/{order_id}/status", response_model=dict, summary="Update order status — admin only")
async def admin_update_order_status(
    order_id: str,
    body: dict,
    _admin: Admin,
    db: DB,
) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order: Order | None = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    try:
        order.status = OrderStatus(body.get("status"))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    await db.flush()
    return {"id": order.id, "status": order.status.value}


# ---------------------------------------------------------------------------
# Size sync
# ---------------------------------------------------------------------------


@router.post(
    "/sync-sizes",
    response_model=dict,
    summary="Sync size availability for discounted products from Lamoda — admin only",
)
async def sync_sizes(_admin: Admin, db: DB) -> dict:
    """Fetch current size availability from lamoda.ru for all discounted products
    that have a SKU. Updates sizes_json in place. Safe to re-run."""
    result = await db.execute(
        select(Product)
        .where(Product.discount_percent > 0)
        .where(Product.sku.isnot(None))
        .where(Product.sku != "")
        .where(Product.in_stock.is_(True))
        .order_by(Product.created_at.desc())
    )
    products = result.scalars().all()

    if not products:
        return {"updated": 0, "skipped": 0, "errors": 0, "total": 0}

    updated = 0
    skipped = 0
    errors = 0
    error_skus: list[str] = []

    async with httpx.AsyncClient() as client:
        for product in products:
            try:
                availability = await fetch_lamoda_availability(product.sku, client)
                if availability is None:
                    skipped += 1
                else:
                    product.sizes = apply_availability(product.sizes, availability)
                    await db.flush()
                    updated += 1
            except Exception as exc:
                errors += 1
                error_skus.append(f"{product.sku}: {exc}")

            await asyncio.sleep(0.8)

    from app.telegram import send_telegram
    await send_telegram(
        f"🔄 *Dommoda — синк размеров завершён*\n\n"
        f"✅ Обновлено: {updated}\n"
        f"⏭ Пропущено: {skipped}\n"
        f"❌ Ошибок: {errors}\n"
        f"📦 Всего товаров: {len(products)}"
    )

    return {
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "total": len(products),
        "error_skus": error_skus[:10],
    }
