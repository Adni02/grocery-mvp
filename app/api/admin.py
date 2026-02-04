"""Admin API routes (secured by API key for Retool access)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import AdminApiKey, DbSession
from app.models.order import OrderStatus
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.address_service import AddressService
from app.services.order_service import OrderService
from app.services.product_service import ProductService

router = APIRouter()


# ============================================================================
# Product Management
# ============================================================================


@router.get("/products", response_model=list[ProductResponse])
async def admin_list_products(
    db: DbSession,
    _: AdminApiKey,
    include_inactive: bool = False,
):
    """
    List all products (including inactive ones for admin).
    """
    product_service = ProductService(db)
    products, _ = await product_service.list_products(
        page=1,
        limit=1000,
        is_active=not include_inactive,
    )
    return [ProductResponse.model_validate(p) for p in products]


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_product(
    data: ProductCreate,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Create a new product.
    """
    product_service = ProductService(db)

    try:
        product = await product_service.create_product(data)
        return ProductResponse.model_validate(product)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def admin_update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Update a product.
    """
    product_service = ProductService(db)
    product = await product_service.update_product(product_id, data)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse.model_validate(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(
    product_id: UUID,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Soft-delete a product (sets is_active=False).
    """
    product_service = ProductService(db)
    deleted = await product_service.delete_product(product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


# ============================================================================
# Order Management
# ============================================================================


@router.get("/orders")
async def admin_list_orders(
    db: DbSession,
    _: AdminApiKey,
    page: int = 1,
    limit: int = 50,
    status: Optional[OrderStatus] = None,
):
    """
    List all orders with optional status filter.
    """
    order_service = OrderService(db)
    orders, total = await order_service.list_orders_admin(
        page=page,
        limit=limit,
        status=status,
    )

    return {
        "items": [
            {
                "id": str(order.id),
                "invoice_number": order.invoice_number,
                "status": order.status.value,
                "total": float(order.total),
                "customer_email": order.user.email if order.user else None,
                "customer_phone": order.user.phone if order.user else None,
                "address_snapshot": order.address_snapshot,
                "item_count": sum(item.quantity for item in order.items),
                "created_at": order.created_at.isoformat(),
            }
            for order in orders
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def admin_get_order(
    order_id: UUID,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Get order details by ID.
    """
    order_service = OrderService(db)
    order = await order_service.get_order_admin(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return OrderResponse.model_validate(order)


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Update order status.

    Valid transitions:
    - PLACED → CONFIRMED, CANCELED
    - CONFIRMED → PACKING, CANCELED
    - PACKING → OUT_FOR_DELIVERY, CANCELED
    - OUT_FOR_DELIVERY → DELIVERED, CANCELED
    - DELIVERED, CANCELED → (no further transitions)
    """
    order_service = OrderService(db)

    try:
        order = await order_service.update_order_status(
            order_id=order_id,
            new_status=data.status,
            notes=data.notes,
        )
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Postcode Management
# ============================================================================


@router.get("/postcodes")
async def admin_list_postcodes(
    db: DbSession,
    _: AdminApiKey,
):
    """
    List all service postcodes.
    """
    address_service = AddressService(db)
    postcodes = await address_service.list_service_postcodes()

    return [
        {
            "id": p.id,
            "postcode": p.postcode,
            "city_name": p.city_name,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat(),
        }
        for p in postcodes
    ]


@router.post("/postcodes", status_code=status.HTTP_201_CREATED)
async def admin_add_postcode(
    postcode: str,
    city_name: str,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Add a new service postcode.
    """
    address_service = AddressService(db)

    try:
        service_postcode = await address_service.add_service_postcode(postcode, city_name)
        return {
            "id": service_postcode.id,
            "postcode": service_postcode.postcode,
            "city_name": service_postcode.city_name,
            "is_active": service_postcode.is_active,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/postcodes/{postcode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_remove_postcode(
    postcode_id: int,
    db: DbSession,
    _: AdminApiKey,
):
    """
    Remove a service postcode.
    """
    address_service = AddressService(db)
    removed = await address_service.remove_service_postcode(postcode_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Postcode not found",
        )
