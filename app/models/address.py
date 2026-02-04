"""Address and service area models."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class ServicePostcode(Base, TimestampMixin):
    """Allowed postcodes for delivery service."""

    __tablename__ = "service_postcodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    postcode: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship to service addresses
    service_addresses: Mapped[list["ServiceAddress"]] = relationship(
        "ServiceAddress",
        back_populates="postcode_ref",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ServicePostcode {self.postcode} - {self.city_name}>"


class ServiceAddress(Base, TimestampMixin):
    """Known addresses within service postcodes (optional address list)."""

    __tablename__ = "service_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    postcode_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("service_postcodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    street_name: Mapped[str] = mapped_column(String(255), nullable=False)
    building_numbers: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )  # e.g., "1-50" or NULL for all

    # Relationship
    postcode_ref: Mapped["ServicePostcode"] = relationship(
        "ServicePostcode",
        back_populates="service_addresses",
    )

    def __repr__(self) -> str:
        return f"<ServiceAddress {self.street_name}>"


class Address(Base, TimestampMixin):
    """User's saved addresses."""

    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Home, Work, etc.
    postcode: Mapped[str] = mapped_column(String(10), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    building: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    apartment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="address")

    def to_snapshot(self) -> dict:
        """Convert address to a snapshot dictionary for order storage."""
        return {
            "label": self.label,
            "postcode": self.postcode,
            "city": self.city,
            "street": self.street,
            "building": self.building,
            "floor": self.floor,
            "apartment": self.apartment,
            "instructions": self.instructions,
        }

    @property
    def full_address(self) -> str:
        """Return formatted full address."""
        parts = [self.street]
        if self.building:
            parts.append(self.building)
        if self.floor:
            parts.append(f"floor {self.floor}")
        if self.apartment:
            parts.append(f"apt {self.apartment}")
        parts.append(f"{self.postcode} {self.city}")
        return ", ".join(parts)

    def __repr__(self) -> str:
        return f"<Address {self.label or self.street}>"
