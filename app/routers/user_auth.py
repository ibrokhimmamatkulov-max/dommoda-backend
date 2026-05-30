from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.security import create_user_access_token, decode_user_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
DB = Annotated[AsyncSession, Depends(get_db)]


class PhoneLoginRequest(BaseModel):
    phone: str
    name: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    phone: str
    name: str | None


@router.post("/login", response_model=AuthResponse)
async def phone_login(body: PhoneLoginRequest, db: DB) -> AuthResponse:
    phone = body.phone.strip()
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(id=str(uuid.uuid4()), phone=phone, name=body.name)
        db.add(user)
        await db.flush()

    elif body.name and not user.name:
        user.name = body.name
        await db.flush()

    token = create_user_access_token(phone)
    return AuthResponse(access_token=token, phone=user.phone, name=user.name)


@router.get("/me")
async def get_me(db: DB, authorization: str = Header(default="")) -> dict:
    try:
        phone = decode_user_token(authorization.replace("Bearer ", ""))
    except Exception:
        return {"authenticated": False}

    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "phone": user.phone, "name": user.name}


@router.get("/orders")
async def get_my_orders(db: DB, authorization: str = Header(default="")) -> list[dict]:
    try:
        phone = decode_user_token(authorization.replace("Bearer ", ""))
    except Exception:
        return []

    result = await db.execute(
        select(Order).where(Order.phone == phone).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "status": o.status.value,
            "total": o.total,
            "items_count": len(o.items),
            "items": o.items,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]
