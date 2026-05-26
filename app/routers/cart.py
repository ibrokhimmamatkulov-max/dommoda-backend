from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.schemas.order import (
    CartItemValidationResult,
    CartValidateRequest,
    CartValidateResponse,
)

router = APIRouter(prefix="/api/cart", tags=["cart"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/validate",
    response_model=CartValidateResponse,
    summary="Validate cart items before checkout",
)
async def validate_cart(body: CartValidateRequest, db: DB) -> CartValidateResponse:
    """Check each cart item for availability before the customer proceeds to checkout.

    Returns a per-item validation result. ``all_valid`` is True only when every
    item passes.  Individual failure reasons use the same message keys the
    frontend expects.
    """
    product_ids = [item.product_id for item in body.items]

    result = await db.execute(
        select(Product).where(Product.id.in_(product_ids))
    )
    products_by_id: dict[str, Product] = {p.id: p for p in result.scalars().all()}

    validation_results: list[CartItemValidationResult] = []

    for item in body.items:
        product = products_by_id.get(item.product_id)

        if product is None:
            validation_results.append(
                CartItemValidationResult(
                    product_id=item.product_id,
                    size=item.size,
                    color=item.color,
                    quantity=item.quantity,
                    valid=False,
                    reason="Товар не найден",
                )
            )
            continue

        if not product.in_stock:
            validation_results.append(
                CartItemValidationResult(
                    product_id=item.product_id,
                    size=item.size,
                    color=item.color,
                    quantity=item.quantity,
                    valid=False,
                    reason="Товар нет в наличии",
                )
            )
            continue

        # Check that the requested size is marked available in the product data
        size_available = any(
            s["label"] == item.size and s["available"]
            for s in product.sizes
        )
        if not size_available:
            validation_results.append(
                CartItemValidationResult(
                    product_id=item.product_id,
                    size=item.size,
                    color=item.color,
                    quantity=item.quantity,
                    valid=False,
                    reason=f"Размер {item.size} недоступен",
                )
            )
            continue

        validation_results.append(
            CartItemValidationResult(
                product_id=item.product_id,
                size=item.size,
                color=item.color,
                quantity=item.quantity,
                valid=True,
            )
        )

    all_valid = all(r.valid for r in validation_results)
    return CartValidateResponse(all_valid=all_valid, items=validation_results)
