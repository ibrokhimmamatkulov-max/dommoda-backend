from __future__ import annotations

from pydantic import BaseModel


class SubcategoryOut(BaseModel):
    id: str
    label: str


class CategoryOut(BaseModel):
    id: str
    label: str
    icon: str
    subcategories: list[SubcategoryOut]

    @classmethod
    def from_orm_category(cls, category) -> "CategoryOut":
        return cls(
            id=category.id,
            label=category.label,
            icon=category.icon,
            subcategories=[SubcategoryOut(**s) for s in category.subcategories],
        )
