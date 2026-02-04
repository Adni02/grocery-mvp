"""API routes package."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.addresses import router as addresses_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.admin import router as admin_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products_router, prefix="/products", tags=["Products"])
api_router.include_router(addresses_router, prefix="/addresses", tags=["Addresses"])
api_router.include_router(cart_router, prefix="/cart", tags=["Cart"])
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
