from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import DeliveryMethod, Order, OrderStatus
from app.schemas.order import CreateOrderRequest, OrderItemOut, OrderOut

router = APIRouter(prefix="/api/orders", tags=["orders"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
)
async def create_order(body: CreateOrderRequest, db: DB) -> OrderOut:
    """Persist a new order and return the full order record.

    The client is responsible for supplying pre-validated prices (the backend
    does not re-fetch product prices here — cart validation happens at
    ``POST /api/cart/validate`` before this call).

    Raises 422 if input validation fails.
    """
    subtotal = sum(item.unit_price * item.quantity for item in body.items)
    promo_discount = min(body.promo_discount, subtotal)  # cannot discount more than cart
    total = max(subtotal - promo_discount, 0)

    order = Order(
        id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        status=OrderStatus.CONFIRMED,
        delivery_method=DeliveryMethod(body.delivery_method),
        recipient_name=body.recipient_name,
        phone=body.phone,
        email=body.email,
        city=body.city,
        street=body.street,
        building=body.building,
        apartment=body.apartment,
        zip_code=body.zip_code,
        comment=body.comment,
        subtotal=subtotal,
        promo_discount=promo_discount,
        promo_code=body.promo_code,
        total=total,
    )
    order.items = [item.model_dump() for item in body.items]

    db.add(order)
    await db.flush()
    await db.refresh(order)

    from app.telegram import send_order_notification
    await send_order_notification(order)

    return OrderOut.from_orm_order(order)


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    summary="Get order status and details by ID",
)
async def get_order(order_id: str, db: DB) -> OrderOut:
    """Return an order by its string ID.

    Raises 404 if the order does not exist.

    Note: there is intentionally no auth check here because the order ID
    itself (an 8-character random hex) acts as an unguessable token for the
    order-confirmation page — the same pattern used by most e-commerce sites.
    For a production system with user accounts, filter by user_id as well.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )
    return OrderOut.from_orm_order(order)
