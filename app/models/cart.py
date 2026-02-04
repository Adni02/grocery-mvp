"""Cart model for shopping cart functionality."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Cart(Base, TimestampMixin):
    """Shopping cart model."""

    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Relationships
    items: Mapped[list["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def item_count(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self) -> float:
        """Calculate cart subtotal."""
        return sum(
            float(item.product.price) * item.quantity
            for item in self.items
            if item.product
        )

    def __repr__(self) -> str:
        return f"<Cart {self.id} ({self.item_count} items)>"


class CartItem(Base, TimestampMixin):
    """Cart item model."""

    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    product: Mapped["Product"] = relationship("Product", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CartItem {self.product_id} x{self.quantity}>"
