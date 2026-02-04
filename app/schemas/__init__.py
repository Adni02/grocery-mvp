"""Pydantic schemas package."""

from app.schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    PostcodeVerifyRequest,
    PostcodeVerifyResponse,
    ServiceAddressResponse,
)
from app.schemas.auth import AuthVerifyRequest, AuthVerifyResponse, UserResponse
from app.schemas.cart import (
    CartItemAdd,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
    CartSyncRequest,
)
from app.schemas.order import (
    OrderCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.schemas.product import (
    CategoryResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

__all__ = [
    # Auth
    "AuthVerifyRequest",
    "AuthVerifyResponse",
    "UserResponse",
    # Product
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
    "CategoryResponse",
    # Address
    "PostcodeVerifyRequest",
    "PostcodeVerifyResponse",
    "ServiceAddressResponse",
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    # Cart
    "CartItemAdd",
    "CartItemUpdate",
    "CartItemResponse",
    "CartResponse",
    "CartSyncRequest",
    # Order
    "OrderCreate",
    "OrderResponse",
    "OrderListResponse",
    "OrderItemResponse",
    "OrderStatusUpdate",
]
