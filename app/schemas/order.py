"""Order schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    """Create order request."""

    address_id: UUID
    notes: Optional[str] = Field(None, max_length=500)


class OrderItemResponse(BaseModel):
    """Order item response."""

    id: UUID
    product_id: UUID
    product_snapshot: dict[str, Any]
    quantity: int
    price_at_purchase: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class OrderStatusHistoryResponse(BaseModel):
    """Order status history entry."""

    status: OrderStatus
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """Full order response."""

    id: UUID
    invoice_number: Optional[str] = None
    status: OrderStatus
    address_snapshot: dict[str, Any]
    items: list[OrderItemResponse]
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    notes: Optional[str] = None
    status_history: list[OrderStatusHistoryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    """Order list item (summary)."""

    id: UUID
    invoice_number: Optional[str] = None
    status: OrderStatus
    total: Decimal
    item_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Paginated order list response."""

    items: list[OrderListItem]
    total: int
    page: int
    limit: int


class OrderStatusUpdate(BaseModel):
    """Update order status request."""

    status: OrderStatus
    notes: Optional[str] = Field(None, max_length=500)
