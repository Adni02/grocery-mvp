"""Cart service for shopping cart operations."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemAdd, CartResponse, CartItemResponse


class CartService:
    """Service for shopping cart operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        """Get existing cart or create a new one for the user."""
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.flush()
            await self.db.refresh(cart)

        return cart

    async def get_cart(self, user_id: UUID) -> Optional[Cart]:
        """Get cart for a user."""
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_cart_response(self, user_id: UUID) -> CartResponse:
        """Get cart formatted as response."""
        cart = await self.get_or_create_cart(user_id)
        return self._cart_to_response(cart)

    async def add_item(self, user_id: UUID, data: CartItemAdd) -> CartResponse:
        """Add an item to the cart or update quantity if exists."""
        cart = await self.get_or_create_cart(user_id)

        # Check if product exists and is active
        product = await self._get_active_product(data.product_id)
        if not product:
            raise ValueError("Product not found or unavailable")

        # Check if item already in cart
        existing_item = next(
            (item for item in cart.items if item.product_id == data.product_id),
            None,
        )

        if existing_item:
            existing_item.quantity += data.quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=data.product_id,
                quantity=data.quantity,
            )
            self.db.add(cart_item)
            cart.items.append(cart_item)

        await self.db.flush()
        await self.db.refresh(cart)
        return self._cart_to_response(cart)

    async def update_item(
        self, user_id: UUID, product_id: UUID, quantity: int
    ) -> CartResponse:
        """Update item quantity in cart."""
        cart = await self.get_or_create_cart(user_id)

        item = next(
            (item for item in cart.items if item.product_id == product_id),
            None,
        )

        if not item:
            raise ValueError("Item not found in cart")

        if quantity <= 0:
            await self.db.delete(item)
            cart.items.remove(item)
        else:
            item.quantity = quantity

        await self.db.flush()
        await self.db.refresh(cart)
        return self._cart_to_response(cart)

    async def remove_item(self, user_id: UUID, product_id: UUID) -> CartResponse:
        """Remove an item from the cart."""
        cart = await self.get_or_create_cart(user_id)

        item = next(
            (item for item in cart.items if item.product_id == product_id),
            None,
        )

        if item:
            await self.db.delete(item)
            cart.items.remove(item)
            await self.db.flush()

        await self.db.refresh(cart)
        return self._cart_to_response(cart)

    async def clear_cart(self, user_id: UUID) -> CartResponse:
        """Remove all items from the cart."""
        cart = await self.get_cart(user_id)
        if cart:
            stmt = delete(CartItem).where(CartItem.cart_id == cart.id)
            await self.db.execute(stmt)
            cart.items = []
            await self.db.flush()
            await self.db.refresh(cart)

        return CartResponse(items=[], subtotal=Decimal("0.00"), item_count=0)

    async def sync_guest_cart(
        self, user_id: UUID, items: list[CartItemAdd]
    ) -> CartResponse:
        """Sync guest cart items to user cart on login."""
        cart = await self.get_or_create_cart(user_id)

        for item_data in items:
            # Check if product exists and is active
            product = await self._get_active_product(item_data.product_id)
            if not product:
                continue

            # Check if item already in cart
            existing_item = next(
                (item for item in cart.items if item.product_id == item_data.product_id),
                None,
            )

            if existing_item:
                # Keep the higher quantity
                existing_item.quantity = max(existing_item.quantity, item_data.quantity)
            else:
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                )
                self.db.add(cart_item)
                cart.items.append(cart_item)

        await self.db.flush()
        await self.db.refresh(cart)
        return self._cart_to_response(cart)

    async def _get_active_product(self, product_id: UUID) -> Optional[Product]:
        """Get an active product by ID."""
        stmt = select(Product).where(
            Product.id == product_id,
            Product.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _cart_to_response(self, cart: Cart) -> CartResponse:
        """Convert cart model to response schema."""
        items = []
        subtotal = Decimal("0.00")
        item_count = 0

        for cart_item in cart.items:
            if cart_item.product:
                line_total = cart_item.product.price * cart_item.quantity
                items.append(
                    CartItemResponse(
                        product_id=cart_item.product_id,
                        name=cart_item.product.name,
                        slug=cart_item.product.slug,
                        price=cart_item.product.price,
                        unit=cart_item.product.unit,
                        image_url=cart_item.product.image_url,
                        quantity=cart_item.quantity,
                        line_total=line_total,
                    )
                )
                subtotal += line_total
                item_count += cart_item.quantity

        return CartResponse(items=items, subtotal=subtotal, item_count=item_count)
