from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (Index("ix_categories_id", "id"),)

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    icon: Mapped[str] = mapped_column(String(100), nullable=False)
    # JSON-encoded list of {id, label} subcategory objects
    subcategories_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    @property
    def subcategories(self) -> list[dict]:
        return json.loads(self.subcategories_json)

    @subcategories.setter
    def subcategories(self, value: list[dict]) -> None:
        self.subcategories_json = json.dumps(value, ensure_ascii=False)
