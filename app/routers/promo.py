from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.promo import PromoCode
from app.schemas.promo import PromoValidateRequest, PromoValidateResponse

router = APIRouter(prefix="/api/promo", tags=["promo"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/validate",
    response_model=PromoValidateResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="Validate a promo code",
)
async def validate_promo(body: PromoValidateRequest, db: DB) -> PromoValidateResponse:
    """Look up the promo code in the database and return the discount details.

    Always returns HTTP 200 — the ``valid`` field signals whether the code
    was accepted.  This avoids leaking timing differences between valid and
    invalid codes.
    """
    result = await db.execute(
        select(PromoCode).where(
            PromoCode.code == body.code.upper().strip(),
            PromoCode.is_active.is_(True),
        )
    )
    promo = result.scalar_one_or_none()

    if promo is None:
        return PromoValidateResponse(
            valid=False,
            message="Промокод не найден или недействителен",
        )

    return PromoValidateResponse(
        valid=True,
        discountAmount=promo.discount_amount,
        discountPercent=promo.discount_percent,
        message="Промокод применён",
    )
