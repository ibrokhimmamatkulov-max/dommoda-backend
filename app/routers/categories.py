from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "",
    response_model=list[CategoryOut],
    summary="List all product categories with their subcategories",
)
async def list_categories(db: DB) -> list[CategoryOut]:
    """Return all top-level categories ordered by their natural seed order."""
    result = await db.execute(select(Category).order_by(Category.created_at.asc()))
    categories = result.scalars().all()
    return [CategoryOut.from_orm_category(c) for c in categories]
