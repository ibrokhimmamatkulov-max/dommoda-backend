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
    RECEIVED = "received"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_REQUESTED = "return_requested"
    RETURNED = "returned"


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
    recipient_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Delivery address
    city: Mapped[str | None] = mapped_column(String(200), nullable=True)
    street: Mapped[str | None] = mapped_column(String(300), nullable=True)
    building: Mapped[str | None] = mapped_column(String(50), nullable=True)
    apartment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
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
