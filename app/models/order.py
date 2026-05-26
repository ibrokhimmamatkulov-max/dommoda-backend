from __future__ import annotations

import enum
import json
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryMethod(str, enum.Enum):
    COURIER = "courier"
    PICKUP = "pickup"
    POST = "post"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING
    )
    delivery_method: Mapped[DeliveryMethod] = mapped_column(
        SAEnum(DeliveryMethod), nullable=False
    )

    # Contact info
    recipient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)

    # Delivery address
    city: Mapped[str] = mapped_column(String(200), nullable=False)
    street: Mapped[str] = mapped_column(String(300), nullable=False)
    building: Mapped[str] = mapped_column(String(50), nullable=False)
    apartment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pricing (stored in kopecks / smallest currency unit)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    promo_discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    promo_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False)

    # JSON-encoded list of order line items
    items_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @property
    def items(self) -> list[dict]:
        return json.loads(self.items_json)

    @items.setter
    def items(self, value: list[dict]) -> None:
        self.items_json = json.dumps(value, ensure_ascii=False)
