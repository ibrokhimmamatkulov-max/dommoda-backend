from __future__ import annotations
import json
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.setting import SiteSetting

router = APIRouter(prefix="/api/settings", tags=["settings"])

DB = Annotated[AsyncSession, Depends(get_db)]
Admin = Annotated[str, Depends(get_current_admin)]

DEFAULT_BANNER = {
    "imageUrl": "https://placehold.co/600x600/000000/ffffff?text=DOMMODA",
    "badgeText": "-70%",
    "headline": "НОВАЯ КОЛЛЕКЦИЯ",
    "ctaText": "Смотреть",
    "ctaUrl": "/catalog/women",
}


class BannerUpdate(BaseModel):
    imageUrl: str
    badgeText: str
    headline: str
    ctaText: str
    ctaUrl: str


@router.get("/banner")
async def get_banner(db: DB) -> dict:
    row = await db.get(SiteSetting, "banner")
    if row is None:
        return DEFAULT_BANNER
    return json.loads(row.value)


@router.put("/banner")
async def update_banner(_admin: Admin, db: DB, body: BannerUpdate) -> dict:
    row = await db.get(SiteSetting, "banner")
    data = body.model_dump()
    if row is None:
        db.add(SiteSetting(key="banner", value=json.dumps(data)))
    else:
        row.value = json.dumps(data)
    await db.flush()
    return data
