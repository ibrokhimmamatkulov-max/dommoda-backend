from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class CartItemIn(BaseModel):
    product_id: str
    size: str
    color: str
    quantity: int = Field(..., ge=1, le=10)


class CartValidateRequest(BaseModel):
    items: list[CartItemIn] = Field(..., min_length=1)


class CartItemValidationResult(BaseModel):
    product_id: str
    size: str
    color: str
    quantity: int
    valid: bool
    reason: str | None = None


class CartValidateResponse(BaseModel):
    all_valid: bool
    items: list[CartItemValidationResult]


class OrderItemIn(BaseModel):
    product_id: str
    product_name: str
    brand: str
    size: str
    color: str
    quantity: int = Field(..., ge=1, le=10)
    unit_price: int = Field(..., ge=0)


class CreateOrderRequest(BaseModel):
    delivery_method: str = Field(..., pattern="^(courier|pickup|post)$")
    city: str = Field(..., min_length=1, max_length=200)
    street: str | None = Field(None, max_length=300)
    building: str | None = Field(None, max_length=50)
    apartment: str | None = Field(None, max_length=50)
    zip_code: str | None = Field(None, max_length=20)
    recipient_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., min_length=7, max_length=30)
    email: EmailStr | None = None
    comment: str | None = Field(None, max_length=1000)
    items: list[OrderItemIn] = Field(..., min_length=1)
    promo_code: str | None = Field(None, max_length=50)
    promo_discount: int = Field(0, ge=0)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 7:
            raise ValueError("Phone number must contain at least 7 digits")
        return v


class OrderItemOut(BaseModel):
    product_id: str
    product_name: str
    brand: str
    size: str
    color: str
    quantity: int
    unit_price: int


class OrderOut(BaseModel):
    id: str
    status: str
    delivery_method: str
    recipient_name: str
    phone: str
    email: str
    city: str
    street: str
    building: str
    apartment: str | None
    zip_code: str
    comment: str | None
    subtotal: int
    promo_discount: int
    promo_code: str | None
    total: int
    items: list[OrderItemOut]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_order(cls, order) -> "OrderOut":
        return cls(
            id=order.id,
            status=order.status,
            delivery_method=order.delivery_method,
            recipient_name=order.recipient_name,
            phone=order.phone,
            email=order.email,
            city=order.city,
            street=order.street,
            building=order.building,
            apartment=order.apartment,
            zip_code=order.zip_code,
            comment=order.comment,
            subtotal=order.subtotal,
            promo_discount=order.promo_discount,
            promo_code=order.promo_code,
            total=order.total,
            items=[OrderItemOut(**item) for item in order.items],
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
