"""Cart API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse, CartSyncRequest
from app.services.cart_service import CartService

router = APIRouter()


@router.get("", response_model=CartResponse)
async def get_cart(
    db: DbSession,
    user: CurrentUser,
):
    """
    Get the current user's shopping cart.
    """
    cart_service = CartService(db)
    return await cart_service.get_cart_response(user.id)


@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    data: CartItemAdd,
    db: DbSession,
    user: CurrentUser,
):
    """
    Add an item to the cart.

    If the item already exists, the quantity is added to the existing quantity.
    """
    cart_service = CartService(db)

    try:
        return await cart_service.add_item(user.id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: UUID,
    data: CartItemUpdate,
    db: DbSession,
    user: CurrentUser,
):
    """
    Update the quantity of an item in the cart.

    Set quantity to 0 to remove the item.
    """
    cart_service = CartService(db)

    try:
        return await cart_service.update_item(user.id, product_id, data.quantity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    product_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """
    Remove an item from the cart.
    """
    cart_service = CartService(db)
    return await cart_service.remove_item(user.id, product_id)


@router.post("/sync", response_model=CartResponse)
async def sync_guest_cart(
    data: CartSyncRequest,
    db: DbSession,
    user: CurrentUser,
):
    """
    Sync guest cart items to the user's cart.

    Called after login to merge the guest cart with the user's existing cart.
    For duplicate products, the higher quantity is kept.
    """
    cart_service = CartService(db)
    return await cart_service.sync_guest_cart(user.id, data.items)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    db: DbSession,
    user: CurrentUser,
):
    """
    Clear all items from the cart.
    """
    cart_service = CartService(db)
    return await cart_service.clear_cart(user.id)
