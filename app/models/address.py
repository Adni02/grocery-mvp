"""Address and service area models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class Address(Base, TimestampMixin):
    """User delivery address model."""

    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # "Home", "Work"
    street: Mapped[str] = mapped_column(String(200), nullable=False)
    building: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    apartment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    postcode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="address")

    def to_snapshot(self) -> dict[str, Any]:
        """Create a snapshot of address data for order storage."""
        return {
            "id": str(self.id),
            "label": self.label,
            "street": self.street,
            "building": self.building,
            "floor": self.floor,
            "apartment": self.apartment,
            "postcode": self.postcode,
            "city": self.city,
            "instructions": self.instructions,
        }

    def __repr__(self) -> str:
        return f"<Address {self.label}: {self.street}>"


class ServicePostcode(Base, TimestampMixin):
    """Service area postcodes - defines where we deliver."""

    __tablename__ = "service_postcodes"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    postcode: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
    )
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
    )

    def __repr__(self) -> str:
        return f"<ServicePostcode {self.postcode} - {self.city}>"


class ServiceAddress(Base, TimestampMixin):
    """Fine-grained service address rules - for blacklisting or special handling."""

    __tablename__ = "service_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    street_pattern: Mapped[str] = mapped_column(String(200), nullable=False)
    postcode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ServiceAddress {self.street_pattern}, {self.postcode}>"
