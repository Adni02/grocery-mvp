"""Cart schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    """Add item to cart."""

    product_id: UUID
    quantity: int = Field(..., gt=0, le=99)


class CartItemUpdate(BaseModel):
    """Update cart item quantity."""

    quantity: int = Field(..., gt=0, le=99)


class CartItemResponse(BaseModel):
    """Cart item response."""

    product_id: UUID
    name: str
    slug: str
    price: Decimal
    unit: str
    image_url: Optional[str] = None
    quantity: int
    line_total: Decimal

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """Full cart response."""

    items: list[CartItemResponse]
    subtotal: Decimal
    item_count: int


class CartSyncRequest(BaseModel):
    """Sync guest cart to user cart on login."""

    items: list[CartItemAdd]
