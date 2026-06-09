from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category", "category"),
        Index("ix_products_category_subcategory", "category", "subcategory"),
        Index("ix_products_in_stock", "in_stock"),
        Index("ix_products_review_count", "review_count"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    brand: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(50), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    price_original: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # JSON-encoded list of image URLs stored as TEXT
    images_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # JSON-encoded list of {label, available} dicts
    sizes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # JSON-encoded list of {label, hex} dicts
    colors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # ---------------------------------------------------------------------------
    # Convenience accessors — avoid leaking raw JSON outside the model layer
    # ---------------------------------------------------------------------------

    @property
    def images(self) -> list[str]:
        return json.loads(self.images_json)

    @images.setter
    def images(self, value: list[str]) -> None:
        self.images_json = json.dumps(value, ensure_ascii=False)

    @property
    def sizes(self) -> list[dict]:
        return json.loads(self.sizes_json)

    @sizes.setter
    def sizes(self, value: list[dict]) -> None:
        self.sizes_json = json.dumps(value, ensure_ascii=False)

    @property
    def colors(self) -> list[dict]:
        return json.loads(self.colors_json)

    @colors.setter
    def colors(self, value: list[dict]) -> None:
        self.colors_json = json.dumps(value, ensure_ascii=False)
