from __future__ import annotations
import json
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.analytics import AnalyticsEvent
from app.telegram import send_telegram

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

DB = Annotated[AsyncSession, Depends(get_db)]

EMOJI = {
    "visit": "👁",
    "product_view": "🛍",
    "add_to_cart": "🛒",
    "checkout_start": "💳",
}

LABEL = {
    "visit": "Новый посетитель",
    "product_view": "Смотрит товар",
    "add_to_cart": "Добавил в корзину",
    "checkout_start": "Начал оформление",
}


class TrackRequest(BaseModel):
    event_type: str
    session_id: str
    page: str | None = None
    data: dict | None = None


@router.post("")
async def track_event(body: TrackRequest, db: DB) -> dict:
    allowed = {"visit", "product_view", "add_to_cart", "checkout_start"}
    if body.event_type not in allowed:
        return {"ok": False}

    # Для "visit" — проверяем не было ли уже события от этой сессии
    if body.event_type == "visit":
        existing = await db.execute(
            select(AnalyticsEvent).where(
                AnalyticsEvent.session_id == body.session_id,
                AnalyticsEvent.event_type == "visit",
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            return {"ok": True, "skipped": True}

    event = AnalyticsEvent(
        event_type=body.event_type,
        session_id=body.session_id,
        page=body.page,
        data=json.dumps(body.data, ensure_ascii=False) if body.data else None,
    )
    db.add(event)
    await db.flush()

    # Считаем сессии за сегодня для контекста
    total_sessions = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
            AnalyticsEvent.event_type == "visit"
        )
    )
    sessions_count = total_sessions.scalar_one()

    emoji = EMOJI.get(body.event_type, "📊")
    label = LABEL.get(body.event_type, body.event_type)

    lines = [f"{emoji} *{label}*"]

    if body.data:
        if "product_name" in body.data:
            lines.append(f"👕 {body.data['product_name']}")
        if "brand" in body.data:
            lines.append(f"🏷 {body.data['brand']}")
        if "cart_total" in body.data:
            lines.append(f"💰 Корзина: {body.data['cart_total']:,} ₽")

    if body.page:
        lines.append(f"📄 {body.page}")

    if body.event_type == "visit":
        lines.append(f"👥 Посетитель #{sessions_count} за всё время")

    msg = "\n".join(lines)
    await send_telegram(msg)

    return {"ok": True}
