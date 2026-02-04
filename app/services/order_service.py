"""Order service for order management and checkout."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.order import Invoice, Order, OrderItem, OrderStatus, OrderStatusHistory
from app.services.address_service import AddressService
from app.services.cart_service import CartService
from app.schemas.order import OrderCreate


class OrderService:
    """Service for order operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.address_service = AddressService(db)
        self.cart_service = CartService(db)

    async def create_order(self, user_id: UUID, data: OrderCreate) -> Order:
        """Create a new order from the user's cart."""
        # 1. Verify address exists, belongs to user, and is verified
        address = await self.address_service.get_verified_address(data.address_id, user_id)
        if not address:
            raise ValueError("Please select a verified delivery address")

        # 2. Get user's cart
        cart = await self.cart_service.get_cart(user_id)
        if not cart or not cart.items:
            raise ValueError("Your cart is empty")

        # 3. Create address snapshot
        address_snapshot = address.to_snapshot()

        # 4. Calculate totals and create order items (with current prices from DB)
        subtotal = Decimal("0.00")
        order_items_data = []

        for cart_item in cart.items:
            if not cart_item.product or not cart_item.product.is_active:
                continue

            # Use current price from product (server-validated)
            price_at_purchase = cart_item.product.price
            line_total = price_at_purchase * cart_item.quantity
            subtotal += line_total

            product_snapshot = {
                "name": cart_item.product.name,
                "sku": cart_item.product.sku,
                "unit": cart_item.product.unit,
                "image_url": cart_item.product.image_url,
            }

            order_items_data.append({
                "product_id": cart_item.product_id,
                "product_snapshot": product_snapshot,
                "quantity": cart_item.quantity,
                "price_at_purchase": price_at_purchase,
                "line_total": line_total,
            })

        if not order_items_data:
            raise ValueError("No valid items in cart")

        # 5. Calculate delivery fee and total
        delivery_fee = Decimal(str(settings.delivery_fee))
        total = subtotal + delivery_fee

        # 6. Generate invoice number
        invoice_number = await self._generate_invoice_number()

        # 7. Create order
        order = Order(
            user_id=user_id,
            address_id=address.id,
            address_snapshot=address_snapshot,
            status=OrderStatus.PLACED,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            invoice_number=invoice_number,
            invoice_generated_at=datetime.now(timezone.utc),
            notes=data.notes,
        )
        self.db.add(order)
        await self.db.flush()

        # 8. Create order items
        for item_data in order_items_data:
            order_item = OrderItem(order_id=order.id, **item_data)
            self.db.add(order_item)

        # 9. Create initial status history entry
        status_history = OrderStatusHistory(
            order_id=order.id,
            status=OrderStatus.PLACED,
            notes="Order placed by customer",
        )
        self.db.add(status_history)

        # 10. Create invoice record
        invoice = Invoice(
            order_id=order.id,
            invoice_number=invoice_number,
        )
        self.db.add(invoice)

        # 11. Clear the cart
        await self.cart_service.clear_cart(user_id)

        await self.db.flush()
        await self.db.refresh(order)

        return order

    async def get_order(self, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Get a specific order by ID, ensuring it belongs to the user."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
            )
            .where(Order.id == order_id, Order.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_admin(self, order_id: UUID) -> Optional[Order]:
        """Get a specific order by ID (admin access)."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
                selectinload(Order.user),
            )
            .where(Order.id == order_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_orders(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Order], int]:
        """List orders for a user with pagination."""
        # Base query
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )

        # Count total
        count_stmt = select(func.count()).select_from(
            select(Order.id).where(Order.user_id == user_id).subquery()
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        return orders, total

    async def list_orders_admin(
        self,
        page: int = 1,
        limit: int = 50,
        status: Optional[OrderStatus] = None,
    ) -> tuple[list[Order], int]:
        """List all orders (admin access)."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.user),
            )
            .order_by(Order.created_at.desc())
        )

        if status:
            stmt = stmt.where(Order.status == status)

        # Count
        count_subq = select(Order.id)
        if status:
            count_subq = count_subq.where(Order.status == status)
        count_stmt = select(func.count()).select_from(count_subq.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        return orders, total

    async def update_order_status(
        self,
        order_id: UUID,
        new_status: OrderStatus,
        notes: Optional[str] = None,
        changed_by: Optional[UUID] = None,
    ) -> Order:
        """Update order status with validation."""
        order = await self.get_order_admin(order_id)
        if not order:
            raise ValueError("Order not found")

        # Validate transition
        current_status = order.status
        if not current_status.can_transition_to(new_status):
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )

        # Update status
        order.status = new_status

        # Add history entry
        history = OrderStatusHistory(
            order_id=order_id,
            status=new_status,
            changed_by=changed_by,
            notes=notes,
        )
        self.db.add(history)

        await self.db.flush()
        await self.db.refresh(order)

        return order

    async def _generate_invoice_number(self) -> str:
        """Generate a unique sequential invoice number."""
        year = datetime.now(timezone.utc).year

        # Get the latest invoice number for this year
        stmt = (
            select(Invoice.invoice_number)
            .where(Invoice.invoice_number.like(f"INV-{year}-%"))
            .order_by(Invoice.id.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_invoice = result.scalar_one_or_none()

        if last_invoice:
            # Extract sequence number and increment
            try:
                last_seq = int(last_invoice.split("-")[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"INV-{year}-{next_seq:06d}"
