from __future__ import annotations

import uuid
from typing import Annotated

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.order import DeliveryMethod, Order, OrderStatus
from app.models.product import Product
from app.schemas.order import CreateOrderRequest, OrderItemOut, OrderOut
from app.telegram import send_telegram

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
        status=OrderStatus.RECEIVED,
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
    # Fetch SKU for each product so it appears in the Telegram notification
    product_ids = [item.product_id for item in body.items]
    sku_map: dict[str, str | None] = {}
    if product_ids:
        result_skus = await db.execute(
            select(Product.id, Product.sku).where(Product.id.in_(product_ids))
        )
        sku_map = {row.id: row.sku for row in result_skus}

    items_data = []
    for item in body.items:
        d = item.model_dump()
        d["sku"] = sku_map.get(item.product_id)
        items_data.append(d)
    order.items = items_data

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


@router.post("/{order_id}/return", summary="Customer requests a return")
async def request_return(order_id: str, db: DB) -> dict:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order: Order | None = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Возврат возможен только для доставленных заказов",
        )
    order.status = OrderStatus.RETURN_REQUESTED
    await db.flush()
    await send_telegram(
        f"↩️ *Запрос на возврат*\n\n"
        f"📦 Заказ: {order.id}\n"
        f"📞 Телефон: {order.phone}\n"
        f"💰 Сумма: {order.total:,} ₽\n\n"
        f"Зайди в админку и обработай возврат\."
    )
    return {"ok": True, "status": "return_requested"}
