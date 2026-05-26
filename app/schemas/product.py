from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProductSize(BaseModel):
    label: str
    available: bool


class ProductColor(BaseModel):
    label: str
    hex: str


class ProductOut(BaseModel):
    """Serialised representation of a single product, matching the frontend
    ``Product`` TypeScript interface exactly.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    brand: str
    name: str
    category: str
    subcategory: str
    price: int
    price_original: int | None = Field(None, alias="priceOriginal")
    discount_percent: int | None = Field(None, alias="discountPercent")
    images: list[str]
    sizes: list[ProductSize]
    colors: list[ProductColor]
    rating: float
    review_count: int = Field(..., alias="reviewCount")
    description: str | None = None
    in_stock: bool = Field(..., alias="inStock")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @classmethod
    def from_orm_product(cls, product) -> "ProductOut":
        """Build the response schema from a Product ORM instance."""
        return cls(
            id=product.id,
            brand=product.brand,
            name=product.name,
            category=product.category,
            subcategory=product.subcategory,
            price=product.price,
            priceOriginal=product.price_original,
            discountPercent=product.discount_percent,
            images=product.images,
            sizes=[ProductSize(**s) for s in product.sizes],
            colors=[ProductColor(**c) for c in product.colors],
            rating=product.rating,
            reviewCount=product.review_count,
            description=product.description,
            inStock=product.in_stock,
        )


class ProductListOut(BaseModel):
    """Paginated product list response."""

    products: list[ProductOut]
    total: int
    page: int
    limit: int
    has_more: bool
