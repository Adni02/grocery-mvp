"""Product schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    """Category response schema."""

    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    sort_order: int
    is_active: bool
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CategoryWithChildren(CategoryResponse):
    """Category with nested children."""

    children: list["CategoryWithChildren"] = []


class ProductBase(BaseModel):
    """Base product schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    unit: str = Field(..., min_length=1, max_length=20)
    unit_quantity: Decimal = Field(default=Decimal("1.000"), gt=0)
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_active: bool = True
    is_featured: bool = False


class ProductCreate(ProductBase):
    """Create product schema."""

    sku: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=255)


class ProductUpdate(BaseModel):
    """Update product schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    unit_quantity: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class ProductResponse(BaseModel):
    """Product response schema."""

    id: UUID
    sku: str
    name: str
    slug: str
    description: Optional[str] = None
    price: Decimal
    unit: str
    unit_quantity: Decimal
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Paginated product list response."""

    items: list[ProductResponse]
    total: int
    page: int
    limit: int
    pages: int
