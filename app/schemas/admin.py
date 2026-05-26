"""Pydantic schemas for admin authentication and product management."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class AdminLoginRequest(BaseModel):
    login: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Product admin schemas
# ---------------------------------------------------------------------------


class ProductCreate(BaseModel):
    """Schema for creating or fully replacing a product via the admin API."""

    name: str = Field(..., min_length=1, max_length=500)
    brand: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., description="women / men / kids / sport")
    subcategory: str
    price: int = Field(..., gt=0)
    price_original: int | None = None
    description: str = ""
    sizes: list[str] = []
    colors: list[str] = []
    images: list[str] = []
    in_stock: bool = True


class ProductUpdate(BaseModel):
    """Schema for partially updating a product via the admin API.

    All fields are optional — only provided fields are applied.
    """

    name: str | None = Field(None, min_length=1, max_length=500)
    brand: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = None
    subcategory: str | None = None
    price: int | None = Field(None, gt=0)
    price_original: int | None = None
    description: str | None = None
    sizes: list[str] | None = None
    colors: list[str] | None = None
    images: list[str] | None = None
    in_stock: bool | None = None


class AdminProductListOut(BaseModel):
    """Paginated response for the admin product list."""

    products: list[dict]
    total: int
    page: int
    limit: int
    has_more: bool
