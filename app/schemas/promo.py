from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PromoValidateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)


class PromoValidateResponse(BaseModel):
    """Response schema matching the frontend TypeScript contract exactly.

    The frontend reads ``discountAmount`` and ``discountPercent`` in camelCase.
    We use ``alias`` so the JSON output uses camelCase while the Python
    attribute name stays snake_case.
    """

    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    discount_amount: int | None = Field(None, alias="discountAmount")
    discount_percent: int | None = Field(None, alias="discountPercent")
    message: str | None = None
