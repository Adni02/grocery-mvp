"""Order and related models."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, GUID, PortableJSON

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.product import Product
    from app.models.user import User


class OrderStatus(str, enum.Enum):
    """Order status enum."""

    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PACKING = "PACKING"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"

    @classmethod
    def valid_transitions(cls) -> dict[str, list[str]]:
        """Return valid status transitions."""
        return {
            cls.PLACED: [cls.CONFIRMED, cls.CANCELED],
            cls.CONFIRMED: [cls.PACKING, cls.CANCELED],
            cls.PACKING: [cls.OUT_FOR_DELIVERY, cls.CANCELED],
            cls.OUT_FOR_DELIVERY: [cls.DELIVERED, cls.CANCELED],
            cls.DELIVERED: [],  # Terminal state
            cls.CANCELED: [],  # Terminal state
        }

    def can_transition_to(self, new_status: "OrderStatus") -> bool:
        """Check if transition to new_status is valid."""
        return new_status in self.valid_transitions().get(self, [])


class Order(Base, TimestampMixin):
    """Order model."""

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    address_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("addresses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    address_snapshot: Mapped[dict[str, Any]] = mapped_column(
        PortableJSON,
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.PLACED,
        nullable=False,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )
    invoice_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    address: Mapped["Address"] = relationship("Address", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )

    def __repr__(self) -> str:
        return f"<Order {self.invoice_number or self.id}>"


class OrderItem(Base):
    """Order line item model."""

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_snapshot: Mapped[dict[str, Any]] = mapped_column(
        PortableJSON,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem {self.product_snapshot.get('name', 'Unknown')} x{self.quantity}>"


class OrderStatusHistory(Base):
    """Order status change history for audit trail."""

    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", create_type=False),
        nullable=False,
    )
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")

    def __repr__(self) -> str:
        return f"<OrderStatusHistory {self.order_id} -> {self.status}>"


class Invoice(Base):
    """Invoice metadata model."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"
